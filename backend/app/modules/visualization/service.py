import logging
import pandas as pd
from pathlib import Path
from app.core.config import settings
from app.core.constants import IntentType
from app.modules.visualization.builders import line, bar, pie, heatmap, histogram, scatter
from app.modules.visualization.schemas import ChartResponse, ExplainChartResponse
from app.ai.llm_factory import get_fast_llm

logger = logging.getLogger(__name__)

# ── Chart type decision rules ──────────────────────────────

CHART_TYPE_RULES = {
    # Keywords → chart type
    "trend":        "line",
    "over time":    "line",
    "time series":  "line",
    "monthly":      "line",
    "weekly":       "line",
    "daily":        "line",
    "growth":       "line",
    "change":       "line",

    "distribution": "histogram",
    "spread":       "histogram",
    "range":        "histogram",
    "frequency":    "histogram",
    "how many":     "histogram",

    "proportion":   "pie",
    "percentage":   "pie",
    "share":        "pie",
    "breakdown":    "pie",
    "composition":  "pie",
    "percent":      "pie",

    "correlation":  "heatmap",
    "relationship": "scatter",
    "vs":           "scatter",
    "versus":       "scatter",
    "compare two":  "scatter",
    "x vs y":       "scatter",
}


def decide_chart_type(question: str, df: pd.DataFrame) -> str:
    """
    Decide the best chart type for a question.
    Priority: keyword matching → column type analysis → default bar
    """
    q_lower = question.lower()

    # Direct keyword match
    for keyword, chart_type in CHART_TYPE_RULES.items():
        if keyword in q_lower:
            return chart_type

    # Explicit mentions
    for chart_name in ["bar", "line", "pie", "histogram", "scatter", "heatmap"]:
        if chart_name in q_lower:
            return chart_name

    # Default: bar chart (most universal for business data)
    return "bar"


def generate_chart(
    df: pd.DataFrame,
    chart_type: str,
    x_col: str,
    y_col: str | None = None,
    color_col: str | None = None,
    title: str = "",
) -> str:
    """
    Route to the correct chart builder based on chart_type.
    Returns Plotly JSON string.
    """
    chart_type = chart_type.lower().strip()

    try:
        if chart_type == "line":
            return line.make_line_chart(df, x_col, y_col or "", title=title)

        elif chart_type == "bar":
            return bar.make_bar_chart(df, x_col, y_col or "", title=title, color_col=color_col)

        elif chart_type == "pie":
            return pie.make_pie_chart(df, x_col, y_col or "", title=title)

        elif chart_type == "heatmap":
            columns = [c for c in [x_col, y_col] if c] or None
            return heatmap.make_heatmap(df, columns=columns, title=title)

        elif chart_type == "histogram":
            return histogram.make_histogram(df, x_col, title=title)

        elif chart_type == "scatter":
            return scatter.make_scatter(df, x_col, y_col or "", color_col=color_col, title=title)

        else:
            # Unknown type — fallback to bar
            logger.warning(f"Unknown chart type '{chart_type}', falling back to bar")
            return bar.make_bar_chart(df, x_col, y_col or "", title=title)

    except Exception as e:
        logger.error(f"Chart generation failed: type={chart_type} error={e}")
        return '{"error": "Chart generation failed."}'


async def explain_chart(
    chart_type: str,
    x_column: str,
    y_column: str | None,
    data_summary: str,
    title: str = "",
) -> ExplainChartResponse:
    """
    Uses LLM to explain what a chart shows in 2 business sentences.
    Powers the 'Explain this chart' button.
    """
    import time
    from app.ai.llm_factory import get_fast_llm
    from langchain_core.messages import HumanMessage
    from app.ai.observability import log_llm_usage

    prompt = f"""You are a business analyst explaining a chart to a non-technical manager.

Chart type: {chart_type}
Chart title: {title or f'{y_column} by {x_column}'}
X axis: {x_column}
Y axis: {y_column or 'count'}
Data summary: {data_summary}

Write exactly 2 sentences:
1. What the chart shows (the main pattern or finding)
2. What this means for the business (the implication)

Be specific with numbers. Use plain language. No jargon."""

    try:
        llm = get_fast_llm()
        start = time.perf_counter()
        response = llm.invoke([HumanMessage(content=prompt)])
        latency = round((time.perf_counter() - start) * 1000, 2)
        log_llm_usage("explain_chart", settings.ollama_fast_model, latency_ms=latency)

        return ExplainChartResponse(explanation=response.content.strip())

    except Exception as e:
        logger.error(f"Chart explanation failed: {e}")
        return ExplainChartResponse(
            explanation=f"This {chart_type} chart shows the relationship between {x_column} and {y_column or 'count'}. Use it to identify patterns and outliers in your data."
        )
