from pydantic import BaseModel
from datetime import datetime


class GenerateReportRequest(BaseModel):
    dataset_id: str
    session_id: str | None = None


class ReportTaskResponse(BaseModel):
    report_id: str
    status: str = "pending"
    message: str


class ReportResponse(BaseModel):
    id: str
    dataset_id: str
    status: str
    file_path: str | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}