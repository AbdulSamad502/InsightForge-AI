import json
import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ChartToolInput(BaseModel):
    chart_type: str = Field(
        description="Type of chart: 'bar', 'line', 'pie', 'histogram', 'scatter', 'heatmap'"
    )
    x_column: str = Field(description="Column name for X axis")
    y_column: str = Field(description="Column name for Y axis (or values for pie)")
    title: str = Field(description="Chart title", default="")


class ChartTool(BaseTool):
    """
    Generates a Plotly chart from the current dataframe.
    Returns the chart as a JSON string that the frontend renders.
    """
    name: str = "generate_chart"
    description: str = (
        "Generate a chart to visualize data. "
        "Use after getting analysis results when a visual would help. "
        "Specify chart_type (bar/line/pie/histogram/scatter), x_column, y_column, and title. "
        "Returns Plotly chart JSON."
    )
    args_schema: type[BaseModel] = ChartToolInput

    _df: pd.DataFrame | None = None

    def set_dataframe(self, df: pd.DataFrame) -> None:
        self._df = df

    def _run(self, chart_type: str, x_column: str, y_column: str, title: str = "") -> str:
        if self._df is None:
            return "Error: No dataframe loaded."

        try:
            df = self._df

            # Validate columns exist
            if x_column not in df.columns:
                return f"Error: Column '{x_column}' not found. Available: {list(df.columns)}"
            if y_column not in df.columns and chart_type != "histogram":
                return f"Error: Column '{y_column}' not found. Available: {list(df.columns)}"

            fig = None
            chart_type = chart_type.lower().strip()

            if chart_type == "bar":
                # If x is categorical, groupby first
                if df[x_column].dtype == object:
                    plot_df = df.groupby(x_column)[y_column].sum().reset_index()
                else:
                    plot_df = df[[x_column, y_column]]
                fig = px.bar(plot_df, x=x_column, y=y_column, title=title or f"{y_column} by {x_column}")

            elif chart_type == "line":
                plot_df = df.sort_values(x_column)
                fig = px.line(plot_df, x=x_column, y=y_column, title=title or f"{y_column} over {x_column}")

            elif chart_type == "pie":
                if df[x_column].dtype == object:
                    plot_df = df.groupby(x_column)[y_column].sum().reset_index()
                else:
                    plot_df = df[[x_column, y_column]]
                fig = px.pie(plot_df, names=x_column, values=y_column, title=title or f"{y_column} by {x_column}")

            elif chart_type == "histogram":
                fig = px.histogram(df, x=x_column, title=title or f"Distribution of {x_column}")

            elif chart_type == "scatter":
                fig = px.scatter(df, x=x_column, y=y_column, title=title or f"{x_column} vs {y_column}")

            else:
                fig = px.bar(df, x=x_column, y=y_column, title=title)

            if fig is None:
                return "Error: Could not generate chart."

            # Apply consistent theme
            fig.update_layout(
                template="plotly_white",
                font=dict(family="Inter, sans-serif"),
                margin=dict(t=50, l=20, r=20, b=20),
            )

            return fig.to_json()

        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            return f"Error generating chart: {str(e)}"

    async def _arun(self, chart_type: str, x_column: str, y_column: str, title: str = "") -> str:
        return self._run(chart_type, x_column, y_column, title)


chart_tool = ChartTool()