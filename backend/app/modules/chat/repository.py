from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.modules.chat.models import ChatSession, ChatMessage


# ── Chat Session CRUD ──────────────────────────────────────

def create_session(
    db: Session, user_id: str, dataset_id: str, title: str | None = None
) -> ChatSession:
    session = ChatSession(
        user_id=user_id, dataset_id=dataset_id, title=title
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str) -> ChatSession | None:
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def get_sessions_by_user(db: Session, user_id: str) -> list[ChatSession]:
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )


def update_session_title(db: Session, session_id: str, title: str) -> None:
    session = get_session(db, session_id)
    if session:
        session.title = title
        session.updated_at = datetime.now(timezone.utc)
        db.commit()


def delete_session(db: Session, session_id: str) -> bool:
    session = get_session(db, session_id)
    if session:
        db.delete(session)
        db.commit()
        return True
    return False


# ── Chat Message CRUD ──────────────────────────────────────

def save_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    chart_data: dict | None = None,
    insight: str | None = None,
    recommendation: str | None = None,
    intent_type: str | None = None,
) -> ChatMessage:
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        chart_data=chart_data,
        insight=insight,
        recommendation=recommendation,
        intent_type=intent_type,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_messages_by_session(db: Session, session_id: str) -> list[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
