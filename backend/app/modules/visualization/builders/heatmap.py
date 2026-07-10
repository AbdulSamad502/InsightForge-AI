import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np


def make_heatmap(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    title: str = "",
) -> str:
    """
    Correlation heatmap — shows relationships between numeric columns.
    If columns is None, uses all numeric columns.
    Returns Plotly JSON string.
    """
    try:
        # Select numeric columns
        if columns:
            numeric_df = df[columns].select_dtypes(include=[np.number])
        else:
            numeric_df = df.select_dtypes(include=[np.number])

        if numeric_df.shape[1] < 2:
            return json.dumps({"error": "Need at least 2 numeric columns for a correlation heatmap."})

        # Compute correlation
        corr_matrix = numeric_df.corr().round(2)

        fig = px.imshow(
            corr_matrix,
            title=title or "Correlation Matrix",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            text_auto=True,
            aspect="auto",
        )

        fig.update_traces(
            hovertemplate="%{x} × %{y}<br>Correlation: %{z}<extra></extra>",
        )

        fig = _apply_theme(fig)
        return fig.to_json()

    except Exception as e:
        return json.dumps({"error": str(e)})


def _apply_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Inter, Arial, sans-serif", size=12),
        title_font=dict(size=16, color="#1a1a2e"),
        margin=dict(t=60, l=20, r=20, b=40),
    )
    return fig
