"""Local Chroma index over the appeal fixtures themselves, used by the
precedent-consistency specialist to find how similar past cases were
actually resolved. Same PersistentClient/path as the guidelines store,
a separate collection.
"""

import chromadb

from appeal_arbiter.fixtures.appeal_cases import AppealInput, load_appeal_cases
from appeal_arbiter.retrieval.store import get_client

COLLECTION_NAME = "appeal_precedents"


def ingest_precedents(client: chromadb.ClientAPI | None = None) -> chromadb.Collection:
    client = client or get_client()
    collection = client.get_or_create_collection(COLLECTION_NAME)
    cases = load_appeal_cases()

    collection.upsert(
        ids=[c.id for c in cases],
        documents=[f"{c.category}: {c.content_summary}" for c in cases],
        metadatas=[
            {"category": c.category, "outcome": c.ground_truth_outcome, "case_id": c.id}
            for c in cases
        ],
    )
    return collection


def query_precedents(case: AppealInput, n_results: int = 3, client: chromadb.ClientAPI | None = None):
    """Finds the most similar past-resolved cases, excluding `case` itself."""
    client = client or get_client()
    collection = client.get_or_create_collection(COLLECTION_NAME)

    raw = collection.query(
        query_texts=[f"{case.category}: {case.content_summary}"],
        n_results=n_results + 1,  # +1 headroom in case `case` itself is indexed
    )
    ids, docs, metas = raw["ids"][0], raw["documents"][0], raw["metadatas"][0]
    filtered = [(i, d, m) for i, d, m in zip(ids, docs, metas) if i != case.id][:n_results]

    return {
        "ids": [[i for i, _, _ in filtered]],
        "documents": [[d for _, d, _ in filtered]],
        "metadatas": [[m for _, _, m in filtered]],
    }


if __name__ == "__main__":
    ingest_precedents()
    print("Ingested appeal precedents")
