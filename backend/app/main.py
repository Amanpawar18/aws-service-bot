import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pythonjsonlogger.json import JsonFormatter

from app.agent.agent import build_agent
from app.api.routes import chat, health


def _setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)


_setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("startup")
    app.state.agent = build_agent()
    yield
    logger.info("shutdown")


app = FastAPI(title="AWS Support Bot API", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(chat.router)
