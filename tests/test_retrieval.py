import chromadb

from appeal_arbiter.retrieval.ingest import parse_guidelines
from appeal_arbiter.retrieval.store import ingest_guidelines, query_guidelines


def test_parse_guidelines_covers_known_categories():
    chunks = parse_guidelines()
    titles = {c.title for c in chunks}
    assert "Monetization fraud & abuse" in titles
    assert "Harassment & bullying" in titles
    assert len(chunks) > 40  # bullet-level granularity, not section-level


def test_sealed_posts_query_retrieves_monetization_fraud_chunk(tmp_path):
    client = chromadb.PersistentClient(path=str(tmp_path))
    ingest_guidelines(client=client)

    result = query_guidelines(
        "my sealed post was removed for tricking people into unlocking it",
        n_results=1,
        client=client,
    )

    assert result["metadatas"][0][0]["title"] == "Monetization fraud & abuse"
    assert "Sealed Posts" in result["documents"][0][0]
