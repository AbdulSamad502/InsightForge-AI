import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # csv | xlsx
    status: Mapped[str] = mapped_column(String(20), default="uploaded")
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    col_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationship to profile
    profile: Mapped["DatasetProfile | None"] = relationship(
        "DatasetProfile", back_populates="dataset", uselist=False, cascade="all, delete"
    )

    def __repr__(self) -> str:
        return f"<Dataset {self.original_filename}>"


class DatasetProfile(Base):
    __tablename__ = "dataset_profiles"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    dataset_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    columns_metadata: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Example: [{"name": "revenue", "dtype": "float64", "null_pct": 2.3, "unique_count": 450}]

    statistics: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Example: {"revenue": {"min": 0, "max": 50000, "mean": 4200, "std": 1200}}

    null_summary: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Example: {"revenue": 28, "category": 0}

    sample_questions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Example: ["What is total revenue by category?", ...]

    profiled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationship back to dataset
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="profile")

    def __repr__(self) -> str:
        return f"<DatasetProfile dataset_id={self.dataset_id}>"