import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import APIClient
from components.chat_message import render_message

st.set_page_config(page_title="AI Chat", page_icon="💬", layout="wide")

# ── Auth guard ─────────────────────────────────────────────
if not st.session_state.get("token"):
    st.warning("Please login first.")
    st.stop()

client = APIClient()

# ── Page header ────────────────────────────────────────────
st.title("💬 AI Data Analyst Chat")
st.markdown("Ask any question about your data in plain English.")
st.divider()

# ════════════════════════════════════════════════════════════
# SECTION 1 — DATASET + SESSION SELECTOR
# ════════════════════════════════════════════════════════════

col_left, col_right = st.columns([2, 1])

with col_left:
    # Load datasets
    datasets_data, ds_status = client.list_datasets()

    if ds_status != 200 or not datasets_data:
        st.warning("No datasets found. Please upload a dataset first.")
        if st.button("Go to Upload"):
            st.switch_page("pages/1_Upload.py")
        st.stop()

    # Dataset selector
    dataset_options = {
        ds["original_filename"]: ds["id"] for ds in datasets_data
    }

    # Pre-select from session state if set on upload page
    default_name = st.session_state.get("current_dataset_name", list(dataset_options.keys())[0])
    default_idx = list(dataset_options.keys()).index(default_name) if default_name in dataset_options else 0

    selected_dataset_name = st.selectbox(
        "Select Dataset",
        options=list(dataset_options.keys()),
        index=default_idx,
    )
    selected_dataset_id = dataset_options[selected_dataset_name]

with col_right:
    if st.button("🆕 New Chat", use_container_width=True, type="primary"):
        with st.spinner("Creating new session..."):
            session_data, status = client.create_session(selected_dataset_id)
        if status == 201:
            st.session_state["current_session_id"] = session_data["id"]
            st.session_state["chat_messages"] = []
            st.rerun()
        else:
            st.error("Could not create chat session.")

# ── Initialize session if none exists ─────────────────────
if "current_session_id" not in st.session_state:
    with st.spinner("Starting your chat session..."):
        session_data, status = client.create_session(selected_dataset_id)
    if status == 201:
        st.session_state["current_session_id"] = session_data["id"]
        st.session_state["chat_messages"] = []
    else:
        st.error("Could not create chat session. Check your backend.")
        st.stop()

# Load existing messages if session changed
# if "chat_messages" not in st.session_state:
#     session_data, status = client.get_session(st.session_state["current_session_id"])
#     if status == 200:
#         st.session_state["chat_messages"] = session_data.get("messages", [])
#     else:
#         st.session_state["chat_messages"] = []
session_data, status = client.get_session(
    st.session_state["current_session_id"]
)

# if status == 200:
#     st.session_state["chat_messages"] = session_data.get("messages", [])
# else:
#     st.session_state["chat_messages"] = []
if "chat_messages" not in st.session_state:
    session_data, status = client.get_session(
        st.session_state["current_session_id"]
    )

    if status == 200:
        st.session_state["chat_messages"] = session_data.get("messages", [])
    else:
        st.session_state["chat_messages"] = []
st.divider()

# ════════════════════════════════════════════════════════════
# SECTION 2 — SUGGESTION CHIPS
# ════════════════════════════════════════════════════════════

suggestions = st.session_state.get("suggestions", [])
if suggestions:
    st.markdown("**💡 Suggested Questions:**")
    chip_cols = st.columns(min(len(suggestions), 3))
    for i, question in enumerate(suggestions):
        col_idx = i % 3
        with chip_cols[col_idx]:
            if st.button(question, key=f"chip_{i}", use_container_width=True):
                st.session_state["prefill_question"] = question

st.divider()

# ════════════════════════════════════════════════════════════
# SECTION 3 — CHAT HISTORY
# ════════════════════════════════════════════════════════════

# Render all existing messages
for message in st.session_state.get("chat_messages", []):
    render_message(message, client=client)
