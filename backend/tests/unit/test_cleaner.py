import pandas as pd
import numpy as np
import pytest
from app.modules.datasets.cleaner import (
    detect_missing_values,
    detect_duplicates,
    detect_negative_values,
    detect_inconsistent_categories,
    apply_clean,
    build_cleaning_report,
)
from app.modules.datasets.schemas import CleanConfig


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "revenue":   [100.0, 200.0, None, 400.0, None],
        "category":  ["Electronics", "electronics", "ELECTRONICS", "Furniture", "furniture"],
        "quantity":  [10, -5, 3, 0, 8],
        "order_date": ["2024-01-01", "2024-01-02", "not-a-date", "2024-01-04", "2024-01-05"],
        "product":   ["A", "B", "A", "B", "A"],
    })


@pytest.fixture
def df_with_duplicates():
    return pd.DataFrame({
        "id":    [1, 2, 2, 3, 4],
        "value": [10, 20, 20, 30, 40],
    })


def test_detects_missing_values(sample_df):
    result = detect_missing_values(sample_df)
    assert "revenue" in result
    assert result["revenue"]["count"] == 2
    assert result["revenue"]["pct"] == 40.0
    assert "category" not in result


def test_detects_duplicates(df_with_duplicates):
    count = detect_duplicates(df_with_duplicates)
    assert count == 1


def test_detect_no_duplicates(sample_df):
    assert detect_duplicates(sample_df) == 0


def test_detects_negative_prices(sample_df):
    result = detect_negative_values(sample_df)
    assert "quantity" in result
    assert result["quantity"] == 1


def test_detects_invalid_dates(sample_df):
    result = {}
    from app.modules.datasets.cleaner import detect_invalid_dates
    result = detect_invalid_dates(sample_df)
    assert "order_date" in result
    assert "not-a-date" in result["order_date"]


def test_detects_inconsistent_categories(sample_df):
    result = detect_inconsistent_categories(sample_df)
    assert "category" in result
    lower_variants = [v.lower() for v in result["category"]]
    assert "electronics" in lower_variants


def test_apply_fill_missing_with_median(sample_df):
    config = CleanConfig(fill_missing={"revenue": "fill_median"})
    cleaned, changes = apply_clean(sample_df, config)
    assert cleaned["revenue"].isnull().sum() == 0
    assert any("median" in c for c in changes)


def test_apply_remove_duplicates(df_with_duplicates):
    config = CleanConfig(remove_duplicates=True)
    cleaned, changes = apply_clean(df_with_duplicates, config)
    assert len(cleaned) == 4
    assert any("duplicate" in c.lower() for c in changes)


def test_apply_standardize_categories(sample_df):
    config = CleanConfig(standardize_categories=["category"])
    cleaned, changes = apply_clean(sample_df, config)
    assert any("standardized" in c.lower() for c in changes)


def test_build_cleaning_report(sample_df):
    report = build_cleaning_report(sample_df, "test-id")
    issue_types = [i.issue_type for i in report.issues]
    assert "missing_values" in issue_types
    assert report.total_issues > 0