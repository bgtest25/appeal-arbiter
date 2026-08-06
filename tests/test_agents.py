"""Integration test against the real Anthropic API — deliberately not mocked,
since the point of this project is to demonstrate genuine multi-agent
reasoning, not just that the graph wiring is structurally valid. Kept to a
single case to bound the API cost of running the test suite.
"""

from appeal_arbiter.agents.graph import run_appeal
from appeal_arbiter.agents.schemas import Outcome
from appeal_arbiter.fixtures.appeal_cases import load_appeal_cases


def test_run_appeal_produces_a_full_reconciled_decision():
    case = next(c for c in load_appeal_cases() if c.id == "case-003")

    result = run_appeal(case)

    for key in ("evidence_assessment", "policy_assessment", "precedent_assessment"):
        assert key in result
        assert result[key].outcome in Outcome.__args__
        assert result[key].reasoning

    decision = result["supervisor_decision"]
    assert decision.final_outcome in Outcome.__args__
    assert decision.reasoning
