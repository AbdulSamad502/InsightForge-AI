import logging
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.ensemble import IsolationForest

from app.modules.ml.engines.preprocessor import detect_time_column

logger = logging.getLogger(__name__)


class AnomalyEngine:
    """
    Anomaly detection using IQR method + IsolationForest refinement.
    Works on any numeric column, with or without a time column.
    """

    def __init__(self):
        self.target_col: str = ""
        self.date_col: str | None = None
        self.result_df: pd.DataFrame | None = None
        self.anomaly_count: int = 0
        self.total_count: int = 0

    def fit_predict(self, df: pd.DataFrame, target_col: str) -> pd.DataFrame:
        """
        Detect anomalies using two-stage approach:
        Stage 1: IQR method flags extreme outliers
        Stage 2: IsolationForest refines detection
        Returns df with 'anomaly_score' and 'is_anomaly' columns.
        """
        self.target_col = target_col
        self.date_col = detect_time_column(df)

        work_df = df.copy()

        # Drop rows where target is null
        work_df = work_df.dropna(subset=[target_col]).reset_index(drop=True)
        self.total_count = len(work_df)

        if self.total_count < 5:
            raise ValueError(
                f"Need at least 5 data points for anomaly detection. Found {self.total_count}."
            )

        values = work_df[target_col].values.reshape(-1, 1)

        # Stage 1: IQR bounds
        Q1 = np.percentile(values, 25)
        Q3 = np.percentile(values, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 2.0 * IQR
        upper_bound = Q3 + 2.0 * IQR
        iqr_anomaly = (values.flatten() < lower_bound) | (values.flatten() > upper_bound)

        # Stage 2: IsolationForest
        contamination = min(0.15, max(0.05, iqr_anomaly.sum() / len(values)))
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        iso_scores = iso_forest.fit_predict(values)
        iso_anomaly = iso_scores == -1

        # Combine: anomaly if flagged by EITHER method
        is_anomaly = iqr_anomaly | iso_anomaly

        # Anomaly score: distance from mean in std units
        mean_val = float(np.mean(values))
        std_val  = float(np.std(values)) or 1.0
        anomaly_scores = np.abs((values.flatten() - mean_val) / std_val)

        work_df["anomaly_score"] = anomaly_scores.round(3)
        work_df["is_anomaly"]    = is_anomaly

        self.result_df   = work_df
        self.anomaly_count = int(is_anomaly.sum())

        logger.info(
            f"Anomaly detection complete: {self.anomaly_count}/{self.total_count} anomalies found"
        )
        return work_df

    def get_summary(self) -> dict:
        """Return a summary of anomaly detection results."""
        if self.result_df is None:
            return {}

        anomaly_rows = self.result_df[self.result_df["is_anomaly"] == True]
        anomaly_pct  = round(self.anomaly_count / max(self.total_count, 1) * 100, 1)

        # Most extreme anomalies
        top_anomalies = (
            anomaly_rows
            .nlargest(5, "anomaly_score")[[self.target_col, "anomaly_score"]]
            .to_dict(orient="records")
        )

        # Date info if available
        extreme_dates = []
        if self.date_col and self.date_col in anomaly_rows.columns:
            extreme_dates = anomaly_rows.nlargest(5, "anomaly_score")[self.date_col].astype(str).tolist()

        return {
            "anomaly_count":   self.anomaly_count,
            "total_count":     self.total_count,
            "anomaly_pct":     anomaly_pct,
            "top_anomalies":   top_anomalies,
            "extreme_dates":   extreme_dates,
            "target_column":   self.target_col,
        }

    def get_chart(self) -> str:
        """
        Time-series chart with normal points in blue,
        anomaly points highlighted as large red markers.
        """
        if self.result_df is None:
            return "{}"

        df = self.result_df
        normal   = df[df["is_anomaly"] == False]
        anomalies = df[df["is_anomaly"] == True]

        # X axis: use date column if available, otherwise index
        if self.date_col and self.date_col in df.columns:
            x_normal    = pd.to_datetime(normal[self.date_col]).dt.strftime("%Y-%m-%d")
            x_anomaly   = pd.to_datetime(anomalies[self.date_col]).dt.strftime("%Y-%m-%d")
            x_all       = pd.to_datetime(df[self.date_col]).dt.strftime("%Y-%m-%d")
            x_label     = self.date_col
        else:
            x_normal    = normal.index.tolist()
            x_anomaly   = anomalies.index.tolist()
            x_all       = df.index.tolist()
            x_label     = "Index"

        fig = go.Figure()

        # Normal points
        fig.add_trace(go.Scatter(
            x=x_all.tolist() if hasattr(x_all, "tolist") else list(x_all),
            y=df[self.target_col].tolist(),
            mode="lines+markers",
            name="Normal",
            line=dict(color="#4361ee", width=1.5),
            marker=dict(size=5, color="#4361ee"),
        ))

        # Anomaly points (large red markers on top)
        if len(anomalies) > 0:
            fig.add_trace(go.Scatter(
                x=x_anomaly.tolist() if hasattr(x_anomaly, "tolist") else list(x_anomaly),
                y=anomalies[self.target_col].tolist(),
                mode="markers",
                name="Anomaly",
                marker=dict(
                    size=14,
                    color="#e74c3c",
                    symbol="x",
                    line=dict(width=2, color="#c0392b"),
                ),
                hovertemplate=(
                    f"<b>ANOMALY</b><br>{x_label}: %{{x}}<br>"
                    f"{self.target_col}: %{{y:,.2f}}<extra></extra>"
                ),
            ))

        # Add threshold lines (IQR bounds)
        values = df[self.target_col].values
        Q1, Q3 = np.percentile(values, 25), np.percentile(values, 75)
        IQR = Q3 - Q1

        fig.add_hline(
            y=Q3 + 2.0 * IQR,
            line_dash="dash",
            line_color="#f39c12",
            annotation_text="Upper bound",
            annotation_position="right",
        )
        fig.add_hline(
            y=max(0, Q1 - 2.0 * IQR),
            line_dash="dash",
            line_color="#f39c12",
            annotation_text="Lower bound",
            annotation_position="right",
        )

        fig.update_layout(
            title=f"Anomaly Detection — {self.target_col} ({self.anomaly_count} anomalies found)",
            xaxis_title=x_label,
            yaxis_title=self.target_col,
            template="plotly_white",
            font=dict(family="Inter, Arial, sans-serif", size=13),
            margin=dict(t=60, l=60, r=80, b=40),
            hovermode="x unified",
        )

        return fig.to_json()