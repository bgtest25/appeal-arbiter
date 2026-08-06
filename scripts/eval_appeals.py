"""Replays all synthetic appeal fixtures through the live multi-agent graph
and reports how the supervisor's final_outcome compares to hand-labeled
ground truth. Same honest-eval methodology as the Trust & Safety Copilot v1
eval: real LLM calls end-to-end, no mocking, precision/recall per outcome
class rather than one vague "accuracy" number.

Costs ~18 cases x 4 LLM calls (3 specialists + supervisor) = ~72 calls per
run. Cases run concurrently (bounded pool) since each case's own specialists
already run in parallel inside the graph itself.
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

from appeal_arbiter.agents.graph import run_appeal
from appeal_arbiter.agents.schemas import Outcome
from appeal_arbiter.fixtures.appeal_cases import AppealCase, load_appeal_cases

RESULTS_PATH = Path(__file__).parent / "eval_results.json"
OUTCOMES: tuple[str, ...] = Outcome.__args__  # ("uphold", "overturn", "escalate")


@dataclass
class CaseResult:
    case_id: str
    category: str
    ground_truth: str
    predicted: str
    specialist_outcomes: dict[str, str]
    specialists_disagreed: bool
    supervisor_reasoning: str


def run_one(case: AppealCase) -> CaseResult:
    state = run_appeal(case)
    specialist_outcomes = {
        "evidence": state["evidence_assessment"].outcome,
        "policy": state["policy_assessment"].outcome,
        "precedent": state["precedent_assessment"].outcome,
    }
    decision = state["supervisor_decision"]
    return CaseResult(
        case_id=case.id,
        category=case.category,
        ground_truth=case.ground_truth_outcome,
        predicted=decision.final_outcome,
        specialist_outcomes=specialist_outcomes,
        specialists_disagreed=len(set(specialist_outcomes.values())) > 1,
        supervisor_reasoning=decision.reasoning,
    )


def confusion_matrix(results: list[CaseResult]) -> dict[str, dict[str, int]]:
    matrix = {gt: {pred: 0 for pred in OUTCOMES} for gt in OUTCOMES}
    for r in results:
        matrix[r.ground_truth][r.predicted] += 1
    return matrix


def precision_recall_f1(results: list[CaseResult]) -> dict[str, dict[str, float]]:
    metrics = {}
    for outcome in OUTCOMES:
        tp = sum(1 for r in results if r.predicted == outcome and r.ground_truth == outcome)
        fp = sum(1 for r in results if r.predicted == outcome and r.ground_truth != outcome)
        fn = sum(1 for r in results if r.predicted != outcome and r.ground_truth == outcome)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        metrics[outcome] = {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}
    return metrics


def specialist_accuracy(results: list[CaseResult]) -> dict[str, float]:
    return {
        specialist: sum(1 for r in results if r.specialist_outcomes[specialist] == r.ground_truth)
        / len(results)
        for specialist in ("evidence", "policy", "precedent")
    }


def main() -> None:
    cases = load_appeal_cases()
    print(f"Running {len(cases)} cases through the live multi-agent graph "
          f"({len(cases) * 4} real LLM calls)...")

    results: list[CaseResult] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(run_one, case): case for case in cases}
        for i, future in enumerate(as_completed(futures), 1):
            case = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                print(f"  [{i}/{len(cases)}] {case.id} FAILED: {exc}", file=sys.stderr)
                continue
            marker = "correct" if result.predicted == result.ground_truth else "WRONG"
            disagreement_note = " (specialists disagreed)" if result.specialists_disagreed else ""
            print(
                f"  [{i}/{len(cases)}] {case.id}: predicted={result.predicted} "
                f"ground_truth={result.ground_truth} [{marker}]{disagreement_note}"
            )
            results.append(result)

    results.sort(key=lambda r: r.case_id)

    agreement = sum(1 for r in results if r.predicted == r.ground_truth) / len(results)
    matrix = confusion_matrix(results)
    metrics = precision_recall_f1(results)
    spec_acc = specialist_accuracy(results)
    disagreement_cases = [r for r in results if r.specialists_disagreed]

    print("\n=== Confusion matrix (rows=ground truth, cols=predicted) ===")
    print("".ljust(12) + "".join(o.ljust(12) for o in OUTCOMES))
    for gt in OUTCOMES:
        print(gt.ljust(12) + "".join(str(matrix[gt][pred]).ljust(12) for pred in OUTCOMES))

    correct = sum(1 for r in results if r.predicted == r.ground_truth)
    print(f"\n=== Overall supervisor agreement with ground truth: {agreement:.1%} ({correct}/{len(results)}) ===")

    print("\n=== Per-outcome precision/recall/F1 ===")
    for outcome, m in metrics.items():
        print(
            f"  {outcome:10s} precision={m['precision']:.2f} recall={m['recall']:.2f} "
            f"f1={m['f1']:.2f} (n={m['support']})"
        )

    print("\n=== Individual specialist accuracy (vs. ground truth) ===")
    for specialist, acc in spec_acc.items():
        print(f"  {specialist:10s} {acc:.1%}")

    print(f"\n=== Cases with specialist disagreement: {len(disagreement_cases)}/{len(results)} ===")
    for r in disagreement_cases:
        marker = "correct" if r.predicted == r.ground_truth else "WRONG"
        print(
            f"  {r.case_id} ({r.category}): {r.specialist_outcomes} -> supervisor={r.predicted} "
            f"ground_truth={r.ground_truth} [{marker}]"
        )

    RESULTS_PATH.write_text(
        json.dumps(
            {
                "agreement": agreement,
                "confusion_matrix": matrix,
                "metrics": metrics,
                "specialist_accuracy": spec_acc,
                "cases": [asdict(r) for r in results],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nFull results written to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
