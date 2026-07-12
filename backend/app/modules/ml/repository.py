from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.modules.ml.models import MLResult


def create_ml_result(
    db: Session,
    user_id: str,
    dataset_id: str,
    model_type: str,
    target_column: str | None = None,
) -> MLResult:
    result = MLResult(
        user_id=user_id,
        dataset_id=dataset_id,
        model_type=model_type,
        target_column=target_column,
        status="pending",
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_ml_result(db: Session, result_id: str) -> MLResult | None:
    return db.query(MLResult).filter(MLResult.id == result_id).first()


def get_results_by_user(db: Session, user_id: str) -> list[MLResult]:
    return (
        db.query(MLResult)
        .filter(MLResult.user_id == user_id)
        .order_by(MLResult.created_at.desc())
        .limit(20)
        .all()
    )


def update_result_running(db: Session, result_id: str) -> None:
    result = get_ml_result(db, result_id)
    if result:
        result.status = "running"
        db.commit()


def update_result_complete(
    db: Session,
    result_id: str,
    result_data: dict,
    chart_data: dict | None,
) -> None:
    result = get_ml_result(db, result_id)
    if result:
        result.status = "complete"
        result.result_data = result_data
        result.chart_data = chart_data
        result.completed_at = datetime.now(timezone.utc)
        db.commit()


def update_result_failed(db: Session, result_id: str, error: str) -> None:
    result = get_ml_result(db, result_id)
    if result:
        result.status = "failed"
        result.error_message = error[:500]
        result.completed_at = datetime.now(timezone.utc)
        db.commit()