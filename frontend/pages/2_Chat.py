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
if "chat_messages" not in st.session_state:
    session_data, status = client.get_session(st.session_state["current_session_id"])
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
    render_message(message)

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
    render_message({"role": "user", "content": user_input})

    # Add to message history
    st.session_state["chat_messages"].append({
        "role": "user",
        "content": user_input,
    })

    # Call the API
    with st.spinner("🤔 Analyzing your data..."):
        response_data, status = client.send_message(
            st.session_state["current_session_id"],
            user_input,
        )

    if status == 200:
        assistant_message = response_data["message"]

        # Render assistant response
        render_message(assistant_message)

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
