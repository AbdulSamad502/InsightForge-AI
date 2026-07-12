import logging
from pathlib import Path
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.shared.dependencies import get_current_user
from app.modules.authentication.models import User
from app.modules.reports import repository, service
from app.modules.reports.schemas import (
    GenerateReportRequest, ReportTaskResponse, ReportResponse
)
from app.core.exceptions import DatasetNotFoundError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate", response_model=ReportTaskResponse, status_code=202)
def generate_report(
    request: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start report generation. Returns 202 immediately.
    Poll GET /reports/{id}/status to check progress.
    """
    report = repository.create_report(db, current_user.id, request.dataset_id)

    background_tasks.add_task(
        service.run_report_task,
        report_id=report.id,
        dataset_id=request.dataset_id,
        user_id=current_user.id,
        session_id=request.session_id,
        db_url=settings.database_url,
    )

    return ReportTaskResponse(
        report_id=report.id,
        status="pending",
        message=f"Report generation started. Poll /reports/{report.id}/status for updates.",
    )


@router.get("/", response_model=list[ReportResponse])
def list_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all reports for the current user."""
    return repository.get_reports_by_user(db, current_user.id)


@router.get("/{report_id}/status", response_model=ReportResponse)
def get_report_status(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check report generation status."""
    report = repository.get_report(db, report_id)
    if not report or report.user_id != current_user.id:
        raise DatasetNotFoundError(report_id)
    return ReportResponse.model_validate(report)


@router.get("/{report_id}/download")
def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download the generated PDF report."""
    report = repository.get_report(db, report_id)
    if not report or report.user_id != current_user.id:
        raise DatasetNotFoundError(report_id)

    if report.status != "complete" or not report.file_path:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Report is not ready for download.")

    pdf_path = Path(report.file_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found on server.")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"business_report_{report_id[:8]}.pdf",
    )   