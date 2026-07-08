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
        "revenue":  [100.0, 200.0, None, 400.0, None],
        "category": ["Electronics", "electronics", "ELECTRONICS", "Furniture", "furniture"],
        "quantity": [10, -5, 3, 0, 8],
        "order_date": ["2024-01-01", "2024-01-02", "not-a-date", "2024-01-04", "2024-01-05"],
        "product":  ["A", "B", "A", "B", "A"],
    })


@pytest.fixture
def df_with_duplicates():
    return pd.DataFrame({
        "id":    [1, 2, 2, 3, 4],
        "value": [10, 20, 20, 30, 40],
    })


# ── Test 1 ─────────────────────────────────────────────────
def test_detect_missing_values(sample_df):
    result = detect_missing_values(sample_df)
    assert "revenue" in result
    assert result["revenue"]["count"] == 2
    assert result["revenue"]["pct"] == 40.0
    assert "category" not in result  # no nulls in category


# ── Test 2 ─────────────────────────────────────────────────
def test_detect_duplicates(df_with_duplicates):
    count = detect_duplicates(df_with_duplicates)
    assert count == 1  # row index 2 is a duplicate of row index 1


# ── Test 3 ─────────────────────────────────────────────────
def test_detect_no_duplicates(sample_df):
    count = detect_duplicates(sample_df)
    assert count == 0


# ── Test 4 ─────────────────────────────────────────────────
def test_detect_negative_values(sample_df):
    result = detect_negative_values(sample_df)
    assert "quantity" in result
    assert result["quantity"] == 1  # one negative value: -5


# ── Test 5 ─────────────────────────────────────────────────
def test_detect_inconsistent_categories(sample_df):
    result = detect_inconsistent_categories(sample_df)
    assert "category" in result
    variants = result["category"]
    lower_versions = [v.lower() for v in variants]
    assert "electronics" in lower_versions
    assert "furniture" in lower_versions


# ── Test 6 ─────────────────────────────────────────────────
def test_apply_clean_fill_median(sample_df):
    config = CleanConfig(fill_missing={"revenue": "fill_median"})
    cleaned_df, changes = apply_clean(sample_df, config)
    assert cleaned_df["revenue"].isnull().sum() == 0
    assert any("median" in c for c in changes)


# ── Test 7 ─────────────────────────────────────────────────
def test_apply_clean_remove_duplicates(df_with_duplicates):
    config = CleanConfig(remove_duplicates=True)
    cleaned_df, changes = apply_clean(df_with_duplicates, config)
    assert len(cleaned_df) == 4  # was 5, one duplicate removed
    assert any("duplicate" in c.lower() for c in changes)


# ── Test 8 ─────────────────────────────────────────────────
def test_apply_clean_standardize_categories(sample_df):
    config = CleanConfig(standardize_categories=["category"])
    cleaned_df, changes = apply_clean(sample_df, config)
    unique_vals = cleaned_df["category"].str.lower().unique()
    # After title-casing all should normalize to same form
    assert any("standardized" in c.lower() for c in changes)


# ── Test 9 ─────────────────────────────────────────────────
def test_build_cleaning_report_finds_all_issues(sample_df):
    report = build_cleaning_report(sample_df, "test-dataset-id")
    issue_types = [i.issue_type for i in report.issues]
    assert "missing_values" in issue_types
    assert report.total_issues > 0


# ── Test 10 ────────────────────────────────────────────────
def test_apply_clean_fix_negatives(sample_df):
    config = CleanConfig(fix_negative_columns=["quantity"])
    cleaned_df, changes = apply_clean(sample_df, config)
    assert (cleaned_df["quantity"] < 0).sum() == 0
    assert any("negative" in c.lower() for c in changes)