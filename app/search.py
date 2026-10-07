from elasticsearch import AsyncElasticsearch
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db import Document


class SearchService:
    def __init__(self, es: AsyncElasticsearch, session_factory: async_sessionmaker[AsyncSession]):
        self.es = es
        self.session_factory = session_factory

    async def search(self, query: str, limit: int = 20) -> list[dict]:
        # Elasticsearch decides relevance; DB decides final chronological ordering.
        response = await self.es.search(
            index="documents",
            size=1000,
            query={
                "match": {
                    "text": {
                        "query": query,
                        "operator": "and",
                    }
                }
            },
            _source=False,
        )
        ids = [int(hit["_id"]) for hit in response["hits"]["hits"]]
        if not ids:
            return []

        async with self.session_factory() as session:
            result = await session.execute(
                select(Document)
                .where(Document.id.in_(ids))
                .order_by(Document.created_date.desc())
                .limit(limit)
            )
            docs = result.scalars().all()

        return [
            {
                "id": doc.id,
                "rubrics": doc.rubrics,
                "text": doc.text,
                "created_date": doc.created_date,
            }
            for doc in docs
        ]

    async def delete(self, document_id: int) -> bool:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Document).where(Document.id == document_id)
            )
            doc = result.scalar_one_or_none()
            if doc is None:
                return False
            await session.delete(doc)
            await session.commit()

        await self.es.delete(index="documents", id=document_id, ignore=[404])
        return True
