from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.routes import health


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield

    test_app = FastAPI(lifespan=_lifespan)
    test_app.include_router(health.router)

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        yield ac
