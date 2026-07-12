import time
import logging
import httpx
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"
POLL_INTERVAL = 2   # seconds between polls
MAX_POLLS = 30      # max 60 seconds waiting


class MLToolInput(BaseModel):
    model_type: str = Field(
        description="Type: 'forecast' for predictions, 'anomaly' for outlier detection, 'churn' for customer churn"
    )
    target_column: str = Field(description="The numeric column to analyze")
    dataset_id: str = Field(description="The dataset ID")


class MLTool(BaseTool):
    """
    Triggers ML model training and polls for results.
    Used for FORECAST, ANOMALY, and CHURN intents.
    """
    name: str = "run_ml_model"
    description: str = (
        "Run machine learning on the dataset. "
        "Use for: 'forecast'=predict future values, 'anomaly'=detect outliers, 'churn'=customer churn. "
        "Input model_type, target_column (numeric column name), and dataset_id."
    )
    args_schema: type[BaseModel] = MLToolInput

    # Injected by the agent executor
    _token: str = ""
    _dataset_id: str = ""

    def set_context(self, token: str, dataset_id: str) -> None:
        self._token = token
        self._dataset_id = dataset_id

    def _run(self, model_type: str, target_column: str, dataset_id: str) -> str:
        headers = {"Authorization": f"Bearer {self._token}"}

        # Use injected dataset_id if not provided properly
        if not dataset_id or dataset_id == "unknown":
            dataset_id = self._dataset_id

        endpoint_map = {
            "forecast": f"{BACKEND_URL}/api/v1/ml/forecast",
            "anomaly":  f"{BACKEND_URL}/api/v1/ml/anomaly",
            "churn":    f"{BACKEND_URL}/api/v1/ml/churn",
        }

        endpoint = endpoint_map.get(model_type.lower())
        if not endpoint:
            return f"Error: Unknown model_type '{model_type}'. Use 'forecast', 'anomaly', or 'churn'."

        try:
            # Start the ML task
            response = httpx.post(
                endpoint,
                headers=headers,
                json={"dataset_id": dataset_id, "target_column": target_column},
                timeout=15,
            )

            if response.status_code != 202:
                return f"Error starting ML task: {response.text[:200]}"

            task_id = response.json()["task_id"]
            logger.info(f"ML task started: type={model_type} task_id={task_id}")

            # Poll for result
            poll_url = f"{BACKEND_URL}/api/v1/ml/results/{task_id}"
            for attempt in range(MAX_POLLS):
                time.sleep(POLL_INTERVAL)
                poll_response = httpx.get(poll_url, headers=headers, timeout=10)

                if poll_response.status_code != 200:
                    continue

                result = poll_response.json()
                status = result.get("status")

                if status == "complete":
                    return self._format_result(model_type, result)
                elif status == "failed":
                    error = result.get("error_message", "Unknown error")
                    return f"ML task failed: {error}"
                # else: still pending/running, keep polling

            return f"ML task timed out after {MAX_POLLS * POLL_INTERVAL} seconds. Try again."

        except Exception as e:
            logger.error(f"ML tool error: {e}")
            return f"Error running ML model: {str(e)}"

    def _format_result(self, model_type: str, result: dict) -> str:
        """Format ML result as a readable text summary."""
        data = result.get("result_data", {})

        if model_type == "forecast":
            dates = data.get("dates", [])
            preds = data.get("predictions", [])
            lower = data.get("lower_ci", [])
            upper = data.get("upper_ci", [])
            mae = data.get("mae", 0)
            r2 = data.get("r2_score", 0)

            lines = [f"📈 FORECAST COMPLETE (MAE: {mae:,.0f}, R²: {r2:.2f})\n"]
            for d, p, l, u in zip(dates, preds, lower, upper):
                lines.append(f"  {d}: {p:,.0f} (range: {l:,.0f} – {u:,.0f})")
            return "\n".join(lines)

        elif model_type == "anomaly":
            count = data.get("anomaly_count", 0)
            total = data.get("total_count", 0)
            pct   = data.get("anomaly_pct", 0)
            top   = data.get("top_anomalies", [])

            lines = [f"🔍 ANOMALY DETECTION COMPLETE\n"]
            lines.append(f"Found {count} anomalies out of {total} data points ({pct}%)\n")
            if top:
                lines.append("Most extreme anomalies:")
                for a in top[:3]:
                    col = list(a.keys())[0]
                    lines.append(f"  Value: {a.get(col, 'N/A'):,.2f} (score: {a.get('anomaly_score', 0):.2f})")
            return "\n".join(lines)

        elif model_type == "churn":
            accuracy = data.get("accuracy", 0)
            fi = data.get("feature_importance", [])
            at_risk = data.get("top_at_risk_customers", [])

            lines = [f"⚠️ CHURN PREDICTION COMPLETE (Accuracy: {accuracy:.1%})\n"]
            if fi:
                lines.append("Top factors driving churn:")
                for f in fi[:3]:
                    lines.append(f"  {f['feature']}: {f['importance']:.1%} importance")
            high_risk = [c for c in at_risk if c.get("risk_level") == "High"]
            lines.append(f"\n{len(high_risk)} customers at HIGH risk of churning.")
            return "\n".join(lines)

        return f"ML task complete: {str(data)[:200]}"

    async def _arun(self, model_type: str, target_column: str, dataset_id: str) -> str:
        return self._run(model_type, target_column, dataset_id)


ml_tool = MLTool()