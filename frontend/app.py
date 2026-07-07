import streamlit as st
import sys
import os

# Make sure imports work from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from components.auth_forms import show_login_form, show_register_form

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Initialize session state ───────────────────────────────
if "token" not in st.session_state:
    st.session_state["token"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None


def show_auth_page():
    """Show login/register when not authenticated."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.title("📊 AI Data Analyst")
        st.markdown("#### Your AI-powered Business Intelligence Platform")
        st.divider()

        tab1, tab2 = st.tabs(["Login", "Create Account"])
        with tab1:
            show_login_form()
        with tab2:
            show_register_form()


def show_main_app():
    """Show main app when authenticated."""
    user = st.session_state["user"]

    # ── Sidebar ────────────────────────────────────────────
    with st.sidebar:
        st.title("📊 AI Data Analyst")
        st.divider()

        st.markdown(f"**{user['full_name']}**")
        st.caption(user['email'])
        st.divider()

        st.markdown("### Navigation")
        st.page_link("pages/1_Upload.py",    label="📁 Upload Data")
        st.page_link("pages/2_Chat.py",      label="💬 AI Chat")
        st.page_link("pages/3_Dashboard.py", label="📈 Dashboard")
        st.page_link("pages/4_Reports.py",   label="📄 Reports")

        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # ── Main content ───────────────────────────────────────
    st.title(f"Welcome, {user['full_name']}! 👋")
    st.markdown("#### What would you like to do today?")
    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### 📁 Upload Data")
        st.markdown("Upload your CSV or Excel files to get started.")
        if st.button("Upload Dataset", use_container_width=True):
            st.switch_page("pages/1_Upload.py")

    with col2:
        st.markdown("### 💬 AI Chat")
        st.markdown("Ask questions about your data in plain English.")
        if st.button("Start Chatting", use_container_width=True):
            st.switch_page("pages/2_Chat.py")

    with col3:
        st.markdown("### 📈 Dashboard")
        st.markdown("View KPIs, trends, and recent activity.")
        if st.button("View Dashboard", use_container_width=True):
            st.switch_page("pages/3_Dashboard.py")

    with col4:
        st.markdown("### 📄 Reports")
        st.markdown("Generate and download professional PDF reports.")
        if st.button("Generate Report", use_container_width=True):
            st.switch_page("pages/4_Reports.py")


# ── Main router ────────────────────────────────────────────
if st.session_state["token"] is None:
    show_auth_page()
else:
    show_main_app()