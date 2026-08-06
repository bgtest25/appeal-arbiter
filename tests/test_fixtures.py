from appeal_arbiter.fixtures.appeal_cases import load_appeal_cases
from appeal_arbiter.retrieval.ingest import parse_guidelines


def test_appeal_cases_load_with_unique_ids():
    cases = load_appeal_cases()
    assert len(cases) == 18
    assert len({c.id for c in cases}) == len(cases)


def test_appeal_case_categories_match_real_guideline_categories():
    cases = load_appeal_cases()
    real_titles = {c.title for c in parse_guidelines()}
    for case in cases:
        assert case.category in real_titles, f"{case.id} category {case.category!r} not in guidelines"


def test_outcome_distribution_has_all_three_buckets():
    cases = load_appeal_cases()
    outcomes = {c.ground_truth_outcome for c in cases}
    assert outcomes == {"uphold", "overturn", "escalate"}
