from fastapi.testclient import TestClient

from appeal_arbiter.agents.schemas import Outcome
from appeal_arbiter.main import app

client = TestClient(app)


def test_list_fixtures_returns_all_18_without_leaking_ground_truth():
    response = client.get("/fixtures")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 18
    assert "ground_truth_outcome" not in body[0]


def test_get_fixture_returns_full_case_including_ground_truth():
    response = client.get("/fixtures/case-003")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "case-003"
    assert body["ground_truth_outcome"] == "overturn"


def test_get_unknown_fixture_is_404():
    response = client.get("/fixtures/does-not-exist")
    assert response.status_code == 404


def test_adjudicate_fixture_real_end_to_end():
    """Not mocked — a real run through the live graph via the actual HTTP
    layer, same case used in test_agents.py's direct-graph test, so this
    specifically verifies the FastAPI wiring/serialization rather than
    re-proving the graph itself works."""
    response = client.post("/fixtures/case-003/adjudicate")
    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == "case-003"
    for key in ("evidence_assessment", "policy_assessment", "precedent_assessment"):
        assert body[key]["outcome"] in Outcome.__args__
        assert body[key]["reasoning"]
    assert body["supervisor_decision"]["final_outcome"] in Outcome.__args__
