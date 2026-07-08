import pandas as pd
import numpy as np
from app.modules.datasets.schemas import CleaningIssue, CleaningReport, CleanConfig


# ════════════════════════════════════════════════════════════
# DETECTION FUNCTIONS
# ════════════════════════════════════════════════════════════

def detect_missing_values(df: pd.DataFrame) -> dict[str, dict]:
    """
    Returns per-column missing value info.
    Example: {"revenue": {"count": 28, "pct": 12.3}}
    """
    result = {}
    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        if null_count > 0:
            result[col] = {
                "count": null_count,
                "pct": round(null_count / len(df) * 100, 1),
            }
    return result


def detect_duplicates(df: pd.DataFrame) -> int:
    """Returns the number of fully duplicate rows."""
    return int(df.duplicated().sum())


def detect_negative_values(df: pd.DataFrame) -> dict[str, int]:
    """
    Finds numeric columns that contain negative values
    where negative doesn't make business sense (price, quantity, revenue).
    Returns: {"revenue": 5, "quantity": 2}
    """
    result = {}
    # Only check columns whose names suggest they shouldn't be negative
    suspicious_keywords = [
        "price", "revenue", "sales", "quantity", "qty",
        "amount", "cost", "profit", "income", "value", "total",
    ]
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        col_lower = col.lower()
        if any(kw in col_lower for kw in suspicious_keywords):
            neg_count = int((df[col] < 0).sum())
            if neg_count > 0:
                result[col] = neg_count
    return result


def detect_invalid_dates(df: pd.DataFrame) -> dict[str, list]:
    """
    Finds columns that look like dates but have unparseable values.
    Returns: {"order_date": ["13/45/2023", "not-a-date"]}
    """
    result = {}
    date_keywords = [
    "date",
    "time",
    "day",
    "month",
    "year",
    "created",
    "updated",
]

    for col in df.select_dtypes(include=["object"]).columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in date_keywords):
            bad_values = []
            for val in df[col].dropna().unique()[:50]:  # check first 50 unique values
                try:
                    pd.to_datetime(val)
                except (ValueError, TypeError):
                    bad_values.append(str(val))
            if bad_values:
                result[col] = bad_values[:10]  # return max 10 examples
    return result


def detect_inconsistent_categories(df: pd.DataFrame) -> dict[str, list]:
    """
    Finds categorical columns where the same value appears in different cases.
    Example: {"category": ["Electronics", "electronics", "ELECTRONICS"]}
    """
    result = {}
    cat_cols = df.select_dtypes(include=["object"]).columns

    for col in cat_cols:
        unique_vals = df[col].dropna().unique()
        if len(unique_vals) > 50:
            # Too many unique values — probably text, not category
            continue

        # Group values by their lowercase version
        lower_groups: dict[str, list] = {}
        for val in unique_vals:
            key = str(val).lower().strip()
            if key not in lower_groups:
                lower_groups[key] = []
            lower_groups[key].append(str(val))

        # Find groups with more than one variant
        inconsistent = []
        for variants in lower_groups.values():
            if len(variants) > 1:
                inconsistent.extend(variants)

        if inconsistent:
            result[col] = inconsistent

    return result


# ════════════════════════════════════════════════════════════
# BUILD CLEANING REPORT
# ════════════════════════════════════════════════════════════

def build_cleaning_report(df: pd.DataFrame, dataset_id: str) -> CleaningReport:
    """
    Runs all detections and assembles a CleaningReport.
    This is what the frontend displays as the cleaning card UI.
    """
    issues: list[CleaningIssue] = []

    # ── Missing values ─────────────────────────────────────
    missing = detect_missing_values(df)
    for col, info in missing.items():
        issues.append(CleaningIssue(
            issue_type="missing_values",
            column=col,
            description=f"'{col}' has {info['count']} missing values ({info['pct']}%)",
            count=info["count"],
            fix_options=["fill_median", "fill_mean", "fill_mode", "drop_rows", "skip"],
        ))

    # ── Duplicates ─────────────────────────────────────────
    dup_count = detect_duplicates(df)
    has_duplicates = dup_count > 0
    if has_duplicates:
        issues.append(CleaningIssue(
            issue_type="duplicates",
            column=None,
            description=f"{dup_count} duplicate rows found in dataset",
            count=dup_count,
            fix_options=["remove_duplicates", "skip"],
        ))

    # ── Negative values ────────────────────────────────────
    negatives = detect_negative_values(df)
    for col, count in negatives.items():
        issues.append(CleaningIssue(
            issue_type="negative_values",
            column=col,
            description=f"'{col}' has {count} unexpected negative values",
            count=count,
            fix_options=["replace_with_zero", "drop_rows", "skip"],
        ))

    # ── Invalid dates ──────────────────────────────────────
    bad_dates = detect_invalid_dates(df)
    for col, bad_vals in bad_dates.items():
        issues.append(CleaningIssue(
            issue_type="invalid_dates",
            column=col,
            description=f"'{col}' has {len(bad_vals)} unparseable date values",
            count=len(bad_vals),
            fix_options=["drop_rows", "skip"],
        ))

    # ── Inconsistent categories ────────────────────────────
    inconsistent = detect_inconsistent_categories(df)
    for col, variants in inconsistent.items():
        issues.append(CleaningIssue(
            issue_type="inconsistent_categories",
            column=col,
            description=f"'{col}' has inconsistent casing: {', '.join(variants[:4])}",
            count=len(variants),
            fix_options=["standardize_lowercase", "standardize_titlecase", "skip"],
        ))

    return CleaningReport(
        dataset_id=dataset_id,
        total_issues=len(issues),
        issues=issues,
        has_duplicates=has_duplicates,
        duplicate_count=dup_count,
    )


