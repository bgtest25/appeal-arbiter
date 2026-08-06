from typing import TypedDict

from appeal_arbiter.agents.schemas import (
    EvidenceAssessment,
    PolicyAssessment,
    PrecedentAssessment,
    SupervisorDecision,
)
from appeal_arbiter.fixtures.appeal_cases import AppealInput


class AppealState(TypedDict, total=False):
    case: AppealInput
    evidence_assessment: EvidenceAssessment
    policy_assessment: PolicyAssessment
    precedent_assessment: PrecedentAssessment
    supervisor_decision: SupervisorDecision
