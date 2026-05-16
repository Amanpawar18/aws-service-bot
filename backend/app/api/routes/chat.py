import logging
from typing import Any

from fastapi import APIRouter, Request
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, RemoveMessage

from app.api.schemas import ChatRequest, ChatResponse, HistoryResponse, MessageSchema

router = APIRouter()
logger = logging.getLogger(__name__)


def _config(session_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": session_id}}


def _is_visible_ai(msg: BaseMessage) -> bool:
    return (
        isinstance(msg, AIMessage)
        and isinstance(msg.content, str)
        and bool(msg.content)
        and not getattr(msg, "tool_calls", [])
    )


def _state_messages(agent: Any, config: dict[str, Any]) -> list[Any]:  # noqa: ANN401
    return agent.get_state(config).values.get("messages", [])  # type: ignore[no-any-return]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request) -> ChatResponse:
    agent = req.app.state.agent
    config = _config(request.session_id)
    logger.info("chat request", extra={"session_id": request.session_id})

    result: dict[str, Any] = await agent.ainvoke(
        {"messages": [HumanMessage(content=request.message)]},
        config=config,
    )

    content = ""
    for msg in reversed(result.get("messages", [])):
        if _is_visible_ai(msg):
            content = msg.content
            break

    return ChatResponse(role="assistant", content=content)


@router.get("/chat/{session_id}/history", response_model=HistoryResponse)
async def get_history(session_id: str, req: Request) -> HistoryResponse:
    agent = req.app.state.agent
    config = _config(session_id)
    raw = _state_messages(agent, config)

    messages = [
        MessageSchema(
            role="user" if isinstance(m, HumanMessage) else "assistant",
            content=m.content if isinstance(m.content, str) else "",
        )
        for m in raw
        if (isinstance(m, HumanMessage) and m.content) or _is_visible_ai(m)
    ]
    return HistoryResponse(session_id=session_id, messages=messages)


@router.delete("/chat/{session_id}/history")
async def delete_history(session_id: str, req: Request) -> dict[str, str]:
    agent = req.app.state.agent
    config = _config(session_id)
    existing = _state_messages(agent, config)
    if existing:
        removals = [RemoveMessage(id=m.id) for m in existing]
        agent.update_state(config, {"messages": removals})
    return {"status": "cleared", "session_id": session_id}
