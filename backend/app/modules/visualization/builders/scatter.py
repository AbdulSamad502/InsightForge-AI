import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np


def make_scatter(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str | None = None,
    size_col: str | None = None,
    title: str = "",
    add_trendline: bool = True,
) -> str:
    """
    Scatter plot — best for showing relationships between two numeric variables.
    Optionally adds a trendline to show the direction of correlation.
    Returns Plotly JSON string.
    """
    try:
        cols = [x_col, y_col]
        if color_col and color_col in df.columns:
            cols.append(color_col)
        if size_col and size_col in df.columns:
            cols.append(size_col)

        plot_df = df[cols].dropna()

        # Limit to 500 points for performance
        if len(plot_df) > 500:
            plot_df = plot_df.sample(500, random_state=42)

        trendline = "ols" if add_trendline else None

        fig = px.scatter(
            plot_df,
            x=x_col,
            y=y_col,
            color=color_col,
            size=size_col,
            title=title or f"{x_col} vs {y_col}",
            trendline=trendline,
            opacity=0.7,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )

        # Add correlation annotation
        if pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_col]):
            corr = df[[x_col, y_col]].dropna().corr().iloc[0, 1]
            fig.add_annotation(
                text=f"Correlation: {corr:.3f}",
                xref="paper", yref="paper",
                x=0.02, y=0.98,
                showarrow=False,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#cccccc",
                font=dict(size=12),
            )

        fig = _apply_theme(fig)
        return fig.to_json()

    except Exception as e:
        return json.dumps({"error": str(e)})


def _apply_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Inter, Arial, sans-serif", size=13),
        title_font=dict(size=16, color="#1a1a2e"),
        margin=dict(t=60, l=40, r=20, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
    )
    return fig
