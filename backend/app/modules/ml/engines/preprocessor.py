import logging
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
# TIME COLUMN DETECTION
# ════════════════════════════════════════════════════════════

DATE_KEYWORDS = [
    "date", "time", "day", "month", "year",
    "created", "updated", "ordered", "at", "timestamp",
]


def detect_time_column(df: pd.DataFrame) -> str | None:
    """
    Auto-detect the time/date column in a DataFrame.
    Returns the column name or None if not found.
    """
    # Check column names for date keywords
    for col in df.columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in DATE_KEYWORDS):
            # Verify it's actually parseable as dates
            try:
                pd.to_datetime(df[col].dropna().iloc[:5])
                logger.info(f"Auto-detected time column: '{col}'")
                return col
            except (ValueError, TypeError, IndexError):
                continue

    # Check if any column IS already datetime dtype
    for col in df.select_dtypes(include=["datetime64"]).columns:
        return col

    logger.info("No time column detected in dataset.")
    return None


def detect_numeric_target_columns(df: pd.DataFrame) -> list[str]:
    """
    Return numeric columns that are likely targets for prediction.
    Prioritizes columns with business-sounding names.
    """
    business_keywords = [
        "revenue", "sales", "profit", "amount", "value",
        "price", "quantity", "count", "total", "income",
    ]
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # Prioritize business-named columns
    priority = [c for c in numeric_cols if any(k in c.lower() for k in business_keywords)]
    others = [c for c in numeric_cols if c not in priority]

    return priority + others


# ════════════════════════════════════════════════════════════
# TIME FEATURE ENGINEERING
# ════════════════════════════════════════════════════════════

def create_time_features(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """
    Create time-based features for forecasting.
    Adds: month, quarter, day_of_week, lag_1, lag_2, rolling_mean_3
    Returns new DataFrame with features added.
    """
    df = df.copy()

    # Parse date column
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df = df.sort_values(date_col).reset_index(drop=True)

    # Calendar features
    df["_month"]       = df[date_col].dt.month
    df["_quarter"]     = df[date_col].dt.quarter
    df["_day_of_week"] = df[date_col].dt.dayofweek
    df["_day_of_year"] = df[date_col].dt.dayofyear
    df["_year"]        = df[date_col].dt.year

    # Numeric time index (for trend)
    df["_time_index"]  = np.arange(len(df))

    logger.info(f"Created time features from column '{date_col}'")
    return df


def add_lag_features(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """
    Add lag and rolling window features for the target column.
    Requires df to be sorted by time already.
    """
    df = df.copy()
    df["_lag_1"]          = df[target_col].shift(1)
    df["_lag_2"]          = df[target_col].shift(2)
    df["_lag_3"]          = df[target_col].shift(3)
    df["_rolling_mean_3"] = df[target_col].shift(1).rolling(3).mean()
    df["_rolling_mean_7"] = df[target_col].shift(1).rolling(7).mean()
    return df


# ════════════════════════════════════════════════════════════
# CATEGORICAL ENCODING
# ════════════════════════════════════════════════════════════

def encode_categoricals(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, LabelEncoder]]:
    """
    Label-encode all object/category columns.
    Returns encoded DataFrame and dict of {col: encoder} for inverse transform.
    """
    df = df.copy()
    encoders: dict[str, LabelEncoder] = {}

    for col in df.select_dtypes(include=["object", "category"]).columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    return df, encoders


# ════════════════════════════════════════════════════════════
# FEATURE SCALING
# ════════════════════════════════════════════════════════════

def scale_features(
    df: pd.DataFrame,
    feature_cols: list[str],
) -> tuple[pd.DataFrame, StandardScaler]:
    """
    Standard-scale the given feature columns.
    Returns scaled DataFrame and fitted scaler.
    """
    df = df.copy()
    scaler = StandardScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols].fillna(0))
    return df, scaler


# ════════════════════════════════════════════════════════════
# AGGREGATION HELPER
# ════════════════════════════════════════════════════════════

def aggregate_by_time(
    df: pd.DataFrame,
    date_col: str,
    target_col: str,
    freq: str = "ME",
) -> pd.DataFrame:
    """
    Aggregate target column by time period.
    freq: 'ME' = month end, 'W' = week, 'D' = day, 'QE' = quarter end
    Returns DataFrame with [date_col, target_col] aggregated.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, target_col])
    df = df.set_index(date_col)
    aggregated = df[target_col].resample(freq).sum().reset_index()
    aggregated.columns = [date_col, target_col]
    return aggregated.dropna()