from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from langchain_core.messages import AIMessage, HumanMessage

from app.api.routes import chat, health


def make_mock_agent() -> MagicMock:
    agent = MagicMock()

    async def fake_ainvoke(*args: object, **kwargs: object) -> dict[str, list[Any]]:
        return {"messages": [AIMessage(content="S3 is object storage.")]}

    agent.ainvoke = fake_ainvoke
    agent.get_state = MagicMock(
        return_value=MagicMock(
            values={
                "messages": [
                    HumanMessage(content="What is S3?"),
                    AIMessage(content="S3 is object storage."),
                ]
            }
        )
    )
    agent.update_state = MagicMock()
    return agent


@pytest.fixture
def mock_agent() -> MagicMock:
    return make_mock_agent()


@pytest.fixture
async def client(mock_agent: MagicMock) -> AsyncGenerator[AsyncClient, None]:
    test_app = FastAPI()
    test_app.state.agent = mock_agent
    test_app.include_router(health.router)
    test_app.include_router(chat.router)

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        yield ac


async def test_chat_returns_200(client: AsyncClient) -> None:
    response = await client.post(
        "/chat", json={"session_id": "s1", "message": "What is S3?"}
    )
    assert response.status_code == 200


async def test_chat_content_type_is_json(client: AsyncClient) -> None:
    response = await client.post(
        "/chat", json={"session_id": "s1", "message": "What is S3?"}
    )
    assert "application/json" in response.headers["content-type"]


async def test_chat_returns_assistant_content(client: AsyncClient) -> None:
    response = await client.post(
        "/chat", json={"session_id": "s1", "message": "What is S3?"}
    )
    body = response.json()
    assert body["role"] == "assistant"
    assert body["content"] == "S3 is object storage."


async def test_chat_rejects_empty_message(client: AsyncClient) -> None:
    response = await client.post("/chat", json={"session_id": "s1", "message": ""})
    assert response.status_code == 422


async def test_chat_rejects_missing_session_id(client: AsyncClient) -> None:
    response = await client.post("/chat", json={"message": "What is S3?"})
    assert response.status_code == 422


async def test_get_history_returns_200(client: AsyncClient) -> None:
    response = await client.get("/chat/s1/history")
    assert response.status_code == 200


async def test_get_history_returns_messages(client: AsyncClient) -> None:
    response = await client.get("/chat/s1/history")
    body = response.json()
    assert body["session_id"] == "s1"
    messages = body["messages"]
    assert any(m["role"] == "user" and "S3" in m["content"] for m in messages)
    assert any(m["role"] == "assistant" for m in messages)


async def test_delete_history_returns_200(client: AsyncClient) -> None:
    response = await client.delete("/chat/s1/history")
    assert response.status_code == 200


async def test_delete_history_calls_update_state(
    client: AsyncClient, mock_agent: MagicMock
) -> None:
    await client.delete("/chat/s1/history")
    mock_agent.update_state.assert_called_once()
