
import time
import logging
from pathlib import Path
from langchain.tools import BaseTool
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from app.core.config import settings,key_rotator
from app.ai.observability import log_llm_usage
from app.core.key_manager import get_next_key

logger = logging.getLogger(__name__)

# Load prompts once at module load time
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(filename: str) -> str:
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8")


class InsightToolInput(BaseModel):
    question: str = Field(description="The original user question")
    result: str = Field(description="The analysis result from pandas execution")
    columns: str = Field(description="Comma-separated list of dataset column names")


class InsightTool(BaseTool):
    """
    Takes a pandas analysis result and generates:
    1. A plain-English business insight (what it means)
    2. One specific, actionable recommendation (what to do)
    """
    name: str = "generate_insight"
    description: str = (
        "After getting analysis results, use this tool to generate a business insight "
        "and recommendation. Input the original question, the result, and column names."
    )
    args_schema: type[BaseModel] = InsightToolInput

    def _run(self, question: str, result: str, columns: str) -> str:
        try:
            insight_prompt_template = _load_prompt("insight.md")
            rec_prompt_template = _load_prompt("recommendation.md")

            llm = ChatGroq(
                model=settings.groq_main_model,
                api_key=get_next_key(),
                temperature=0.4,
                max_tokens=300,
            )

            # Step 1: Generate insight
            insight_prompt = insight_prompt_template.format(
                question=question,
                result=result[:2000],  # truncate very long results
                columns=columns,
            )
            start = time.perf_counter()
            insight_response = llm.invoke([HumanMessage(content=insight_prompt)])
            insight_text = insight_response.content.strip()

            # Step 2: Generate recommendation based on insight
            rec_prompt = rec_prompt_template.format(insight=insight_text)
            rec_response = llm.invoke([HumanMessage(content=rec_prompt)])
            rec_text = rec_response.content.strip()

            latency = round((time.perf_counter() - start) * 1000, 2)
            log_llm_usage("generate_insight", settings.groq_main_model, latency_ms=latency)

            return f"INSIGHT: {insight_text}\n\nRECOMMENDATION: {rec_text}"

        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return f"INSIGHT: Analysis complete.\n\nRECOMMENDATION: Review the data above for actionable patterns."

    async def _arun(self, question: str, result: str, columns: str) -> str:
        return self._run(question, result, columns)


insight_tool = InsightTool()