# ════════════════════════════════════════════════════════════
# APPLY CLEANING
# ════════════════════════════════════════════════════════════

def apply_clean(df: pd.DataFrame, config: CleanConfig) -> tuple[pd.DataFrame, list[str]]:
    """
    Applies the user's chosen fixes to the DataFrame.
    Returns: (cleaned_df, list of changes applied as strings)
    """
    df = df.copy()
    changes: list[str] = []

    # ── Remove duplicates ──────────────────────────────────
    if config.remove_duplicates:
        before = len(df)
        df = df.drop_duplicates()
        removed = before - len(df)
        if removed > 0:
            changes.append(f"Removed {removed} duplicate rows")

    # ── Fill missing values ────────────────────────────────
    for col, method in config.fill_missing.items():
        if col not in df.columns:
            continue
        null_count = df[col].isnull().sum()
        if null_count == 0:
            continue

        if method == "fill_median" and pd.api.types.is_numeric_dtype(df[col]):
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            changes.append(f"Filled {null_count} missing values in '{col}' with median ({median_val:.2f})")

        elif method == "fill_mean" and pd.api.types.is_numeric_dtype(df[col]):
            mean_val = df[col].mean()
            df[col] = df[col].fillna(mean_val)
            changes.append(f"Filled {null_count} missing values in '{col}' with mean ({mean_val:.2f})")

        elif method == "fill_mode":
            mode_val = df[col].mode()
            if not mode_val.empty:
                df[col] = df[col].fillna(mode_val[0])
                changes.append(f"Filled {null_count} missing values in '{col}' with mode ('{mode_val[0]}')")

        elif method == "drop_rows":
            before = len(df)
            df = df.dropna(subset=[col])
            dropped = before - len(df)
            changes.append(f"Dropped {dropped} rows with missing '{col}'")

    # ── Fix negative values ────────────────────────────────
    for col in config.fix_negative_columns:
        if col not in df.columns:
            continue
        neg_count = int((df[col] < 0).sum())
        if neg_count > 0:
            df[col] = df[col].clip(lower=0)
            changes.append(f"Replaced {neg_count} negative values in '{col}' with 0")

    # ── Standardize categories ─────────────────────────────
    for col in config.standardize_categories:
        if col not in df.columns:
            continue
        df[col] = df[col].str.strip().str.title()
        changes.append(f"Standardized casing in '{col}' to Title Case")

    return df, changes


# ════════════════════════════════════════════════════════════
# COLUMN TYPE DETECTION
# ════════════════════════════════════════════════════════════

def detect_column_type(series: pd.Series) -> str:
    """
    Returns a business-friendly type label for a column.
    Returns: "numeric" | "datetime" | "categorical" | "text"
    """
    # Already numeric
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    # Try to parse as datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    # Try parsing object columns as datetime
    if series.dtype == object:
        try:
            pd.to_datetime(series.dropna().iloc[:20])
            return "datetime"
        except (ValueError, TypeError):
            pass

        # Decide between categorical and text
        unique_ratio = series.nunique() / max(len(series), 1)
        if unique_ratio < 0.3:  # less than 30% unique = likely categorical
            return "categorical"
        return "text"

    return "text"


def compute_column_metadata(df: pd.DataFrame) -> list[dict]:
    """
    Returns metadata for every column.
    Used to build DatasetProfile.columns_metadata
    """
    metadata = []
    for col in df.columns:
        series = df[col]
        col_type = detect_column_type(series)
        sample = series.dropna().head(3).tolist()
        # Convert numpy types to Python native for JSON serialization
        sample = [
            int(v) if isinstance(v, (np.integer,)) else
            float(v) if isinstance(v, (np.floating,)) else
            str(v)
            for v in sample
        ]
        metadata.append({
            "name": col,
            "dtype": col_type,
            "null_count": int(series.isnull().sum()),
            "null_pct": round(series.isnull().sum() / max(len(df), 1) * 100, 1),
            "unique_count": int(series.nunique()),
            "sample_values": sample,
        })
    return metadata


def compute_statistics(df: pd.DataFrame) -> dict:
    """
    Compute min, max, mean, std for numeric columns.
    Returns JSON-serializable dict.
    """
    stats = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        desc = df[col].describe()
        stats[col] = {
            "min": round(float(desc["min"]), 2),
            "max": round(float(desc["max"]), 2),
            "mean": round(float(desc["mean"]), 2),
            "std": round(float(desc["std"]), 2),
            "median": round(float(df[col].median()), 2),
        }
    return stats