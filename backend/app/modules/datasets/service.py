import os
import uuid
import json
import time
import logging
import pandas as pd
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import InvalidFileError, FileTooLargeError, DatasetNotFoundError
from app.modules.datasets import repository
from app.modules.datasets.schemas import (
    UploadResponse, CleanConfig, CleanResponse,
    PreviewResponse, DatasetResponse, DatasetProfileResponse,
    ColumnMetadata, CleaningReport,
)
from app.modules.datasets.cleaner import (
    build_cleaning_report,
    apply_clean,
    compute_column_metadata,
    compute_statistics,
)
from app.ai.observability import log_llm_usage
from app.ai.llm_factory import get_fast_llm

logger = logging.getLogger(__name__)

# ── Storage path ───────────────────────────────────────────
STORAGE_PATH = Path(settings.storage_path)
UPLOADS_DIR = STORAGE_PATH / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def _validate_file(file: UploadFile) -> str:
    """Validate extension and return file type ('csv' or 'xlsx')."""
    if not file.filename:
        raise InvalidFileError("No filename provided.")

    ext = Path(file.filename).suffix.lower().lstrip(".")
    if ext not in settings.allowed_extensions_list:
        raise InvalidFileError(
            f"File type '.{ext}' is not allowed. Accepted: {settings.allowed_extensions}"
        )
    return ext


def _sanitize_filename(original: str, user_id: str) -> str:
    """Create a safe, unique filename."""
    stem = Path(original).stem
    ext = Path(original).suffix.lower()
    # Keep only alphanumeric + dash + underscore
    safe_stem = "".join(c if c.isalnum() or c in "-_" else "_" for c in stem)
    unique_id = str(uuid.uuid4())[:8]
    return f"{user_id[:8]}_{safe_stem}_{unique_id}{ext}"


def _read_file(file_path: Path, file_type: str) -> pd.DataFrame:
    """Read CSV or XLSX into a DataFrame."""
    if file_type == "csv":
        return pd.read_csv(file_path, low_memory=False)
    elif file_type == "xlsx":
        return pd.read_excel(file_path, engine="openpyxl")
    raise InvalidFileError(f"Unsupported file type: {file_type}")


async def _generate_suggestions(df: pd.DataFrame) -> list[str]:
    """
   Call Ollama LLM with suggestion.md prompt to generate 5 smart questions.
    Returns list of question strings.
    Falls back to default questions if LLM fails.
    """
    from app.ai.llm_factory import get_fast_llm
    from app.ai.llm_factory import get_fast_llm
    from langchain_core.messages import HumanMessage
    from app.core.config import settings

    # Load prompt template
    prompt_path = Path(__file__).parent.parent.parent / "ai" / "prompts" / "suggestion.md"
    prompt_template = prompt_path.read_text()

    # Build context
    columns = list(df.columns)
    sample = df.head(3).to_dict(orient="records")
    # Clean sample for JSON serialization
    import numpy as np
    for row in sample:
        for k, v in row.items():
            if isinstance(v, (np.integer,)):
                row[k] = int(v)
            elif isinstance(v, (np.floating,)):
                row[k] = float(v)
            elif pd.isna(v) if not isinstance(v, str) else False:
                row[k] = None

    prompt = prompt_template.format(
        columns=", ".join(columns),
        sample=json.dumps(sample, indent=2)
    )

    start = time.perf_counter()
    try:
        llm = get_fast_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        latency = round((time.perf_counter() - start) * 1000, 2)

        # Parse JSON response
        raw = response.content.strip()
        # Remove any markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        questions = json.loads(raw.strip())
        if isinstance(questions, list) and len(questions) > 0:
            log_llm_usage("generate_suggestions", settings.ollama_fast_model, latency_ms=latency)
            return questions[:5]
    except Exception as e:
        logger.warning(f"LLM suggestion generation failed: {e}. Using defaults.")

    # Fallback questions based on column names
    return _default_suggestions(df)


def _default_suggestions(df: pd.DataFrame) -> list[str]:
    """Fallback suggestions when LLM is unavailable."""
    cols = list(df.columns)
    suggestions = [
        f"What is the distribution of {cols[0]}?",
        f"Show me the top 10 rows by {cols[-1]}.",
        "How many missing values are there per column?",
        "What are the summary statistics for all numeric columns?",
        "Show me the correlation between numeric columns.",
    ]
    return suggestions[:5]


# ════════════════════════════════════════════════════════════
# SERVICE FUNCTIONS
# ════════════════════════════════════════════════════════════

