import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import APIClient
from components.metric_cards import render_kpi_row

st.set_page_config(page_title="Dashboard", page_icon="📈", layout="wide")

# ── Auth guard ─────────────────────────────────────────────
if not st.session_state.get("token"):
    st.warning("Please login first.")
    st.stop()

client = APIClient()

st.title("📈 Dashboard")
st.markdown("Your business data at a glance.")
st.divider()

# Load dashboard data
with st.spinner("Loading dashboard..."):
    summary, status = client.get_dashboard_summary()

if status != 200:
    st.error("Could not load dashboard data. Please try refreshing.")
    st.stop()

kpis = summary.get("kpis", {})

# ── KPI CARDS ──────────────────────────────────────────────
render_kpi_row(kpis)
st.divider()

# ── RECENT ACTIVITY COLUMNS ────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    # Recent Datasets
    st.subheader("📁 Recent Uploads")
    recent_datasets = summary.get("recent_datasets", [])
    if recent_datasets:
        for ds in recent_datasets:
            with st.container():
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(f"**{ds['filename']}**")
                c2.markdown(f"`{ds.get('row_count', 0):,}` rows")
                c3.markdown(f"`{ds['status']}`")
    else:
        st.info("No datasets uploaded yet.")
        if st.button("Upload your first dataset →"):
            st.switch_page("pages/1_Upload.py")

    st.divider()

    # Recent Chat Sessions
    st.subheader("💬 Recent Chats")
    recent_sessions = summary.get("recent_sessions", [])
    if recent_sessions:
        for sess in recent_sessions:
            title = sess.get("title", "Untitled Chat")
            if len(title) > 60:
                title = title[:60] + "..."
            if st.button(f"💬 {title}", key=f"dash_sess_{sess['id']}", use_container_width=True):
                st.session_state["current_session_id"] = sess["id"]
                st.switch_page("pages/2_Chat.py")
    else:
        st.info("No chat sessions yet.")
        if st.button("Start your first chat →"):
            st.switch_page("pages/2_Chat.py")

with col_right:
    # Recent Reports
    st.subheader("📄 Recent Reports")
    recent_reports = summary.get("recent_reports", [])
    if recent_reports:
        for rep in recent_reports:
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.markdown(f"Report `{rep['id'][:8]}...`")

            # Status badge
            status_colors = {
                "complete": "🟢",
                "pending":  "🟡",
                "running":  "🔵",
                "failed":   "🔴",
            }
            badge = status_colors.get(rep["status"], "⚪")
            c2.markdown(f"{badge} {rep['status'].title()}")

            if rep["status"] == "complete":
                if c3.button("⬇", key=f"dash_dl_{rep['id']}", help="Download"):
                    pdf_bytes = client.download_report(rep["id"])
                    if pdf_bytes:
                        st.download_button(
                            "Download PDF",
                            data=pdf_bytes,
                            file_name=f"report_{rep['id'][:8]}.pdf",
                            mime="application/pdf",
                            key=f"dl_{rep['id']}",
                        )
    else:
        st.info("No reports generated yet.")
        if st.button("Generate your first report →"):
            st.switch_page("pages/4_Reports.py")

    st.divider()

    # Recent ML Runs
    st.subheader("🤖 Recent ML Models")
    recent_ml = summary.get("recent_ml_results", [])
    if recent_ml:
        for ml in recent_ml:
            icons = {"forecast": "📈", "anomaly": "🔍", "churn": "⚠️"}
            icon = icons.get(ml["model_type"], "🤖")
            st.markdown(
                f"{icon} **{ml['model_type'].title()}** on `{ml['target_column']}`"
            )
    else:
        st.info("No ML models run yet.")

st.divider()

# ── QUICK ACTIONS ──────────────────────────────────────────
st.subheader("⚡ Quick Actions")
q1, q2, q3, q4 = st.columns(4)

with q1:
    if st.button("📁 Upload Data", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Upload.py")
with q2:
    if st.button("💬 Ask AI", use_container_width=True):
        st.switch_page("pages/2_Chat.py")
with q3:
    if st.button("📄 Generate Report", use_container_width=True):
        st.switch_page("pages/4_Reports.py")
with q4:
    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.rerun()