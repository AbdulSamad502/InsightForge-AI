import logging
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)


class ChurnEngine:
    """
    Customer churn prediction using RandomForestClassifier.
    The target column should be a binary column (1=churned, 0=not churned)
    OR a categorical column like 'status' with 'churned'/'active' values.
    """

    def __init__(self):
        self.model: RandomForestClassifier | None = None
        self.target_col: str = ""
        self.feature_cols: list[str] = []
        self.feature_importances: dict = {}
        self.accuracy: float = 0.0
        self.label_encoders: dict[str, LabelEncoder] = {}
        self.is_fitted: bool = False
        self.class_names: list[str] = []

    def fit(self, df: pd.DataFrame, target_col: str) -> dict:
        """
        Train the churn prediction model.
        Automatically handles binary and categorical target columns.
        """
        self.target_col = target_col
        work_df = df.copy().dropna(subset=[target_col])

        if len(work_df) < 10:
            raise ValueError(
                f"Need at least 10 rows to train churn model. Found {len(work_df)}."
            )

        # Encode target column
        target_series = work_df[target_col]

        # Handle string targets ("churned"/"active", "yes"/"no", "True"/"False")
        if target_series.dtype == object or str(target_series.dtype) == "category":
            le_target = LabelEncoder()
            y = le_target.fit_transform(target_series.astype(str))
            self.class_names = list(le_target.classes_)
        else:
            y = target_series.values.astype(int)
            self.class_names = ["Not Churned", "Churned"]

        # Build feature set — all columns except target
        feature_df = work_df.drop(columns=[target_col])

        # Drop pure text columns (high cardinality)
        for col in feature_df.select_dtypes(include=["object"]).columns:
            if feature_df[col].nunique() > 50:
                feature_df = feature_df.drop(columns=[col])
            else:
                le = LabelEncoder()
                feature_df[col] = le.fit_transform(feature_df[col].astype(str))
                self.label_encoders[col] = le

        # Drop datetime columns
        for col in feature_df.select_dtypes(include=["datetime64"]).columns:
            feature_df = feature_df.drop(columns=[col])

        # Fill remaining nulls
        feature_df = feature_df.fillna(feature_df.median(numeric_only=True))

        self.feature_cols = list(feature_df.columns)
        X = feature_df.values

        if len(X[0]) == 0:
            raise ValueError("No suitable feature columns found for churn prediction.")

        # Train/test split
        if len(X) >= 20:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
        else:
            X_train, X_test, y_train, y_test = X, X, y, y

        # Train RandomForest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42,
            class_weight="balanced",  # handles imbalanced churn data
        )
        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        self.accuracy = float(accuracy_score(y_test, y_pred))

        # Feature importance
        importances = self.model.feature_importances_
        self.feature_importances = dict(
            sorted(
                zip(self.feature_cols, importances.tolist()),
                key=lambda x: x[1],
                reverse=True,
            )
        )

        self.is_fitted = True
        logger.info(
            f"Churn model trained: target={target_col} "
            f"accuracy={self.accuracy:.3f} features={len(self.feature_cols)}"
        )

        return {
            "target_column": target_col,
            "accuracy": round(self.accuracy, 3),
            "training_rows": len(X_train),
            "feature_count": len(self.feature_cols),
        }

    def predict_segments(self, df: pd.DataFrame) -> list[dict]:
        """
        Predict churn probability for each row.
        Returns list of {features, churn_probability, risk_level}.
        """
        if not self.is_fitted or self.model is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        work_df = df.copy()

        for col, le in self.label_encoders.items():
            if col in work_df.columns:
                work_df[col] = le.transform(
                    work_df[col].astype(str).map(
                        lambda x: x if x in le.classes_ else le.classes_[0]
                    )
                )

        # Keep only feature columns
        X = work_df[[c for c in self.feature_cols if c in work_df.columns]].fillna(0).values

        probabilities = self.model.predict_proba(X)
        churn_idx = 1 if probabilities.shape[1] > 1 else 0
        churn_probs = probabilities[:, churn_idx]

        results = []
        for i, prob in enumerate(churn_probs[:50]):  # limit to 50 for display
            risk = "High" if prob > 0.7 else "Medium" if prob > 0.4 else "Low"
            results.append({
                "row_index": i,
                "churn_probability": round(float(prob), 3),
                "risk_level": risk,
            })

        return sorted(results, key=lambda x: x["churn_probability"], reverse=True)

    def get_feature_importance(self) -> list[dict]:
        """Return top 5 features driving churn."""
        top_5 = list(self.feature_importances.items())[:5]
        return [
            {"feature": k, "importance": round(v, 4)}
            for k, v in top_5
        ]

    def get_chart(self) -> str:
        """
        Side-by-side charts:
        Left: Feature importance bar chart
        Right: Churn risk distribution (if predictions available)
        """
        if not self.is_fitted:
            return "{}"

        top_features = self.get_feature_importance()
        features = [f["feature"] for f in top_features]
        importances = [f["importance"] for f in top_features]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=importances,
            y=features,
            orientation="h",
            marker_color=["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db"],
            text=[f"{v:.1%}" for v in importances],
            textposition="outside",
        ))

        fig.update_layout(
            title=f"Top Factors Driving Churn — {self.target_col}",
            xaxis_title="Importance Score",
            yaxis_title="Feature",
            template="plotly_white",
            font=dict(family="Inter, Arial, sans-serif", size=13),
            margin=dict(t=60, l=150, r=60, b=40),
            xaxis=dict(range=[0, max(importances) * 1.3]),
            yaxis=dict(autorange="reversed"),
        )

        return fig.to_json()