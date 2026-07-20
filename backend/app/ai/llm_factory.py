import logging

from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_main_llm():
    print("=" * 60)
    print("MAIN LLM")
    print(settings.llm_provider)
    print("=" * 60)

    if settings.llm_provider.lower() == "groq":
        return ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0.1,
        )

    return ChatOllama(
        model=settings.ollama_main_model,
        base_url=settings.ollama_base_url,
        temperature=0.1,
        num_predict=500,
    )


def get_fast_llm():
    print("=" * 60)
    print("FAST LLM")
    print(settings.llm_provider)
    print("=" * 60)

    if settings.llm_provider.lower() == "groq":
        return ChatGroq(
            model=settings.groq_fast_model,
            api_key=settings.groq_api_key,
            temperature=0,
        )

    return ChatOllama(
        model=settings.ollama_fast_model,
        base_url=settings.ollama_base_url,
        temperature=0,
        num_predict=256,
    )