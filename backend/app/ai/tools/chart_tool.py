import json
import logging
import pandas as pd
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from app.modules.visualization.service import generate_chart, decide_chart_type

logger = logging.getLogger(__name__)


class ChartToolInput(BaseModel):
    chart_type: str = Field(
        description=(
            "Type of chart to generate. Choose the best one for the data:\n"
            "- 'bar': comparing categories (revenue by category, sales by product)\n"
            "- 'line': trends over time (monthly revenue, weekly orders)\n"
            "- 'pie': proportions/percentages (market share, category breakdown)\n"
            "- 'histogram': distribution of a single column (price distribution)\n"
            "- 'scatter': relationship between two numeric columns\n"
            "- 'heatmap': correlation between all numeric columns"
        )
    )
    x_column: str = Field(description="Column name for X axis (or labels for pie chart)")
    y_column: str = Field(description="Column name for Y axis (or values for pie chart). Use empty string for histogram.")
    title: str = Field(description="Descriptive chart title", default="")


class ChartTool(BaseTool):
    """
    Generates professional Plotly charts from the current dataset.
    Use after pandas_analysis to visualize results.
    """
    name: str = "generate_chart"
    description: str = (
        "Generate a chart to visualize data. "
        "Available types: bar, line, pie, histogram, scatter, heatmap. "
        "Use bar for categories, line for time trends, pie for proportions. "
        "Always use EXACT column names from the dataset schema."
    )
    args_schema: type[BaseModel] = ChartToolInput

    _df: pd.DataFrame | None = None

    def set_dataframe(self, df: pd.DataFrame) -> None:
        self._df = df

    def _run(self, chart_type: str, x_column: str, y_column: str = "", title: str = "") -> str:
        if self._df is None:
            return "Error: No dataframe loaded."

        # Validate columns exist
        available = list(self._df.columns)

        if x_column not in available:
            # Try case-insensitive match
            lower_map = {c.lower(): c for c in available}
            if x_column.lower() in lower_map:
                x_column = lower_map[x_column.lower()]
            else:
                return f"Error: Column '{x_column}' not found. Available columns: {available}"

        if y_column and y_column not in available:
            lower_map = {c.lower(): c for c in available}
            if y_column.lower() in lower_map:
                y_column = lower_map[y_column.lower()]
            elif chart_type != "histogram":
                return f"Error: Column '{y_column}' not found. Available columns: {available}"

        chart_json = generate_chart(
            df=self._df,
            chart_type=chart_type,
            x_col=x_column,
            y_col=y_column if y_column else None,
            title=title,
        )

        # Check if generation failed
        try:
            parsed = json.loads(chart_json)
            if "error" in parsed:
                return f"Chart error: {parsed['error']}"
        except Exception:
            pass

        logger.info(f"Chart generated: type={chart_type} x={x_column} y={y_column}")
        return chart_json

    async def _arun(self, chart_type: str, x_column: str, y_column: str = "", title: str = "") -> str:
        return self._run(chart_type, x_column, y_column, title)


# Replace the singleton
chart_tool = ChartTool()
