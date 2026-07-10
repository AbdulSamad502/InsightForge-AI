import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json


def make_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    color_col: str | None = None,
) -> str:
    """
    Line chart — best for trends over time or ordered categories.
    Returns Plotly JSON string.
    """
    # Sort by x axis for clean lines
    try:
        plot_df = df[[x_col, y_col] + ([color_col] if color_col else [])].copy()
        plot_df = plot_df.dropna(subset=[x_col, y_col])

        # Try to parse as datetime for proper time axis
        try:
            plot_df[x_col] = pd.to_datetime(plot_df[x_col])
            plot_df = plot_df.sort_values(x_col)
        except (ValueError, TypeError):
            plot_df = plot_df.sort_values(x_col)

        fig = px.line(
            plot_df,
            x=x_col,
            y=y_col,
            color=color_col,
            title=title or f"{y_col} over {x_col}",
            markers=True,
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
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
        ),
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
    )
    fig.update_traces(
        line=dict(width=2.5),
        marker=dict(size=6),
    )
    return fig
