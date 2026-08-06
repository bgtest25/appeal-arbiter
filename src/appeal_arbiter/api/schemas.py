import uuid

from pydantic import BaseModel, Field

from appeal_arbiter.agents.schemas import (
    EvidenceAssessment,
    PolicyAssessment,
    PrecedentAssessment,
    SupervisorDecision,
)
from appeal_arbiter.fixtures.appeal_cases import OriginalAction


class AdjudicateRequest(BaseModel):
    id: str = Field(default_factory=lambda: f"appeal-{uuid.uuid4().hex[:8]}")
    category: str
    original_action: OriginalAction
    content_summary: str
    original_violation_reason: str
    user_appeal_statement: str


class AdjudicateResponse(BaseModel):
    case_id: str
    evidence_assessment: EvidenceAssessment
    policy_assessment: PolicyAssessment
    precedent_assessment: PrecedentAssessment
    supervisor_decision: SupervisorDecision


class FixtureSummary(BaseModel):
    id: str
    category: str
    original_action: OriginalAction
