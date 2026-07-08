
import streamlit as st
from components.chart_renderer import render_chart


def render_message(message: dict) -> None:
    """
    Renders a single chat message (user or assistant).
    Assistant messages include: text + chart + insight + recommendation.
    """
    role = message.get("role", "user")
    content = message.get("content", "")
    chart_data = message.get("chart_data")
    insight = message.get("insight")
    recommendation = message.get("recommendation")

    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)

    else:  # assistant
        with st.chat_message("assistant", avatar="📊"):
            # Main text response
            st.markdown(content)

            # Chart (if present)
            if chart_data:
                render_chart(chart_data)

            # Insight box
            if insight:
                st.info(f"💡 **Business Insight**\n\n{insight}")

            # Recommendation box
            if recommendation:
                st.success(f"✅ **Recommendation**\n\n{recommendation}")
