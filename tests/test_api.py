from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


class FakeES:
    async def ping(self):
        return True


@pytest.mark.asyncio
async def test_health(monkeypatch):
    # Avoid external dependencies in the smoke test.
    monkeypatch.setattr("app.main.es", FakeES())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
