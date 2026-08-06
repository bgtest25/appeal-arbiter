from typing import Literal

from pydantic import BaseModel, Field

Outcome = Literal["uphold", "overturn", "escalate"]


class EvidenceAssessment(BaseModel):
    outcome: Outcome
    reasoning: str = Field(
        description="Why this outcome, grounded in the gap (or lack of gap) between the "
        "objective content summary and the appellant's own statement."
    )


class PolicyAssessment(BaseModel):
    outcome: Outcome
    reasoning: str
    cited_guideline: str = Field(description="The specific guideline excerpt this assessment relies on.")


class PrecedentAssessment(BaseModel):
    outcome: Outcome
    reasoning: str
    cited_case_id: str | None = Field(
        default=None, description="The id of the most relevant precedent case, if any."
    )


class SupervisorDecision(BaseModel):
    final_outcome: Outcome
    reasoning: str = Field(
        description="How the three specialist assessments were reconciled, especially if they disagreed."
    )
