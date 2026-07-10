import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json


def make_pie_chart(
    df: pd.DataFrame,
    labels_col: str,
    values_col: str,
    title: str = "",
    top_n: int = 8,
) -> str:
    """
    Pie chart — best for showing proportions/percentages.
    Automatically groups small slices into "Other" if more than top_n categories.
    Returns Plotly JSON string.
    """
    try:
        plot_df = df[[labels_col, values_col]].copy()
        plot_df = plot_df.dropna()

        # Aggregate
        plot_df = (
            plot_df.groupby(labels_col)[values_col]
            .sum()
            .reset_index()
            .sort_values(values_col, ascending=False)
        )

        # Group small slices
        if len(plot_df) > top_n:
            top = plot_df.head(top_n)
            other_val = plot_df.iloc[top_n:][values_col].sum()
            other_row = pd.DataFrame(
                [{labels_col: "Other", values_col: other_val}]
            )
            plot_df = pd.concat([top, other_row], ignore_index=True)

        fig = px.pie(
            plot_df,
            names=labels_col,
            values=values_col,
            title=title or f"{values_col} by {labels_col}",
            hole=0.35,  # donut style — more modern
            color_discrete_sequence=px.colors.qualitative.Set2,
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="%{label}<br>%{value:,.0f}<br>%{percent}<extra></extra>",
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
        margin=dict(t=60, l=20, r=20, b=40),
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5),
    )
    return fig
