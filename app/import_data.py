import ast
import asyncio
import csv
import sys
from datetime import datetime
from pathlib import Path

from elasticsearch.helpers import async_bulk
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.db import Base, Document
from elasticsearch import AsyncElasticsearch


async def main(csv_path: str):
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    es = AsyncElasticsearch(settings.elasticsearch_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    documents = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row_id, row in enumerate(reader, start=1):
            rubrics = ast.literal_eval(row["rubrics"]) if row["rubrics"] else []
            documents.append(
                Document(
                    id=row_id,
                    rubrics=rubrics,
                    text=row["text"],
                    created_date=datetime.fromisoformat(row["created_date"]),
                )
            )

    async with Session() as session:
        # The assignment CSV has no id column, so row number becomes stable id.
        for chunk_start in range(0, len(documents), 500):
            session.add_all(documents[chunk_start:chunk_start + 500])
            await session.commit()

    async def actions():
        for doc in documents:
            yield {
                "_index": settings.elasticsearch_index,
                "_id": doc.id,
                "_source": {"id": doc.id, "text": doc.text},
            }

    await async_bulk(es, actions())
    await es.indices.refresh(index=settings.elasticsearch_index)
    await es.close()
    await engine.dispose()
    print(f"Imported {len(documents)} documents.")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