# ════════════════════════════════════════════════════════════
# SECTION 3.5 — ML MODELS PANEL
# ════════════════════════════════════════════════════════════

with st.expander("🤖 Run ML Models", expanded=False):
    st.markdown("Train and run machine learning models on your dataset.")

    dataset_id = st.session_state.get("current_dataset_id", "")

    if not dataset_id:
        st.warning("Upload and select a dataset first.")
    else:
        ml_col1, ml_col2, ml_col3 = st.columns(3)

        with ml_col1:
            st.markdown("**📈 Forecast**")
            forecast_col = st.text_input(
                "Target column",
                placeholder="e.g. revenue",
                key="forecast_col",
            )
            n_periods = st.slider("Periods to forecast", 1, 12, 3, key="n_periods")
            if st.button("Run Forecast", use_container_width=True, key="btn_forecast"):
                if forecast_col:
                    with st.spinner("Starting forecast model..."):
                        task_data, status = client.run_forecast(
                            dataset_id, forecast_col, n_periods
                        )
                    if status == 202:
                        st.session_state["active_ml_task"] = task_data["task_id"]
                        st.session_state["active_ml_type"] = "forecast"
                        st.rerun()
                    else:
                        st.error(task_data.get("message", "Failed to start forecast."))
                else:
                    st.warning("Enter a column name first.")

        with ml_col2:
            st.markdown("**🔍 Anomaly Detection**")
            anomaly_col = st.text_input(
                "Target column",
                placeholder="e.g. revenue",
                key="anomaly_col",
            )
            if st.button("Detect Anomalies", use_container_width=True, key="btn_anomaly"):
                if anomaly_col:
                    with st.spinner("Starting anomaly detection..."):
                        task_data, status = client.run_anomaly(dataset_id, anomaly_col)
                    if status == 202:
                        st.session_state["active_ml_task"] = task_data["task_id"]
                        st.session_state["active_ml_type"] = "anomaly"
                        st.rerun()
                    else:
                        st.error(task_data.get("message", "Failed to start anomaly detection."))
                else:
                    st.warning("Enter a column name first.")

        with ml_col3:
            st.markdown("**⚠️ Churn Prediction**")
            churn_col = st.text_input(
                "Churn column",
                placeholder="e.g. churned",
                key="churn_col",
            )
            if st.button("Predict Churn", use_container_width=True, key="btn_churn"):
                if churn_col:
                    with st.spinner("Starting churn model..."):
                        task_data, status = client.run_churn(dataset_id, churn_col)
                    if status == 202:
                        st.session_state["active_ml_task"] = task_data["task_id"]
                        st.session_state["active_ml_type"] = "churn"
                        st.rerun()
                    else:
                        st.error(task_data.get("message", "Failed to start churn model."))
                else:
                    st.warning("Enter a column name first.")

