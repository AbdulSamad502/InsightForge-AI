import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json


def make_histogram(
    df: pd.DataFrame,
    col: str,
    bins: int = 20,
    title: str = "",
) -> str:
    """
    Histogram — shows distribution of a numeric column.
    Returns Plotly JSON string.
    """
    try:
        series = df[col].dropna()

        if series.empty:
            return json.dumps({"error": f"Column '{col}' has no data."})

        fig = px.histogram(
            df,
            x=col,
            nbins=bins,
            title=title or f"Distribution of {col}",
            marginal="box",  # adds a box plot on top — very informative
            color_discrete_sequence=["#4361ee"],
        )

        fig.update_traces(
            marker_line_color="white",
            marker_line_width=0.5,
            hovertemplate=f"{col}: %{{x}}<br>Count: %{{y}}<extra></extra>",
        )

        # Add mean line
        mean_val = series.mean()
        fig.add_vline(
            x=mean_val,
            line_dash="dash",
            line_color="#e63946",
            annotation_text=f"Mean: {mean_val:.1f}",
            annotation_position="top right",
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
        bargap=0.05,
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
        yaxis=dict(title="Count", showgrid=True, gridcolor="#f0f0f0"),
    )
    return fig
