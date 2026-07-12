import streamlit as st
import time
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import APIClient

st.set_page_config(page_title="Reports", page_icon="📄", layout="wide")

# ── Auth guard ─────────────────────────────────────────────
if not st.session_state.get("token"):
    st.warning("Please login first.")
    st.stop()

client = APIClient()

st.title("📄 Reports")
st.markdown("Generate professional PDF reports from your AI analysis.")
st.divider()

# ════════════════════════════════════════════════════════════
# SECTION 1 — GENERATE NEW REPORT
# ════════════════════════════════════════════════════════════

st.subheader("🆕 Generate New Report")

datasets_data, ds_status = client.list_datasets()

if ds_status != 200 or not datasets_data:
    st.warning("No datasets found. Upload a dataset first.")
    if st.button("Go to Upload"):
        st.switch_page("pages/1_Upload.py")
    st.stop()

dataset_options = {ds["original_filename"]: ds["id"] for ds in datasets_data}

col1, col2 = st.columns([3, 1])
with col1:
    selected_name = st.selectbox(
        "Select dataset for report",
        options=list(dataset_options.keys()),
    )
    selected_id = dataset_options[selected_name]
    st.caption(
        "The report will include: all AI insights from your chats, "
        "charts, ML results, and executive summary."
    )
with col2:
    st.markdown("&nbsp;")  # spacer
    generate_btn = st.button(
        "📄 Generate Report",
        type="primary",
        use_container_width=True,
    )

if generate_btn:
    with st.spinner("Starting report generation..."):
        task_data, task_status = client.generate_report(selected_id)

    if task_status == 202:
        report_id = task_data["report_id"]
        st.session_state["active_report_id"] = report_id
        st.success(f"Report generation started! Report ID: `{report_id[:8]}...`")
        st.rerun()
    else:
        st.error(f"Failed to start report: {task_data.get('message', 'Unknown error')}")

# ── Polling for active report ──────────────────────────────
if "active_report_id" in st.session_state:
    report_id = st.session_state["active_report_id"]

    with st.container():
        st.info(f"⏳ Generating report `{report_id[:8]}...` — this takes 30-60 seconds")

        poll_placeholder = st.empty()
        for attempt in range(40):
            result, poll_status = client.get_report_status(report_id)
            current_status = result.get("status", "pending")

            status_messages = {
                "pending": "⏳ Queued...",
                "running": "🔄 Building your report (gathering insights, generating charts, writing summary)...",
                "complete": "✅ Report ready!",
                "failed":   "❌ Report generation failed.",
            }
            poll_placeholder.markdown(status_messages.get(current_status, "Working..."))

            if current_status == "complete":
                st.success("✅ Your report is ready!")
                del st.session_state["active_report_id"]

                pdf_bytes = client.download_report(report_id)
                if pdf_bytes:
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"business_report_{report_id[:8]}.pdf",
                        mime="application/pdf",
                        type="primary",
                    )
                st.rerun()
                break

            elif current_status == "failed":
                error = result.get("error_message", "Unknown error")
                st.error(f"Report failed: {error}")
                del st.session_state["active_report_id"]
                break

            time.sleep(3)
        else:
            poll_placeholder.warning(
                "Report is taking longer than expected. "
                "Check the list below for status updates."
            )

st.divider()

# ════════════════════════════════════════════════════════════
# SECTION 2 — ALL REPORTS LIST
# ════════════════════════════════════════════════════════════

st.subheader("📋 All Reports")

reports_data, rep_status = client.list_reports()

if rep_status != 200 or not reports_data:
    st.info("No reports generated yet. Click 'Generate Report' above to create your first one.")
else:
    for rep in reports_data:
        with st.container():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])

            # Report ID
            c1.markdown(f"**Report** `{rep['id'][:12]}...`")

            # Status with badge
            status_icons = {
                "complete": "🟢 Complete",
                "pending":  "🟡 Pending",
                "running":  "🔵 Generating...",
                "failed":   "🔴 Failed",
            }
            c2.markdown(status_icons.get(rep["status"], rep["status"]))

            # Date
            created = rep.get("created_at", "")[:10]
            c3.markdown(f"📅 {created}")

            # Download button
            if rep["status"] == "complete":
                if c4.button("⬇️ Download", key=f"dl_{rep['id']}", use_container_width=True):
                    pdf_bytes = client.download_report(rep["id"])
                    if pdf_bytes:
                        st.download_button(
                            label="Save PDF",
                            data=pdf_bytes,
                            file_name=f"report_{rep['id'][:8]}.pdf",
                            mime="application/pdf",
                            key=f"save_{rep['id']}",
                        )
                    else:
                        st.error("Download failed.")
            elif rep["status"] == "failed":
                error = rep.get("error_message", "")
                c4.markdown(f"<small style='color:red'>{error[:40]}</small>", unsafe_allow_html=True)

        st.markdown("---")