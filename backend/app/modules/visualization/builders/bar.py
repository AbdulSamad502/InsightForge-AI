import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json


def make_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    horizontal: bool = False,
    color_col: str | None = None,
    top_n: int | None = None,
) -> str:
    """
    Bar chart — best for comparing categories.
    horizontal=True makes it easier to read long category names.
    top_n limits to top N values by y_col.
    Returns Plotly JSON string.
    """
    try:
        plot_df = df[[x_col, y_col] + ([color_col] if color_col else [])].copy()
        plot_df = plot_df.dropna(subset=[x_col, y_col])

        # Aggregate if x_col is categorical
        if plot_df[x_col].dtype == object or str(plot_df[x_col].dtype) == "category":
            plot_df = (
                plot_df.groupby(x_col)[y_col]
                .sum()
                .reset_index()
                .sort_values(y_col, ascending=False)
            )

        # Limit to top N
        if top_n and len(plot_df) > top_n:
            plot_df = plot_df.head(top_n)

        # Use horizontal for long labels
        if horizontal or (len(plot_df) > 8):
            fig = px.bar(
                plot_df,
                x=y_col,
                y=x_col,
                orientation="h",
                title=title or f"{y_col} by {x_col}",
                color=color_col,
                color_continuous_scale="Blues",
            )
        else:
            fig = px.bar(
                plot_df,
                x=x_col,
                y=y_col,
                title=title or f"{y_col} by {x_col}",
                color=color_col,
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
        margin=dict(t=60, l=100, r=20, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
    )
    fig.update_traces(
        marker_color="#4361ee",
        marker_line_color="#3a56d4",
        marker_line_width=0.5,
    )
    return fig
