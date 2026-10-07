from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from elasticsearch import AsyncElasticsearch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.db import Base, Document
from app.search import SearchService


engine = create_async_engine(settings.database_url, pool_pre_ping=True)
Session = async_sessionmaker(engine, expire_on_commit=False)
es = AsyncElasticsearch(settings.elasticsearch_url)
search_service = SearchService(es, Session)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await es.indices.create(
        index=settings.elasticsearch_index,
        mappings={
            "properties": {
                "id": {"type": "integer"},
                "text": {"type": "text", "analyzer": "standard"},
            }
        },
        ignore=400,
    )
    yield
    await es.close()
    await engine.dispose()


app = FastAPI(
    title="Document Search Service",
    version="1.0.0",
    description="Simple text search over documents stored in PostgreSQL and Elasticsearch.",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    await es.ping()
    return {"status": "ok"}


@app.get("/search")
async def search(
    q: str = Query(min_length=1, description="Arbitrary text query"),
):
    return await search_service.search(q, limit=20)


@app.delete("/documents/{document_id}", status_code=204)
async def delete_document(document_id: int):
    deleted = await search_service.delete(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return None
