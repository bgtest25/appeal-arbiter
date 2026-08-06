from appeal_arbiter.agents.llm import get_llm
from appeal_arbiter.agents.schemas import SupervisorDecision
from appeal_arbiter.agents.state import AppealState

SUPERVISOR_SYSTEM_PROMPT = """You are the supervisor of a content-moderation appeals panel.

Three specialists have independently assessed this appeal: an evidence re-check (evidence vs. the \
appellant's claim), a policy re-check (grounded in retrieved guideline text), and a precedent-consistency \
check (grounded in similar past-resolved cases). Reconcile their assessments into one final decision.

If they agree, confirm the consensus. If they disagree, explain which specialist's reasoning is more \
decisive for this specific case and why — do not simply take a majority vote without justifying it. If the \
disagreement reflects genuine ambiguity rather than one specialist clearly being right, escalate rather than \
picking a side arbitrarily."""


def supervisor_node(state: AppealState) -> dict:
    case = state["case"]
    ev = state["evidence_assessment"]
    pol = state["policy_assessment"]
    prec = state["precedent_assessment"]

    llm = get_llm().with_structured_output(SupervisorDecision)
    result = llm.invoke(
        [
            ("system", SUPERVISOR_SYSTEM_PROMPT),
            (
                "human",
                f"Case: {case.category} — {case.content_summary}\n"
                f"Original action: {case.original_action}\n\n"
                f"Evidence specialist: {ev.outcome} — {ev.reasoning}\n\n"
                f"Policy specialist: {pol.outcome} — {pol.reasoning} (cited: {pol.cited_guideline})\n\n"
                f"Precedent specialist: {prec.outcome} — {prec.reasoning} "
                f"(cited case: {prec.cited_case_id})\n",
            ),
        ]
    )
    return {"supervisor_decision": result}
