import streamlit as st
import plotly.graph_objects as go
import json


def render_chart(chart_data: dict | str | None) -> None:
    """
    Renders a Plotly chart from JSON data.
    Handles both dict and JSON string formats.
    """
    if chart_data is None:
        return

    try:
        # Parse if it's a string
        if isinstance(chart_data, str):
            chart_data = json.loads(chart_data)
        # Remove unsupported Plotly template fields
        if "layout" in chart_data:
            template = chart_data.get("layout", {}).get("template", {})

            if isinstance(template, dict):
                data = template.get("data", {})

                if "heatmapgl" in data:
                    del data["heatmapgl"]
        fig = go.Figure(chart_data)
        fig.update_layout(
            height=400,
            margin=dict(t=40, l=20, r=20, b=20),
            template="plotly_white",

            # Make all chart text visible
            font=dict(
                color="#111827",
                size=14,
            ),

            title=dict(
                font=dict(
                    color="#000000",
                    size=18,
                )
            ),

            xaxis=dict(
                title_font=dict(color="#000000"),
                tickfont=dict(color="#000000"),
            ),

            yaxis=dict(
                title_font=dict(color="#000000"),
                tickfont=dict(color="#000000"),
            ),

            legend=dict(
                font=dict(
                    color="#000000"
                )
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.warning(f"Could not render chart: {e}")
