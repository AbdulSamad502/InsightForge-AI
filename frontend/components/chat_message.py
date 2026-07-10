import streamlit as st
import json
from components.chart_renderer import render_chart


def render_message(message: dict, client=None) -> None:
    """
    Renders a single chat message (user or assistant).

    Assistant messages show:
    - Text response
    - Plotly chart (if present) + "Explain this chart" button
    - Business insight box
    - Recommendation box
    """
    role = message.get("role", "user")
    content = message.get("content", "")
    chart_data = message.get("chart_data")
    insight = message.get("insight")
    recommendation = message.get("recommendation")
    intent_type = message.get("intent_type", "")
    message_id = message.get("id", str(hash(content)))

    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)
        return

    # ── Assistant message ──────────────────────────────────
    with st.chat_message("assistant", avatar="📊"):

        # Main text response
        st.markdown(content)

        # Chart section
        if chart_data:
            render_chart(chart_data)

            # "Explain this chart" button
            explain_key = f"explain_{message_id}"
            explanation_key = f"explanation_{message_id}"

            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button(
                    "🔍 Explain this chart",
                    key=explain_key,
                    help="Get a plain-English explanation of what this chart shows",
                ):
                    if client:
                        # Extract chart metadata for the explain call
                        chart_type = "bar"
                        x_col = "category"
                        y_col = "value"
                        title = ""

                        try:
                            if isinstance(chart_data, dict):
                                # Try to extract from Plotly layout
                                layout = chart_data.get("layout", {})
                                title = layout.get("title", {})
                                if isinstance(title, dict):
                                    title = title.get("text", "")
                                elif isinstance(title, str):
                                    title = title
                                else:
                                    title = ""

                                # Determine chart type from data type
                                data_items = chart_data.get("data", [{}])
                                if data_items:
                                    trace_type = data_items[0].get("type", "bar")
                                    chart_type = trace_type

                        except Exception:
                            pass

                        # Build data summary from content
                        data_summary = content[:300] if content else "Chart data"

                        with st.spinner("Explaining chart..."):
                            explain_data, status = client.explain_chart(
                                chart_type=chart_type,
                                x_column=x_col,
                                y_column=y_col,
                                data_summary=data_summary,
                                title=str(title),
                            )

                        if status == 200:
                            st.session_state[explanation_key] = explain_data.get("explanation", "")
                        else:
                            st.session_state[explanation_key] = "Could not generate explanation."

            # Show explanation if it exists in session state
            if explanation_key in st.session_state and st.session_state[explanation_key]:
                st.markdown(
                    f"<div style='background:#f0f7ff; padding:12px; border-radius:8px; "
                    f"border-left:4px solid #4361ee; margin-top:8px; color:#111827;'>"
                    f"📖 <b>Chart Explanation</b><br>{st.session_state[explanation_key]}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # Business insight
        if insight:
            st.markdown(
                f"<div style='background:#f0fdf4; color:#111827; padding:12px; border-radius:8px; "
                f"border-left:4px solid #22c55e; margin-top:8px;'>"
                f"💡 <b>Business Insight</b><br>{insight}"
                f"</div>",
                unsafe_allow_html=True,
            )

        # Recommendation
        if recommendation:
            st.markdown(
                f"<div style='background:#fefce8; color:#111827; padding:12px; border-radius:8px; "
                f"border-left:4px solid #eab308; margin-top:8px;'>"
                f"✅ <b>Recommendation</b><br>{recommendation}"
                f"</div>",
                unsafe_allow_html=True,
            )

        # Intent badge (subtle, for portfolio demonstration)
        if intent_type and intent_type != "general":
            st.caption(f"🎯 Intent detected: `{intent_type}`")
