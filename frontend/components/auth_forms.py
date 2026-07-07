import streamlit as st
# from frontend.utils.api_client import APIClient
from utils.api_client import APIClient


def show_login_form():
    st.subheader("Login")
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)

    if submitted:
        if not email or not password:
            st.error("Please fill in all fields.")
            return

        client = APIClient()
        with st.spinner("Logging in..."):
            data, status = client.login(email, password)

        if status == 200:
            st.session_state["token"] = data["access_token"]
            st.session_state["user"] = data["user"]
            st.success(f"Welcome back, {data['user']['full_name']}!")
            st.rerun()
        else:
            st.error(data.get("message", "Login failed. Please check your credentials."))


def show_register_form():
    st.subheader("Create Account")
    with st.form("register_form"):
        full_name = st.text_input("Full Name", placeholder="Abdul Samad")
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", help="Minimum 6 characters")
        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        if not full_name or not email or not password:
            st.error("Please fill in all fields.")
            return

        client = APIClient()
        with st.spinner("Creating account..."):
            data, status = client.register(email, full_name, password)

        if status == 201:
            st.session_state["token"] = data["access_token"]
            st.session_state["user"] = data["user"]
            st.success(f"Account created! Welcome, {data['user']['full_name']}!")
            st.rerun()
        elif status == 409:
            st.error("An account with this email already exists. Please login instead.")
        else:
            st.error(data.get("message", "Registration failed. Please try again."))