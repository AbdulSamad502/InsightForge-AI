from pydantic import BaseModel
from datetime import datetime
from typing import Any


class CreateSessionRequest(BaseModel):
    dataset_id: str
    title: str | None = None


class SendMessageRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    chart_data: dict | None = None
    insight: str | None = None
    recommendation: str | None = None
    intent_type: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionResponse(BaseModel):
    id: str
    user_id: str
    dataset_id: str | None
    title: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageResponse] = []

    model_config = {"from_attributes": True}


class ChatSessionListItem(BaseModel):
    id: str
    dataset_id: str | None
    title: str | None
    created_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class AgentResponse(BaseModel):
    message: ChatMessageResponse
    session_id: str
