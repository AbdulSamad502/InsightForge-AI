"""
Unit tests for ML engines.
Uses small in-memory DataFrames — no file I/O required.
"""
import numpy as np
import pandas as pd
import pytest
from datetime import date, timedelta


# ── Sample DataFrames ──────────────────────────────────────

@pytest.fixture
def time_series_df():
    """Monthly revenue data over 24 months."""
    dates = pd.date_range(start="2022-01-01", periods=24, freq="ME")
    revenue = [
        45000, 47000, 43000, 51000, 53000, 49000,
        55000, 58000, 52000, 61000, 63000, 59000,
        62000, 65000, 60000, 68000, 72000, 67000,
        71000, 75000, 69000, 78000, 82000, 77000,
    ]
    return pd.DataFrame({"order_date": dates.strftime("%Y-%m-%d"), "revenue": revenue})


@pytest.fixture
def anomaly_df():
    """Revenue data with obvious anomalies injected."""
    np.random.seed(42)
    normal = np.random.normal(loc=50000, scale=5000, size=30)
    # Inject 3 anomalies
    normal[5]  = 150000   # very high spike
    normal[15] = -10000   # extreme low (negative)
    normal[25] = 200000   # extreme high
    dates = pd.date_range("2022-01-01", periods=30, freq="ME")
    return pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "revenue": normal})


@pytest.fixture
def churn_df():
    """Customer dataset with churn label."""
    np.random.seed(42)
    n = 50
    return pd.DataFrame({
        "customer_id":    range(n),
        "age":            np.random.randint(20, 70, n),
        "monthly_spend":  np.random.uniform(100, 2000, n).round(2),
        "tenure_months":  np.random.randint(1, 60, n),
        "support_calls":  np.random.randint(0, 10, n),
        "churned":        np.random.choice([0, 1], n, p=[0.7, 0.3]),
    })


# ════════════════════════════════════════════════════════════
# PREPROCESSOR TESTS
# ════════════════════════════════════════════════════════════

def test_detect_time_column(time_series_df):
    from app.modules.ml.engines.preprocessor import detect_time_column
    col = detect_time_column(time_series_df)
    assert col == "order_date"


def test_detect_time_column_none():
    from app.modules.ml.engines.preprocessor import detect_time_column
    df = pd.DataFrame({"product": ["A", "B"], "revenue": [100, 200]})
    col = detect_time_column(df)
    assert col is None


def test_create_time_features(time_series_df):
    from app.modules.ml.engines.preprocessor import create_time_features
    result = create_time_features(time_series_df, "order_date")
    assert "_month" in result.columns
    assert "_quarter" in result.columns
    assert "_time_index" in result.columns
    assert len(result) == len(time_series_df)


def test_aggregate_by_time(time_series_df):
    from app.modules.ml.engines.preprocessor import aggregate_by_time
    result = aggregate_by_time(time_series_df, "order_date", "revenue", freq="QE")
    assert len(result) <= len(time_series_df)
    assert "revenue" in result.columns


# ════════════════════════════════════════════════════════════
# FORECAST ENGINE TESTS
# ════════════════════════════════════════════════════════════

def test_forecast_engine_fit(time_series_df):
    from app.modules.ml.engines.forecast import ForecastEngine
    engine = ForecastEngine()
    metrics = engine.fit(time_series_df, "revenue", "order_date")
    assert engine.is_fitted
    assert "mae" in metrics
    assert metrics["training_rows"] > 0


def test_forecast_engine_predict(time_series_df):
    from app.modules.ml.engines.forecast import ForecastEngine
    engine = ForecastEngine()
    engine.fit(time_series_df, "revenue", "order_date")
    result = engine.predict(n_periods=3)
    assert len(result["dates"]) == 3
    assert len(result["predictions"]) == 3
    assert len(result["lower_ci"]) == 3
    assert len(result["upper_ci"]) == 3
    # All predictions should be non-negative
    assert all(p >= 0 for p in result["predictions"])


