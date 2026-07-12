import streamlit as st


def render_metric_card(label: str, value: str | int, icon: str, delta: str = "") -> None:
    """Render a single KPI metric card."""
    with st.container():
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                color: white;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            ">
                <div style="font-size: 28px; margin-bottom: 4px;">{icon}</div>
                <div style="font-size: 28px; font-weight: bold; margin-bottom: 4px;">
                    {value}
                </div>
                <div style="font-size: 13px; opacity: 0.9;">{label}</div>
                {f'<div style="font-size: 11px; opacity: 0.7; margin-top: 4px;">{delta}</div>' if delta else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_kpi_row(kpis: dict) -> None:
    """Render 5 KPI cards in a row."""
    col1, col2, col3, col4, col5 = st.columns(5)

    cards = [
        (col1, "Datasets",  kpis.get("total_datasets", 0),  "📁", ""),
        (col2, "Chats",     kpis.get("total_chats", 0),     "💬", ""),
        (col3, "Questions", kpis.get("total_messages", 0),  "❓", ""),
        (col4, "Reports",   kpis.get("total_reports", 0),   "📄", ""),
        (col5, "ML Models", kpis.get("total_ml_runs", 0),   "🤖", ""),
    ]

    for col, label, value, icon, delta in cards:
        with col:
            render_metric_card(label, value, icon, delta)