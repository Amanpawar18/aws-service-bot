from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    status: Literal["ok"]


class ChatRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    session_id: str
    message: str = Field(min_length=1)


class MessageSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    role: Literal["user", "assistant"]
    content: str


class HistoryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    session_id: str
    messages: list[MessageSchema]
