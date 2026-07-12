import logging
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

from app.modules.ml.engines.preprocessor import (
    detect_time_column,
    detect_numeric_target_columns,
    create_time_features,
    add_lag_features,
    aggregate_by_time,
)

logger = logging.getLogger(__name__)

# ── Feature columns used for training ─────────────────────
TIME_FEATURE_COLS = [
    "_time_index", "_month", "_quarter",
    "_day_of_week", "_day_of_year", "_year",
    "_lag_1", "_lag_2", "_lag_3",
    "_rolling_mean_3", "_rolling_mean_7",
]


class ForecastEngine:
    """
    Sales/Revenue forecasting using GradientBoostingRegressor.
    Supports any time-indexed numeric column.
    """

    def __init__(self):
        self.model: GradientBoostingRegressor | None = None
        self.target_col: str = ""
        self.date_col: str = ""
        self.trained_df: pd.DataFrame | None = None
        self.feature_cols: list[str] = []
        self.mae: float = 0.0
        self.r2: float = 0.0
        self.is_fitted: bool = False

    def fit(self, df: pd.DataFrame, target_col: str, date_col: str | None = None) -> dict:
        """
        Train the forecasting model.
        Returns training metrics.
        """
        self.target_col = target_col

        # Auto-detect date column if not provided
        if date_col is None:
            date_col = detect_time_column(df)

        if date_col is None:
            raise ValueError(
                "No date column found. Please ensure your dataset has a date/time column."
            )

        self.date_col = date_col

        # Aggregate to monthly level (handles daily data cleanly)
        try:
            agg_df = aggregate_by_time(df, date_col, target_col, freq="ME")
        except Exception:
            # Fallback: just sort by date without aggregating
            agg_df = df[[date_col, target_col]].copy()
            agg_df[date_col] = pd.to_datetime(agg_df[date_col], errors="coerce")
            agg_df = agg_df.dropna().sort_values(date_col).reset_index(drop=True)

        if len(agg_df) < 4:
            raise ValueError(
                f"Need at least 4 data points to forecast. Found only {len(agg_df)}."
            )

        # Feature engineering
        agg_df = create_time_features(agg_df, date_col)
        agg_df = add_lag_features(agg_df, target_col)

        # Drop rows with NaN from lag features
        agg_df = agg_df.dropna()

        # Get available feature columns
        self.feature_cols = [c for c in TIME_FEATURE_COLS if c in agg_df.columns]
        self.trained_df = agg_df

        X = agg_df[self.feature_cols].values
        y = agg_df[target_col].values

        # Train/test split (80/20, no shuffle — time series)
        split = max(1, int(len(X) * 0.8))
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        # Train GradientBoosting
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=3,
            subsample=0.8,
            random_state=42,
        )
        self.model.fit(X_train, y_train)

        # Evaluate
        if len(X_test) > 0:
            y_pred = self.model.predict(X_test)
            self.mae = float(mean_absolute_error(y_test, y_pred))
            self.r2 = float(r2_score(y_test, y_pred)) if len(y_test) > 1 else 0.0
        else:
            # All data used for training
            y_pred_train = self.model.predict(X_train)
            self.mae = float(mean_absolute_error(y_train, y_pred_train))
            self.r2 = float(r2_score(y_train, y_pred_train)) if len(y_train) > 1 else 0.0

        self.is_fitted = True
        logger.info(f"Forecast model trained: target={target_col} MAE={self.mae:.2f} R²={self.r2:.3f}")

        return {
            "target_column": target_col,
            "date_column": date_col,
            "training_rows": len(agg_df),
            "mae": round(self.mae, 2),
            "r2_score": round(self.r2, 3),
        }

    def predict(self, n_periods: int = 3) -> dict:
        """
        Predict next n_periods time steps.
        Uses bootstrap resampling (50 iterations) for confidence intervals.
        """
        if not self.is_fitted or self.trained_df is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        df = self.trained_df.copy()
        last_date = pd.to_datetime(df[self.date_col].iloc[-1])

        # Generate future dates (monthly)
        future_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=n_periods,
            freq="ME",
        )

        # Build future feature rows
        future_rows = []
        last_values = df[self.target_col].tail(7).tolist()

        for i, future_date in enumerate(future_dates):
            row = {
                "_time_index":   len(df) + i,
                "_month":        future_date.month,
                "_quarter":      future_date.quarter,
                "_day_of_week":  future_date.dayofweek,
                "_day_of_year":  future_date.dayofyear,
                "_year":         future_date.year,
                "_lag_1":        last_values[-1] if len(last_values) >= 1 else 0,
                "_lag_2":        last_values[-2] if len(last_values) >= 2 else 0,
                "_lag_3":        last_values[-3] if len(last_values) >= 3 else 0,
                "_rolling_mean_3": np.mean(last_values[-3:]) if len(last_values) >= 3 else np.mean(last_values),
                "_rolling_mean_7": np.mean(last_values[-7:]) if len(last_values) >= 7 else np.mean(last_values),
            }
            available_features = {k: v for k, v in row.items() if k in self.feature_cols}
            feature_vector = [available_features.get(f, 0) for f in self.feature_cols]
            prediction = float(self.model.predict([feature_vector])[0])
            prediction = max(0, prediction)  # no negative predictions
            future_rows.append({"date": future_date, "prediction": prediction})
            last_values.append(prediction)

        # Bootstrap confidence intervals
        n_bootstrap = 50
        bootstrap_preds = np.zeros((n_bootstrap, n_periods))

        X_train = df[self.feature_cols].values
        y_train = df[self.target_col].values

        for b in range(n_bootstrap):
            idx = np.random.choice(len(X_train), size=len(X_train), replace=True)
            boot_model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.05,
                max_depth=3,
                random_state=b,
            )
            boot_model.fit(X_train[idx], y_train[idx])
            for i, row in enumerate(future_rows):
                fv = [
                    df["_time_index"].iloc[-1] + i + 1,
                    row["date"].month,
                    row["date"].quarter,
                    row["date"].dayofweek,
                    row["date"].dayofyear,
                    row["date"].year,
                    last_values[-(i + 1)] if len(last_values) > i else 0,
                    last_values[-(i + 2)] if len(last_values) > i + 1 else 0,
                    last_values[-(i + 3)] if len(last_values) > i + 2 else 0,
                    np.mean(last_values[max(0, -(i + 3)):]) if last_values else 0,
                    np.mean(last_values[max(0, -(i + 7)):]) if last_values else 0,
                ]
                fv_filtered = [fv[j] for j, c in enumerate(self.feature_cols) if c in [
                    "_time_index", "_month", "_quarter", "_day_of_week",
                    "_day_of_year", "_year", "_lag_1", "_lag_2", "_lag_3",
                    "_rolling_mean_3", "_rolling_mean_7",
                ][:len(self.feature_cols)]]
                bootstrap_preds[b, i] = max(0, boot_model.predict([self.feature_cols and fv_filtered or [0]])[0])

        lower_ci = np.percentile(bootstrap_preds, 10, axis=0)
        upper_ci = np.percentile(bootstrap_preds, 90, axis=0)

        return {
            "dates":       [str(r["date"].date()) for r in future_rows],
            "predictions": [round(r["prediction"], 2) for r in future_rows],
            "lower_ci":    [round(max(0, v), 2) for v in lower_ci],
            "upper_ci":    [round(v, 2) for v in upper_ci],
            "mae":         round(self.mae, 2),
            "r2_score":    round(self.r2, 3),
        }

    def get_chart(self, prediction_result: dict) -> str:
        """
        Build forecast chart:
        - Blue line: actual historical values
        - Red dotted line: predictions
        - Shaded band: confidence interval
        """
        if self.trained_df is None:
            return "{}"

        df = self.trained_df
        hist_dates  = pd.to_datetime(df[self.date_col]).dt.strftime("%Y-%m-%d").tolist()
        hist_values = df[self.target_col].tolist()

        pred_dates  = prediction_result["dates"]
        pred_values = prediction_result["predictions"]
        lower_ci    = prediction_result["lower_ci"]
        upper_ci    = prediction_result["upper_ci"]

        fig = go.Figure()

        # Historical line
        fig.add_trace(go.Scatter(
            x=hist_dates, y=hist_values,
            mode="lines+markers",
            name="Historical",
            line=dict(color="#4361ee", width=2.5),
            marker=dict(size=5),
        ))

        # Confidence band (shaded area)
        fig.add_trace(go.Scatter(
            x=pred_dates + pred_dates[::-1],
            y=upper_ci + lower_ci[::-1],
            fill="toself",
            fillcolor="rgba(231, 76, 60, 0.15)",
            line=dict(color="rgba(231,76,60,0)"),
            name="80% Confidence Interval",
            hoverinfo="skip",
        ))

        # Forecast line (dotted)
        fig.add_trace(go.Scatter(
            x=pred_dates, y=pred_values,
            mode="lines+markers",
            name="Forecast",
            line=dict(color="#e74c3c", width=2.5, dash="dot"),
            marker=dict(size=8, symbol="diamond"),
        ))

        fig.update_layout(
            title=f"{self.target_col} Forecast — Next {len(pred_dates)} Periods",
            xaxis_title="Date",
            yaxis_title=self.target_col,
            template="plotly_white",
            font=dict(family="Inter, Arial, sans-serif", size=13),
            margin=dict(t=60, l=60, r=20, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            hovermode="x unified",
        )

        return fig.to_json()