async def upload_and_profile(
    file: UploadFile,
    user_id: str,
    db: Session,
) -> UploadResponse:
    """
    Main upload flow:
    validate → save → read → profile → clean report → suggestions → save to DB
    """

    # a. Validate extension
    file_type = _validate_file(file)

    # b. Read file content and check size
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise FileTooLargeError(settings.max_upload_size_mb)

    # c. Sanitize filename and save to disk
    stored_filename = _sanitize_filename(file.filename, user_id)
    file_path = UPLOADS_DIR / stored_filename
    file_path.write_bytes(content)

    try:
        # d. Read into pandas
        df = _read_file(file_path, file_type)

        if df.empty:
            file_path.unlink(missing_ok=True)
            raise InvalidFileError("The uploaded file is empty.")

        # e. Compute metadata and statistics
        columns_metadata = compute_column_metadata(df)
        statistics = compute_statistics(df)
        null_summary = {col: int(df[col].isnull().sum()) for col in df.columns}

        # f. Save Dataset record to DB
        dataset = repository.create_dataset(
            db=db,
            user_id=user_id,
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_path=str(file_path),
            file_type=file_type,
            row_count=len(df),
            col_count=len(df.columns),
        )

        # g. Generate LLM suggestions
        suggestions = await _generate_suggestions(df)

        # h. Save DatasetProfile to DB
        repository.create_profile(
            db=db,
            dataset_id=dataset.id,
            columns_metadata=columns_metadata,
            statistics=statistics,
            null_summary=null_summary,
            sample_questions=suggestions,
        )

        # i. Update status to profiled
        repository.update_dataset_status(db, dataset.id, "profiled")

        # j. Build cleaning report (what issues exist)
        cleaning_report = build_cleaning_report(df, dataset.id)

        # k. Reload dataset with profile for response
        db.refresh(dataset)

        logger.info(f"Dataset uploaded: id={dataset.id} user={user_id} rows={len(df)}")

        return UploadResponse(
            dataset=DatasetResponse.model_validate(dataset),
            cleaning_report=cleaning_report,
            suggestions=suggestions,
        )

    except (InvalidFileError, FileTooLargeError):
        file_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        file_path.unlink(missing_ok=True)
        logger.error(f"Upload failed for user {user_id}: {e}", exc_info=True)
        raise InvalidFileError(f"Failed to process file: {str(e)}")


def get_preview(dataset_id: str, user_id: str, db: Session) -> PreviewResponse:
    """Return first 50 rows of a dataset."""
    dataset = repository.get_dataset_by_id(db, dataset_id)
    if not dataset or dataset.user_id != user_id:
        raise DatasetNotFoundError(dataset_id)

    df = _read_file(Path(dataset.file_path), dataset.file_type)

    # Convert to JSON-safe format
    preview_df = df.head(50)
    rows = []
    for _, row in preview_df.iterrows():
        row_dict = {}
        for col, val in row.items():
            import numpy as np
            if isinstance(val, (np.integer,)):
                row_dict[col] = int(val)
            elif isinstance(val, (np.floating,)):
                row_dict[col] = None if pd.isna(val) else float(val)
            elif pd.isna(val) if not isinstance(val, str) else False:
                row_dict[col] = None
            else:
                row_dict[col] = str(val)
        rows.append(row_dict)

    return PreviewResponse(
        dataset_id=dataset_id,
        columns=list(df.columns),
        dtypes={col: str(df[col].dtype) for col in df.columns},
        rows=rows,
        total_rows=len(df),
    )


async def clean_dataset(
    dataset_id: str,
    config: CleanConfig,
    user_id: str,
    db: Session,
) -> CleanResponse:
    """
    Apply cleaning operations and save as a new dataset record.
    Original dataset is kept untouched.
    """
    dataset = repository.get_dataset_by_id(db, dataset_id)
    if not dataset or dataset.user_id != user_id:
        raise DatasetNotFoundError(dataset_id)

    df = _read_file(Path(dataset.file_path), dataset.file_type)
    rows_before = len(df)

    # Apply cleaning
    cleaned_df, changes = apply_clean(df, config)
    rows_after = len(cleaned_df)

    # Save cleaned file
    clean_filename = _sanitize_filename(
        f"cleaned_{dataset.original_filename}", user_id
    )
    clean_path = UPLOADS_DIR / clean_filename

    if dataset.file_type == "csv":
        cleaned_df.to_csv(clean_path, index=False)
    else:
        cleaned_df.to_excel(clean_path, index=False, engine="openpyxl")

    # Save new dataset record for cleaned version
    cleaned_dataset = repository.create_dataset(
        db=db,
        user_id=user_id,
        original_filename=f"cleaned_{dataset.original_filename}",
        stored_filename=clean_filename,
        file_path=str(clean_path),
        file_type=dataset.file_type,
        row_count=rows_after,
        col_count=len(cleaned_df.columns),
    )

    # Profile the cleaned dataset too
    columns_metadata = compute_column_metadata(cleaned_df)
    statistics = compute_statistics(cleaned_df)
    null_summary = {col: int(cleaned_df[col].isnull().sum()) for col in cleaned_df.columns}
    suggestions = await _generate_suggestions(cleaned_df)

    repository.create_profile(
        db=db,
        dataset_id=cleaned_dataset.id,
        columns_metadata=columns_metadata,
        statistics=statistics,
        null_summary=null_summary,
        sample_questions=suggestions,
    )
    repository.update_dataset_status(db, cleaned_dataset.id, "cleaned")

    logger.info(
        f"Dataset cleaned: original={dataset_id} cleaned={cleaned_dataset.id} "
        f"rows: {rows_before}→{rows_after} changes={len(changes)}"
    )

    return CleanResponse(
        original_dataset_id=dataset_id,
        cleaned_dataset_id=cleaned_dataset.id,
        changes_applied=changes,
        rows_before=rows_before,
        rows_after=rows_after,
    )


def list_datasets(user_id: str, db: Session) -> list:
    """Return all datasets for a user, newest first."""
    return repository.get_datasets_by_user(db, user_id)


def delete_dataset_service(dataset_id: str, user_id: str, db: Session) -> bool:
    """Delete a dataset and its file from disk."""
    dataset = repository.get_dataset_by_id(db, dataset_id)
    if not dataset or dataset.user_id != user_id:
        raise DatasetNotFoundError(dataset_id)

    # Delete file from disk
    file_path = Path(dataset.file_path)
    file_path.unlink(missing_ok=True)

    # Delete from DB (cascades to profile)
    repository.delete_dataset(db, dataset_id)
    logger.info(f"Dataset deleted: id={dataset_id} user={user_id}")
    return True