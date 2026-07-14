import httpx
import streamlit as st
import os


def _get_backend_url():

    try:
        return st.secrets["BACKEND_URL"]

    except Exception:
        return os.getenv(
            "BACKEND_URL",
            "http://localhost:8000"
        )


BACKEND_URL = _get_backend_url()


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
            timeout=180,  # uploads can take time
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
            timeout=180,  # LLM calls can take 10-30 seconds
        )
        return response.json(), response.status_code
    def explain_chart(
    self,
    chart_type: str,
    x_column: str,
    y_column: str,
    data_summary: str,
    title: str,
    ) -> tuple[dict, int]:

        response = httpx.post(
            f"{self.base_url}/api/v1/visualization/explain",
            headers=self._headers(),
            json={
                "chart_type": chart_type,
                "x_column": x_column,
                "y_column": y_column,
                "data_summary": data_summary,
                "title": title,
            },
            timeout=60,
        )

        return response.json(), response.status_code

    # def explain_chart(self, chart_data: dict) -> tuple[dict, int]:
    #     response = httpx.post(
    #         f"{self.base_url}/api/v1/visualization/explain",
    #         headers=self._headers(),
    #         json={
    #             "chart_data": chart_data
    #         },
    #         timeout=60,
    #     )
    #     return response.json(), response.status_code

    # ── ML methods ─────────────────────────────────────────

    def run_forecast(self, dataset_id: str, target_column: str, n_periods: int = 3) -> tuple[dict, int]:
        response = httpx.post(
            f"{self.base_url}/api/v1/ml/forecast",
            headers=self._headers(),
            json={"dataset_id": dataset_id, "target_column": target_column, "n_periods": n_periods},
            timeout=15,
        )
        return response.json(), response.status_code

    def run_anomaly(self, dataset_id: str, target_column: str) -> tuple[dict, int]:
        response = httpx.post(
            f"{self.base_url}/api/v1/ml/anomaly",
            headers=self._headers(),
            json={"dataset_id": dataset_id, "target_column": target_column},
            timeout=15,
        )
        return response.json(), response.status_code

    def run_churn(self, dataset_id: str, target_column: str) -> tuple[dict, int]:
        response = httpx.post(
            f"{self.base_url}/api/v1/ml/churn",
            headers=self._headers(),
            json={"dataset_id": dataset_id, "target_column": target_column},
            timeout=15,
        )
        return response.json(), response.status_code

    def get_ml_result(self, task_id: str) -> tuple[dict, int]:
        response = httpx.get(
            f"{self.base_url}/api/v1/ml/results/{task_id}",
            headers=self._headers(),
            timeout=10,
        )
        return response.json(), response.status_code
    # ── Report methods ─────────────────────────────────────

    def generate_report(self, dataset_id: str) -> tuple[dict, int]:
        response = httpx.post(
            f"{self.base_url}/api/v1/reports/generate",
            headers=self._headers(),
            json={"dataset_id": dataset_id},
            timeout=15,
        )
        return response.json(), response.status_code

    def list_reports(self) -> tuple[list, int]:
        response = httpx.get(
            f"{self.base_url}/api/v1/reports/",
            headers=self._headers(),
            timeout=10,
        )
        return response.json(), response.status_code

    def get_report_status(self, report_id: str) -> tuple[dict, int]:
        response = httpx.get(
            f"{self.base_url}/api/v1/reports/{report_id}/status",
            headers=self._headers(),
            timeout=10,
        )
        return response.json(), response.status_code

    def download_report(self, report_id: str) -> bytes | None:
        response = httpx.get(
            f"{self.base_url}/api/v1/reports/{report_id}/download",
            headers=self._headers(),
            timeout=30,
        )
        if response.status_code == 200:
            return response.content
        return None

    # ── Dashboard methods ──────────────────────────────────

    def get_dashboard_summary(self) -> tuple[dict, int]:
        response = httpx.get(
            f"{self.base_url}/api/v1/dashboard/summary",
            headers=self._headers(),
            timeout=15,
        )
        return response.json(), response.status_code

