from pydantic import BaseModel
from datetime import datetime
from typing import Any


class ForecastRequest(BaseModel):
    dataset_id: str
    target_column: str
    date_column: str | None = None
    n_periods: int = 3


class AnomalyRequest(BaseModel):
    dataset_id: str
    target_column: str


class ChurnRequest(BaseModel):
    dataset_id: str
    target_column: str


class MLTaskResponse(BaseModel):
    task_id: str
    status: str = "pending"
    message: str = "Task queued. Poll GET /ml/results/{task_id} for updates."


class MLResultResponse(BaseModel):
    id: str
    model_type: str
    target_column: str | None
    status: str
    result_data: dict | None = None
    chart_data: dict | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}