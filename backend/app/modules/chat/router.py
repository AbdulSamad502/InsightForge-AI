from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.shared.dependencies import get_current_user
from app.modules.authentication.models import User
from app.modules.chat import service
from app.modules.chat.schemas import (
    CreateSessionRequest, SendMessageRequest,
    ChatSessionResponse, AgentResponse, ChatSessionListItem,
)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_session(
    data: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new chat session linked to a dataset."""
    return await service.create_session(data, current_user.id, db)


@router.get("/sessions", response_model=list[ChatSessionListItem])
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all chat sessions for the current user."""
    return service.get_sessions(current_user.id, db)


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a session with all its messages."""
    return service.get_session_with_messages(session_id, current_user.id, db)


@router.post("/sessions/{session_id}/message", response_model=AgentResponse)
async def send_message(
    session_id: str,
    data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a message to the AI agent and get a response."""
    return await service.send_message(session_id, data, current_user.id, db)


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a chat session and all its messages."""
    from app.modules.chat.repository import delete_session as repo_delete
    repo_delete(db, session_id)