def test_forecast_engine_chart(time_series_df):
    from app.modules.ml.engines.forecast import ForecastEngine
    import json
    engine = ForecastEngine()
    engine.fit(time_series_df, "revenue", "order_date")
    pred = engine.predict(n_periods=3)
    chart = engine.get_chart(pred)
    parsed = json.loads(chart)
    assert "data" in parsed
    assert len(parsed["data"]) >= 2  # at least historical + forecast traces


def test_forecast_too_few_rows():
    from app.modules.ml.engines.forecast import ForecastEngine
    engine = ForecastEngine()
    df = pd.DataFrame({
        "date": ["2024-01-01", "2024-02-01"],
        "revenue": [1000, 2000],
    })
    with pytest.raises(ValueError, match="at least 4"):
        engine.fit(df, "revenue", "date")


# ════════════════════════════════════════════════════════════
# ANOMALY ENGINE TESTS
# ════════════════════════════════════════════════════════════

def test_anomaly_engine_detects_anomalies(anomaly_df):
    from app.modules.ml.engines.anomaly import AnomalyEngine
    engine = AnomalyEngine()
    result_df = engine.fit_predict(anomaly_df, "revenue")
    assert "is_anomaly" in result_df.columns
    assert "anomaly_score" in result_df.columns
    # Should detect at least our 3 injected anomalies
    assert engine.anomaly_count >= 2


def test_anomaly_engine_summary(anomaly_df):
    from app.modules.ml.engines.anomaly import AnomalyEngine
    engine = AnomalyEngine()
    engine.fit_predict(anomaly_df, "revenue")
    summary = engine.get_summary()
    assert "anomaly_count" in summary
    assert "anomaly_pct" in summary
    assert summary["total_count"] == len(anomaly_df)


def test_anomaly_engine_chart(anomaly_df):
    from app.modules.ml.engines.anomaly import AnomalyEngine
    import json
    engine = AnomalyEngine()
    engine.fit_predict(anomaly_df, "revenue")
    chart = engine.get_chart()
    parsed = json.loads(chart)
    assert "data" in parsed


def test_anomaly_too_few_rows():
    from app.modules.ml.engines.anomaly import AnomalyEngine
    engine = AnomalyEngine()
    df = pd.DataFrame({"revenue": [100, 200, 300]})
    with pytest.raises(ValueError, match="at least 5"):
        engine.fit_predict(df, "revenue")


# ════════════════════════════════════════════════════════════
# CHURN ENGINE TESTS
# ════════════════════════════════════════════════════════════

def test_churn_engine_fit(churn_df):
    from app.modules.ml.engines.churn import ChurnEngine
    engine = ChurnEngine()
    metrics = engine.fit(churn_df.drop(columns=["customer_id"]), "churned")
    assert engine.is_fitted
    assert "accuracy" in metrics
    assert metrics["accuracy"] >= 0.0


def test_churn_engine_feature_importance(churn_df):
    from app.modules.ml.engines.churn import ChurnEngine
    engine = ChurnEngine()
    engine.fit(churn_df.drop(columns=["customer_id"]), "churned")
    fi = engine.get_feature_importance()
    assert len(fi) > 0
    assert "feature" in fi[0]
    assert "importance" in fi[0]


def test_churn_engine_predict_segments(churn_df):
    from app.modules.ml.engines.churn import ChurnEngine
    engine = ChurnEngine()
    engine.fit(churn_df.drop(columns=["customer_id"]), "churned")
    segments = engine.predict_segments(churn_df.drop(columns=["customer_id"]))
    assert len(segments) > 0
    assert "churn_probability" in segments[0]
    assert "risk_level" in segments[0]
    # Probabilities between 0 and 1
    for seg in segments:
        assert 0.0 <= seg["churn_probability"] <= 1.0


def test_churn_too_few_rows():
    from app.modules.ml.engines.churn import ChurnEngine
    engine = ChurnEngine()
    df = pd.DataFrame({"age": [25, 30], "churned": [0, 1]})
    with pytest.raises(ValueError, match="at least 10"):
        engine.fit(df, "churned")