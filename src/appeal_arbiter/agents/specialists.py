"""The three specialist agents. Each is deliberately scoped to reason over
only ONE kind of evidence — evidence-vs-claim, retrieved policy text, or
retrieved precedent — so their assessments are genuinely independent
signals for the supervisor to reconcile, not three copies of the same
judgment.
"""

from appeal_arbiter.agents.llm import get_llm
from appeal_arbiter.agents.schemas import EvidenceAssessment, PolicyAssessment, PrecedentAssessment
from appeal_arbiter.agents.state import AppealState
from appeal_arbiter.retrieval.precedent_store import query_precedents
from appeal_arbiter.retrieval.store import query_guidelines

EVIDENCE_SYSTEM_PROMPT = """You are the evidence re-check specialist on a content-moderation appeals panel.

Your job is ONLY to compare the objective content summary against the appellant's own statement and the \
original violation reason cited by the original moderator. Decide whether the evidence, taken on its own, \
actually supports the original decision. Do not consider general policy text or past cases — other \
specialists handle those; stay narrowly focused on whether the evidence supports the claim.

Decide: uphold (evidence supports the original action), overturn (evidence contradicts or doesn't support \
the original action), or escalate (evidence is genuinely ambiguous, not just inconvenient for one side)."""


def evidence_node(state: AppealState) -> dict:
    case = state["case"]
    llm = get_llm().with_structured_output(EvidenceAssessment)
    result = llm.invoke(
        [
            ("system", EVIDENCE_SYSTEM_PROMPT),
            (
                "human",
                f"Original action taken: {case.original_action}\n"
                f"Original violation reason cited: {case.original_violation_reason}\n"
                f"Objective content summary (what the evidence shows): {case.content_summary}\n"
                f"Appellant's statement: {case.user_appeal_statement}\n",
            ),
        ]
    )
    return {"evidence_assessment": result}


POLICY_SYSTEM_PROMPT = """You are the policy re-check specialist on a content-moderation appeals panel.

You are given the case plus excerpts retrieved from Swypi's actual community guidelines. Decide whether \
the retrieved guideline text actually supports classifying this case as a violation of the claimed category. \
Base your decision ONLY on the guideline excerpts provided, not on general judgment or outside knowledge of \
platform policy — if the excerpts don't clearly support the classification, say so.

Decide: uphold, overturn, or escalate. Cite the specific excerpt your decision relies on most."""


def policy_node(state: AppealState) -> dict:
    case = state["case"]
    retrieved = query_guidelines(f"{case.category}: {case.content_summary}", n_results=3)
    excerpts = "\n".join(
        f"- [{meta['title']}] {doc}"
        for meta, doc in zip(retrieved["metadatas"][0], retrieved["documents"][0])
    )

    llm = get_llm().with_structured_output(PolicyAssessment)
    result = llm.invoke(
        [
            ("system", POLICY_SYSTEM_PROMPT),
            (
                "human",
                f"Claimed violation category: {case.category}\n"
                f"Original violation reason cited: {case.original_violation_reason}\n"
                f"Content summary: {case.content_summary}\n\n"
                f"Retrieved guideline excerpts:\n{excerpts}\n",
            ),
        ]
    )
    return {"policy_assessment": result}


PRECEDENT_SYSTEM_PROMPT = """You are the precedent-consistency specialist on a content-moderation appeals \
panel.

You are given the current case plus the most similar past-resolved appeal cases and how they were actually \
resolved. Decide whether resolving this case the same way as its closest precedent(s) would be consistent, \
or whether this case is meaningfully different enough that a different outcome is justified. If no retrieved \
precedent is genuinely similar, say so rather than forcing a comparison.

Decide: uphold, overturn, or escalate."""


def precedent_node(state: AppealState) -> dict:
    case = state["case"]
    similar = query_precedents(case, n_results=3)
    precedent_text = "\n".join(
        f"- [{cid}] resolved as {meta['outcome']} ({meta['category']}): {doc}"
        for cid, meta, doc in zip(similar["ids"][0], similar["metadatas"][0], similar["documents"][0])
    ) or "(no similar precedent found)"

    llm = get_llm().with_structured_output(PrecedentAssessment)
    result = llm.invoke(
        [
            ("system", PRECEDENT_SYSTEM_PROMPT),
            (
                "human",
                f"Current case ({case.category}): {case.content_summary}\n"
                f"Original violation reason: {case.original_violation_reason}\n\n"
                f"Most similar past-resolved cases:\n{precedent_text}\n",
            ),
        ]
    )
    return {"precedent_assessment": result}