# ── ML result polling ──────────────────────────────────────
if "active_ml_task" in st.session_state:
    task_id = st.session_state["active_ml_task"]
    ml_type = st.session_state.get("active_ml_type", "ML")

    # Poll placeholder
    poll_placeholder = st.empty()

    with poll_placeholder.container():
        with st.spinner(f"⏳ Running {ml_type} model... (this takes 10-30 seconds)"):
            import time
            max_polls = 30
            for _ in range(max_polls):
                result_data, result_status = client.get_ml_result(task_id)
                status = result_data.get("status", "pending")

                if status == "complete":
                    poll_placeholder.empty()

                    # Show result
                    st.success(f"✅ {ml_type.title()} model complete!")

                    data = result_data.get("result_data", {})
                    chart_data = result_data.get("chart_data")

                    # Render chart
                    if chart_data:
                        from components.chart_renderer import render_chart
                        render_chart(chart_data)

                    # Show summary
                    if ml_type == "forecast":
                        dates = data.get("dates", [])
                        preds = data.get("predictions", [])
                        lower = data.get("lower_ci", [])
                        upper = data.get("upper_ci", [])
                        mae = data.get("mae", 0)
                        r2 = data.get("r2_score", 0)

                        st.markdown(f"**Model accuracy:** MAE = {mae:,.0f} | R² = {r2:.3f}")
                        for d, p, l, u in zip(dates, preds, lower, upper):
                            st.markdown(
                                f"📅 **{d}**: `{p:,.0f}` "
                                f"*(confidence range: {l:,.0f} – {u:,.0f})*"
                            )

                    elif ml_type == "anomaly":
                        count = data.get("anomaly_count", 0)
                        total = data.get("total_count", 0)
                        pct = data.get("anomaly_pct", 0)
                        st.markdown(
                            f"**Found {count} anomalies** out of {total} data points "
                            f"({pct}% of data)"
                        )

                    elif ml_type == "churn":
                        accuracy = data.get("accuracy", 0)
                        fi = data.get("feature_importance", [])
                        at_risk = data.get("top_at_risk_customers", [])
                        high_risk = len([c for c in at_risk if c.get("risk_level") == "High"])
                        st.markdown(f"**Model accuracy: {accuracy:.1%}**")
                        st.markdown(f"**{high_risk} customers at HIGH churn risk**")
                        if fi:
                            st.markdown("**Top factors driving churn:**")
                            for f in fi[:3]:
                                st.markdown(f"- {f['feature']}: {f['importance']:.1%} importance")

                    # Clear the task
                    del st.session_state["active_ml_task"]
                    break

                elif status == "failed":
                    poll_placeholder.empty()
                    error = result_data.get("error_message", "Unknown error")
                    st.error(f"ML task failed: {error}")
                    del st.session_state["active_ml_task"]
                    break

                time.sleep(2)
            else:
                poll_placeholder.empty()
                st.warning("ML task is taking longer than expected. Check back in a moment.")
                del st.session_state["active_ml_task"]

# ════════════════════════════════════════════════════════════
# SECTION 4 — CHAT INPUT
# ════════════════════════════════════════════════════════════

# Check for prefilled question from suggestion chips or upload page
prefill = st.session_state.pop("prefill_question", "")

user_input = st.chat_input(
    placeholder="Ask anything about your data... e.g. What is total revenue by category?",
)

# Use prefill if no manual input
if prefill and not user_input:
    user_input = prefill

if user_input:
    # Show user message immediately
    # render_message({"role": "user", "content": user_input})
    # render_message(
    # {"role": "user", "content": user_input},
    # client=client
    # )

    # # Add to message history
    # st.session_state["chat_messages"].append({
    #     "role": "user",
    #     "content": user_input,
    # })

    # Call the API
    with st.spinner("🤔 Analyzing your data..."):
        response_data, status = client.send_message(
            st.session_state["current_session_id"],
            user_input,
        )

    if status == 200:

        assistant_message = response_data["message"]

        # Render assistant response
        # render_message(assistant_message)
        render_message(assistant_message, client=client)

        # Save to session state
        st.session_state["chat_messages"].append(assistant_message)

        # Rerun to update the full chat history display cleanly
        st.rerun()

    else:
        st.error(
            f"Error: {response_data.get('message', 'The AI agent encountered an error. Please try again.')}"
        )

# ════════════════════════════════════════════════════════════
# SECTION 5 — SIDEBAR: PAST SESSIONS
# ════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### 💬 Chat Sessions")
    sessions_data, sess_status = client.list_sessions()

    if sess_status == 200 and sessions_data:
        for sess in sessions_data[:10]:  # show last 10 sessions
            title = sess.get("title") or "Untitled Chat"
            if len(title) > 35:
                title = title[:35] + "..."

            if st.button(
                title,
                key=f"sess_{sess['id']}",
                use_container_width=True,
            ):
                # Load this session's messages
                loaded, load_status = client.get_session(sess["id"])
                if load_status == 200:
                    st.session_state["current_session_id"] = sess["id"]
                    st.session_state["chat_messages"] = loaded.get("messages", [])
                    st.rerun()
    else:
        st.caption("No previous sessions yet.")
