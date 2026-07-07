import httpx
import streamlit as st
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class APIClient:
    """
    All API calls in one place.
    Every method here maps 1:1 to a React fetch() call when we upgrade.
    """

    def __init__(self):
        self.base_url = BACKEND_URL
        self.token = st.session_state.get("token", None)

    def _headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def register(self, email: str, full_name: str, password: str) -> dict:
        response = httpx.post(
            f"{self.base_url}/api/v1/auth/register",
            json={"email": email, "full_name": full_name, "password": password},
            timeout=10,
        )
        return response.json(), response.status_code

    def login(self, email: str, password: str) -> dict:
        response = httpx.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        return response.json(), response.status_code

    def get_me(self) -> dict:
        response = httpx.get(
            f"{self.base_url}/api/v1/auth/me",
            headers=self._headers(),
            timeout=10,
        )
        return response.json(), response.status_code