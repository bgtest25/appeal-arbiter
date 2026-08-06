from contextlib import asynccontextmanager

from fastapi import FastAPI

from appeal_arbiter.api.routes import router
from appeal_arbiter.retrieval.precedent_store import ingest_precedents
from appeal_arbiter.retrieval.store import ingest_guidelines


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Chroma's persisted collections may not exist yet on a fresh disk (e.g. a
    # new container). Re-ingesting on every startup is cheap for this corpus
    # size and keeps every instance self-sufficient without shared storage.
    ingest_guidelines()
    ingest_precedents()
    yield


app = FastAPI(title="appeal-arbiter", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
