from sqlalchemy.orm import Session
from app.modules.datasets.models import Dataset, DatasetProfile


# ── Dataset CRUD ───────────────────────────────────────────

def create_dataset(
    db: Session,
    user_id: str,
    original_filename: str,
    stored_filename: str,
    file_path: str,
    file_type: str,
    row_count: int,
    col_count: int,
) -> Dataset:
    dataset = Dataset(
        user_id=user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_type=file_type,
        row_count=row_count,
        col_count=col_count,
        status="uploaded",
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def get_dataset_by_id(db: Session, dataset_id: str) -> Dataset | None:
    return db.query(Dataset).filter(Dataset.id == dataset_id).first()


def get_datasets_by_user(db: Session, user_id: str) -> list[Dataset]:
    return (
        db.query(Dataset)
        .filter(Dataset.user_id == user_id)
        .order_by(Dataset.created_at.desc())
        .all()
    )


def update_dataset_status(db: Session, dataset_id: str, status: str) -> Dataset | None:
    dataset = get_dataset_by_id(db, dataset_id)
    if dataset:
        dataset.status = status
        db.commit()
        db.refresh(dataset)
    return dataset


def delete_dataset(db: Session, dataset_id: str) -> bool:
    dataset = get_dataset_by_id(db, dataset_id)
    if dataset:
        db.delete(dataset)
        db.commit()
        return True
    return False


# ── DatasetProfile CRUD ────────────────────────────────────

def create_profile(
    db: Session,
    dataset_id: str,
    columns_metadata: list,
    statistics: dict,
    null_summary: dict,
    sample_questions: list | None = None,
) -> DatasetProfile:
    profile = DatasetProfile(
        dataset_id=dataset_id,
        columns_metadata=columns_metadata,
        statistics=statistics,
        null_summary=null_summary,
        sample_questions=sample_questions,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_profile_questions(
    db: Session, dataset_id: str, questions: list[str]
) -> DatasetProfile | None:
    profile = (
        db.query(DatasetProfile)
        .filter(DatasetProfile.dataset_id == dataset_id)
        .first()
    )
    if profile:
        profile.sample_questions = questions
        db.commit()
        db.refresh(profile)
    return profile