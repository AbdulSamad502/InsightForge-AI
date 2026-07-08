import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


def setup_langsmith() -> None:
    """
    Configure LangSmith tracing.
    Called once at app startup.
    When LANGCHAIN_TRACING_V2=true, every LangChain call is
    automatically traced — no extra code needed per call.
    """
    import os
    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2).lower()
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

    if settings.langchain_tracing_v2 and settings.langchain_api_key:
        logger.info(
            f"LangSmith tracing enabled → project: '{settings.langchain_project}'"
        )
    else:
        logger.info("LangSmith tracing disabled (no API key or tracing=false)")


def log_llm_usage(
    operation: str,
    model: str,
    tokens_used: int | None = None,
    latency_ms: float | None = None,
    success: bool = True,
) -> None:
    """
    Log LLM usage to application logs.
    Separate from LangSmith — this goes to your logs/ folder.
    """
    logger.info(
        f"[LLM] operation={operation} model={model} "
        f"tokens={tokens_used} latency={latency_ms}ms success={success}"
    )