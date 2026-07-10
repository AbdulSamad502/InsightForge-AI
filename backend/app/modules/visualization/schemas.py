from pydantic import BaseModel
from typing import Any


class ChartRequest(BaseModel):
    chart_type: str          # line | bar | pie | heatmap | histogram | scatter
    x_column: str
    y_column: str | None = None
    color_column: str | None = None
    title: str = ""
    dataset_id: str


class ChartResponse(BaseModel):
    chart_type: str
    chart_json: str          # Plotly JSON string
    x_column: str
    y_column: str | None


class ExplainChartRequest(BaseModel):
    chart_type: str
    x_column: str
    y_column: str | None = None
    data_summary: str        # e.g. "Electronics: 2.1M, Furniture: 800K, Total: 2.9M"
    title: str = ""


class ExplainChartResponse(BaseModel):
    explanation: str         # 2-sentence business explanation
