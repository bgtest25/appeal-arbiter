from fastapi import APIRouter, HTTPException

from appeal_arbiter.agents.graph import run_appeal
from appeal_arbiter.api.schemas import AdjudicateRequest, AdjudicateResponse, FixtureSummary
from appeal_arbiter.fixtures.appeal_cases import AppealCase, AppealInput, load_appeal_cases

router = APIRouter()


def _to_response(case_id: str, state: dict) -> AdjudicateResponse:
    return AdjudicateResponse(
        case_id=case_id,
        evidence_assessment=state["evidence_assessment"],
        policy_assessment=state["policy_assessment"],
        precedent_assessment=state["precedent_assessment"],
        supervisor_decision=state["supervisor_decision"],
    )


def _get_fixture_or_404(case_id: str) -> AppealCase:
    case = next((c for c in load_appeal_cases() if c.id == case_id), None)
    if case is None:
        raise HTTPException(status_code=404, detail=f"fixture {case_id!r} not found")
    return case


@router.get("/fixtures", response_model=list[FixtureSummary])
def list_fixtures() -> list[AppealCase]:
    return load_appeal_cases()


@router.get("/fixtures/{case_id}", response_model=AppealCase)
def get_fixture(case_id: str) -> AppealCase:
    return _get_fixture_or_404(case_id)


@router.post("/fixtures/{case_id}/adjudicate", response_model=AdjudicateResponse)
def adjudicate_fixture(case_id: str) -> AdjudicateResponse:
    case = _get_fixture_or_404(case_id)
    state = run_appeal(case)
    return _to_response(case.id, state)


@router.post("/appeals/adjudicate", response_model=AdjudicateResponse)
def adjudicate_appeal(request: AdjudicateRequest) -> AdjudicateResponse:
    case = AppealInput(**request.model_dump())
    state = run_appeal(case)
    return _to_response(case.id, state)
