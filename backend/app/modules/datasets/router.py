import logging
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.shared.dependencies import get_current_user
from app.modules.authentication.models import User
from app.modules.datasets import service
from app.modules.datasets.schemas import (
    UploadResponse, DatasetResponse, PreviewResponse,
    CleanConfig, CleanResponse, DatasetListItem,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a CSV or XLSX file, profile it, and return cleaning suggestions."""
    return await service.upload_and_profile(file, current_user.id, db)


@router.get("/", response_model=list[DatasetListItem])
def list_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all datasets for the current user."""
    return service.list_datasets(current_user.id, db)


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single dataset with full profile."""
    from app.modules.datasets.repository import get_dataset_by_id
    from app.core.exceptions import DatasetNotFoundError
    dataset = get_dataset_by_id(db, dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        raise DatasetNotFoundError(dataset_id)
    return DatasetResponse.model_validate(dataset)


@router.get("/{dataset_id}/preview", response_model=PreviewResponse)
def preview_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return first 50 rows of a dataset."""
    return service.get_preview(dataset_id, current_user.id, db)


@router.post("/{dataset_id}/clean", response_model=CleanResponse)
async def clean_dataset(
    dataset_id: str,
    config: CleanConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Apply cleaning operations and return a new cleaned dataset."""
    return await service.clean_dataset(dataset_id, config, current_user.id, db)


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a dataset and its file."""
    service.delete_dataset_service(dataset_id, current_user.id, db)