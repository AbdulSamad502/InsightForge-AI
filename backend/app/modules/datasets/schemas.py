from pydantic import BaseModel
from datetime import datetime
from typing import Any


class ColumnMetadata(BaseModel):
    name: str
    dtype: str           # "numeric" | "datetime" | "categorical" | "text"
    null_count: int
    null_pct: float
    unique_count: int
    sample_values: list[Any]


class DatasetProfileResponse(BaseModel):
    id: str
    dataset_id: str
    columns_metadata: list[ColumnMetadata]
    statistics: dict[str, Any]
    null_summary: dict[str, int]
    sample_questions: list[str] | None
    profiled_at: datetime

    model_config = {"from_attributes": True}


class DatasetResponse(BaseModel):
    id: str
    user_id: str
    original_filename: str
    stored_filename: str
    file_type: str
    status: str
    row_count: int | None
    col_count: int | None
    created_at: datetime
    profile: DatasetProfileResponse | None = None

    model_config = {"from_attributes": True}


class DatasetListItem(BaseModel):
    id: str
    original_filename: str
    file_type: str
    status: str
    row_count: int | None
    col_count: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PreviewResponse(BaseModel):
    dataset_id: str
    columns: list[str]
    dtypes: dict[str, str]
    rows: list[dict[str, Any]]
    total_rows: int


# ── Cleaning schemas ───────────────────────────────────────

class CleaningIssue(BaseModel):
    issue_type: str      # "missing_values" | "duplicates" | "negative_values" | "invalid_dates" | "inconsistent_categories"
    column: str | None   # None for dataset-level issues like duplicates
    description: str     # Human-readable: "Revenue has 28 missing values (12%)"
    count: int
    fix_options: list[str]  # ["fill_median", "fill_mean", "drop_rows", "skip"]


class CleaningReport(BaseModel):
    dataset_id: str
    total_issues: int
    issues: list[CleaningIssue]
    has_duplicates: bool
    duplicate_count: int


class CleanConfig(BaseModel):
    """What the user decided to fix."""
    fill_missing: dict[str, str] = {}
    # Example: {"revenue": "median", "category": "mode"}

    remove_duplicates: bool = False

    fix_negative_columns: list[str] = []
    # Columns where negative values should be replaced with 0

    standardize_categories: list[str] = []
    # Columns where inconsistent casing should be standardized


class CleanResponse(BaseModel):
    original_dataset_id: str
    cleaned_dataset_id: str
    changes_applied: list[str]
    rows_before: int
    rows_after: int


class UploadResponse(BaseModel):
    dataset: DatasetResponse
    cleaning_report: CleaningReport
    suggestions: list[str]