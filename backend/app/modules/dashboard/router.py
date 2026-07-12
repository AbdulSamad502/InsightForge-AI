import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.shared.dependencies import get_current_user
from app.modules.authentication.models import User
from app.modules.datasets.models import Dataset
from app.modules.chat.models import ChatSession, ChatMessage
from app.modules.ml.models import MLResult
from app.modules.reports.models import Report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns all data needed for the dashboard page in one call.
    """
    user_id = current_user.id

    # ── KPI counts ─────────────────────────────────────────
    total_datasets = db.query(func.count(Dataset.id)).filter(
        Dataset.user_id == user_id
    ).scalar() or 0

    total_chats = db.query(func.count(ChatSession.id)).filter(
        ChatSession.user_id == user_id
    ).scalar() or 0

    total_messages = db.query(func.count(ChatMessage.id)).join(
        ChatSession, ChatMessage.session_id == ChatSession.id
    ).filter(ChatSession.user_id == user_id).scalar() or 0

    total_reports = db.query(func.count(Report.id)).filter(
        Report.user_id == user_id,
        Report.status == "complete",
    ).scalar() or 0

    total_ml_runs = db.query(func.count(MLResult.id)).filter(
        MLResult.user_id == user_id,
        MLResult.status == "complete",
    ).scalar() or 0

    # ── Recent items ───────────────────────────────────────
    recent_datasets = db.query(Dataset).filter(
        Dataset.user_id == user_id
    ).order_by(Dataset.created_at.desc()).limit(5).all()

    recent_sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user_id
    ).order_by(ChatSession.updated_at.desc()).limit(5).all()

    recent_reports = db.query(Report).filter(
        Report.user_id == user_id
    ).order_by(Report.created_at.desc()).limit(5).all()

    recent_ml = db.query(MLResult).filter(
        MLResult.user_id == user_id,
        MLResult.status == "complete",
    ).order_by(MLResult.created_at.desc()).limit(3).all()

    return {
        "kpis": {
            "total_datasets":  total_datasets,
            "total_chats":     total_chats,
            "total_messages":  total_messages,
            "total_reports":   total_reports,
            "total_ml_runs":   total_ml_runs,
        },
        "recent_datasets": [
            {
                "id": d.id,
                "filename": d.original_filename,
                "row_count": d.row_count,
                "col_count": d.col_count,
                "status": d.status,
                "created_at": str(d.created_at),
            }
            for d in recent_datasets
        ],
        "recent_sessions": [
            {
                "id": s.id,
                "title": s.title or "Untitled Chat",
                "dataset_id": s.dataset_id,
                "created_at": str(s.created_at),
            }
            for s in recent_sessions
        ],
        "recent_reports": [
            {
                "id": r.id,
                "dataset_id": r.dataset_id,
                "status": r.status,
                "created_at": str(r.created_at),
            }
            for r in recent_reports
        ],
        "recent_ml_results": [
            {
                "id": m.id,
                "model_type": m.model_type,
                "target_column": m.target_column,
                "dataset_id": m.dataset_id,
                "created_at": str(m.created_at),
            }
            for m in recent_ml
        ],
    }