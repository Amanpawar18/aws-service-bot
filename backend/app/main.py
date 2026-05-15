from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield  # graph attached in Phase 4


app = FastAPI(title="AWS Support Bot API", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
