import logging
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.shared.dependencies import get_current_user
from app.modules.authentication.models import User
from app.modules.visualization.schemas import (
    ChartRequest, ChartResponse,
    ExplainChartRequest, ExplainChartResponse,
)
from app.modules.visualization import service
from app.modules.datasets.repository import get_dataset_by_id
from app.core.exceptions import DatasetNotFoundError
import pandas as pd

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/visualization", tags=["Visualization"])


def _load_df(dataset_id: str, user_id: str, db: Session) -> pd.DataFrame:
    """Helper to load dataset into DataFrame."""
    dataset = get_dataset_by_id(db, dataset_id)
    if not dataset or dataset.user_id != user_id:
        raise DatasetNotFoundError(dataset_id)
    file_path = Path(dataset.file_path)
    if dataset.file_type == "csv":
        return pd.read_csv(file_path, low_memory=False)
    return pd.read_excel(file_path, engine="openpyxl")


@router.post("/generate", response_model=ChartResponse)
def generate_chart(
    request: ChartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a chart from a dataset."""
    df = _load_df(request.dataset_id, current_user.id, db)

    chart_json = service.generate_chart(
        df=df,
        chart_type=request.chart_type,
        x_col=request.x_column,
        y_col=request.y_column,
        color_col=request.color_column,
        title=request.title,
    )

    return ChartResponse(
        chart_type=request.chart_type,
        chart_json=chart_json,
        x_column=request.x_column,
        y_column=request.y_column,
    )


@router.post("/explain", response_model=ExplainChartResponse)
async def explain_chart(
    request: ExplainChartRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Explain what a chart shows in plain business English.
    Powers the 'Explain this chart' button in the UI.
    """
    return await service.explain_chart(
        chart_type=request.chart_type,
        x_column=request.x_column,
        y_column=request.y_column,
        data_summary=request.data_summary,
        title=request.title,
    )


@router.get("/chart-types")
def get_chart_types():
    """Return available chart types and when to use each."""
    return {
        "chart_types": [
            {"type": "bar",       "best_for": "Comparing categories"},
            {"type": "line",      "best_for": "Trends over time"},
            {"type": "pie",       "best_for": "Proportions and percentages"},
            {"type": "histogram", "best_for": "Distribution of a single column"},
            {"type": "scatter",   "best_for": "Relationship between two numeric columns"},
            {"type": "heatmap",   "best_for": "Correlation between all numeric columns"},
        ]
    }
