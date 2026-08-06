"""Local Chroma vector store over Swypi's real community guidelines.

Uses Chroma's bundled default embedding function (a local ONNX MiniLM
model) rather than a hosted embeddings API, so the policy-lookup specialist
can run with no dependency beyond ANTHROPIC_API_KEY for the LLM calls
themselves.
"""

import threading

import chromadb

from appeal_arbiter.config import settings
from appeal_arbiter.retrieval.ingest import parse_guidelines

COLLECTION_NAME = "community_guidelines"

_client: chromadb.ClientAPI | None = None
_client_lock = threading.Lock()


def get_client() -> chromadb.ClientAPI:
    """Returns a process-wide singleton PersistentClient.

    Callers (guidelines + precedent specialists) run concurrently as
    parallel LangGraph nodes in a thread pool; instantiating a fresh
    `chromadb.PersistentClient` per call raced on Chroma's Rust-backed
    tenant/system startup when two threads did it at once against the
    same path, corrupting shared client state. One client, reused, avoids it.
    """
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def ingest_guidelines(client: chromadb.ClientAPI | None = None) -> chromadb.Collection:
    client = client or get_client()
    collection = client.get_or_create_collection(COLLECTION_NAME)
    chunks = parse_guidelines()

    collection.upsert(
        ids=[c.id for c in chunks],
        documents=[f"{c.title}: {c.text}" for c in chunks],
        metadatas=[{"section": c.section, "title": c.title} for c in chunks],
    )
    return collection


def query_guidelines(query: str, n_results: int = 3, client: chromadb.ClientAPI | None = None):
    client = client or get_client()
    collection = client.get_or_create_collection(COLLECTION_NAME)
    return collection.query(query_texts=[query], n_results=n_results)


if __name__ == "__main__":
    ingest_guidelines()
    print("Ingested community guidelines into", settings.chroma_persist_dir)
