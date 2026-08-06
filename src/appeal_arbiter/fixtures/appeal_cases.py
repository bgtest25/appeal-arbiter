"""Synthetic contested-appeal fixtures.

Hand-labeled, not scraped from real Swypi appeal data — same methodology
as the Trust & Safety Copilot eval fixtures (see project memory): honestly
disclosed as synthetic rather than presented as real user data, because
real appeal volume is too thin to be a credible standalone benchmark.

Each case pairs an objective `content_summary` (what the evidence actually
shows) against `user_appeal_statement` (what the appellant claims) — the
gap between the two is what the evidence-re-check specialist needs to
reason about. `ground_truth_outcome` is the hand-labeled correct call;
`rationale` documents why, for eval interpretability when a run disagrees.
"""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

FIXTURES_PATH = Path(__file__).parent / "appeal_cases.json"

OriginalAction = Literal["warning", "content_removal", "temporary_suspension", "permanent_ban"]
AppealOutcome = Literal["uphold", "overturn", "escalate"]


class AppealInput(BaseModel):
    """What the multi-agent graph actually needs to adjudicate a case.

    Split out from AppealCase so the API can accept a real appeal — which
    has no hand-labeled ground truth yet — without forcing callers to
    invent a fake `ground_truth_outcome`/`rationale`.
    """

    id: str
    category: str
    original_action: OriginalAction
    content_summary: str
    original_violation_reason: str
    user_appeal_statement: str


class AppealCase(AppealInput):
    ground_truth_outcome: AppealOutcome
    rationale: str


def load_appeal_cases(path: Path = FIXTURES_PATH) -> list[AppealCase]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [AppealCase.model_validate(item) for item in raw]


if __name__ == "__main__":
    cases = load_appeal_cases()
    print(f"{len(cases)} appeal cases loaded")
    outcomes = {}
    for c in cases:
        outcomes[c.ground_truth_outcome] = outcomes.get(c.ground_truth_outcome, 0) + 1
    print("outcome distribution:", outcomes)
