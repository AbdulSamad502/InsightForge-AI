import logging
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.shared.dependencies import get_current_user
from app.modules.authentication.models import User
from app.modules.ml import repository, service
from app.modules.ml.schemas import (
    ForecastRequest, AnomalyRequest, ChurnRequest,
    MLTaskResponse, MLResultResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.post("/forecast", response_model=MLTaskResponse, status_code=202)
def run_forecast(
    request: ForecastRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start a sales/revenue forecasting task.
    Returns 202 immediately with a task_id.
    Poll GET /ml/results/{task_id} to check status.
    """
    ml_result = repository.create_ml_result(
        db, current_user.id, request.dataset_id, "forecast", request.target_column
    )
    background_tasks.add_task(
        service.run_forecast_task,
        task_id=ml_result.id,
        dataset_id=request.dataset_id,
        user_id=current_user.id,
        target_column=request.target_column,
        date_column=request.date_column,
        n_periods=request.n_periods,
        db_url=settings.database_url,
    )
    return MLTaskResponse(
        task_id=ml_result.id,
        status="pending",
        message=f"Forecasting '{request.target_column}' started. Poll /ml/results/{ml_result.id} for updates.",
    )


@router.post("/anomaly", response_model=MLTaskResponse, status_code=202)
def run_anomaly(
    request: AnomalyRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start anomaly detection. Returns 202 + task_id."""
    ml_result = repository.create_ml_result(
        db, current_user.id, request.dataset_id, "anomaly", request.target_column
    )
    background_tasks.add_task(
        service.run_anomaly_task,
        task_id=ml_result.id,
        dataset_id=request.dataset_id,
        user_id=current_user.id,
        target_column=request.target_column,
        db_url=settings.database_url,
    )
    return MLTaskResponse(
        task_id=ml_result.id,
        message=f"Anomaly detection on '{request.target_column}' started.",
    )


@router.post("/churn", response_model=MLTaskResponse, status_code=202)
def run_churn(
    request: ChurnRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start churn prediction. Returns 202 + task_id."""
    ml_result = repository.create_ml_result(
        db, current_user.id, request.dataset_id, "churn", request.target_column
    )
    background_tasks.add_task(
        service.run_churn_task,
        task_id=ml_result.id,
        dataset_id=request.dataset_id,
        user_id=current_user.id,
        target_column=request.target_column,
        db_url=settings.database_url,
    )
    return MLTaskResponse(
        task_id=ml_result.id,
        message=f"Churn prediction on '{request.target_column}' started.",
    )


@router.get("/results/{task_id}", response_model=MLResultResponse)
def get_ml_result(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Poll this endpoint to get ML task status and results."""
    from app.core.exceptions import DatasetNotFoundError
    result = repository.get_ml_result(db, task_id)
    if not result or result.user_id != current_user.id:
        raise DatasetNotFoundError(task_id)
    return MLResultResponse.model_validate(result)


@router.get("/results", response_model=list[MLResultResponse])
def list_ml_results(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List recent ML results for the current user."""
    return repository.get_results_by_user(db, current_user.id)