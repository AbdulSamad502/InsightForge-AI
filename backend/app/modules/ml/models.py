import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class MLResult(Base):
    __tablename__ = "ml_results"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dataset_id: Mapped[str] = mapped_column(
        String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # "forecast" | "anomaly" | "churn"

    target_column: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # "pending" | "running" | "complete" | "failed"

    result_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Stores prediction numbers, summaries, feature importance etc.

    chart_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Plotly JSON parsed as dict for storage

    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<MLResult {self.model_type} status={self.status}>"