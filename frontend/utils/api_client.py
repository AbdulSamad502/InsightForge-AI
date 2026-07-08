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


        # ── Dataset methods ────────────────────────────────────

    def upload_dataset(self, file_bytes: bytes, filename: str) -> tuple[dict, int]:
        response = httpx.post(
            f"{self.base_url}/api/v1/datasets/upload",
            headers=self._headers(),
            files={"file": (filename, file_bytes, "multipart/form-data")},
            timeout=60,  # uploads can take time
        )
        return response.json(), response.status_code

    def list_datasets(self) -> tuple[list, int]:
        response = httpx.get(
            f"{self.base_url}/api/v1/datasets/",
            headers=self._headers(),
            timeout=10,
        )
        return response.json(), response.status_code

    def get_dataset(self, dataset_id: str) -> tuple[dict, int]:
        response = httpx.get(
            f"{self.base_url}/api/v1/datasets/{dataset_id}",
            headers=self._headers(),
            timeout=10,
        )
        return response.json(), response.status_code

    def get_preview(self, dataset_id: str) -> tuple[dict, int]:
        response = httpx.get(
            f"{self.base_url}/api/v1/datasets/{dataset_id}/preview",
            headers=self._headers(),
            timeout=15,
        )
        return response.json(), response.status_code

    def clean_dataset(self, dataset_id: str, config: dict) -> tuple[dict, int]:
        response = httpx.post(
            f"{self.base_url}/api/v1/datasets/{dataset_id}/clean",
            headers=self._headers(),
            json=config,
            timeout=30,
        )
        return response.json(), response.status_code

    def delete_dataset(self, dataset_id: str) -> int:
        response = httpx.delete(
            f"{self.base_url}/api/v1/datasets/{dataset_id}",
            headers=self._headers(),
            timeout=10,
        )
        return response.status_code





    def create_session(self, dataset_id: str) -> tuple[dict, int]:
        response = httpx.post(
            f"{self.base_url}/api/v1/chat/sessions",
            headers=self._headers(),
            json={"dataset_id": dataset_id},
            timeout=15,
        )
        return response.json(), response.status_code

    def list_sessions(self) -> tuple[list, int]:
        response = httpx.get(
            f"{self.base_url}/api/v1/chat/sessions",
            headers=self._headers(),
            timeout=10,
        )
        return response.json(), response.status_code

    def get_session(self, session_id: str) -> tuple[dict, int]:
        response = httpx.get(
            f"{self.base_url}/api/v1/chat/sessions/{session_id}",
            headers=self._headers(),
            timeout=10,
        )
        return response.json(), response.status_code

    def send_message(self, session_id: str, message: str) -> tuple[dict, int]:
        response = httpx.post(
            f"{self.base_url}/api/v1/chat/sessions/{session_id}/message",
            headers=self._headers(),
            json={"message": message},
            timeout=60,  # LLM calls can take 10-30 seconds
        )
        return response.json(), response.status_code
