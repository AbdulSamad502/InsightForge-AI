from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.modules.reports.models import Report


def create_report(db: Session, user_id: str, dataset_id: str) -> Report:
    report = Report(user_id=user_id, dataset_id=dataset_id, status="pending")
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, report_id: str) -> Report | None:
    return db.query(Report).filter(Report.id == report_id).first()


def get_reports_by_user(db: Session, user_id: str) -> list[Report]:
    return (
        db.query(Report)
        .filter(Report.user_id == user_id)
        .order_by(Report.created_at.desc())
        .limit(20)
        .all()
    )


def update_report_running(db: Session, report_id: str) -> None:
    r = get_report(db, report_id)
    if r:
        r.status = "running"
        db.commit()


def update_report_complete(db: Session, report_id: str, file_path: str) -> None:
    r = get_report(db, report_id)
    if r:
        r.status = "complete"
        r.file_path = file_path
        r.completed_at = datetime.now(timezone.utc)
        db.commit()


def update_report_failed(db: Session, report_id: str, error: str) -> None:
    r = get_report(db, report_id)
    if r:
        r.status = "failed"
        r.error_message = error[:500]
        r.completed_at = datetime.now(timezone.utc)
        db.commit()