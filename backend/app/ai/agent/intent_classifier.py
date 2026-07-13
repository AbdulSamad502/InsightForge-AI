import json
import logging
from app.core.config import settings,key_rotator
from app.core.constants import IntentType
from app.core.key_manager import get_next_key
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)


INTENT_PROMPT = """You are an intent classifier for a data analysis chatbot.

Classify the user's question into exactly ONE of these categories:

- analytics: groupby, aggregation, sum, count, average, comparison, ranking, filtering, statistics
- visualization: "show me a chart", "plot", "graph", "visualize", "bar chart", "line chart"
- forecast: "predict", "forecast", "next month", "future", "trend prediction", "will be"
- anomaly: "anomaly", "unusual", "outlier", "spike", "abnormal", "unexpected"
- churn: "churn", "leave", "retention", "at risk", "likely to cancel", "customer loss"
- general: everything else, greetings, unclear questions, help requests

Dataset columns: {columns}
User question: {question}

Respond with ONLY a single JSON object. No explanation. No markdown.
Format: {{"intent": "analytics"}}"""


async def classify_intent(question: str, columns: list[str]) -> IntentType:
    """
    Uses the fast llama-8b model to classify the user's question.
    Falls back to GENERAL if classification fails.
    Cost: ~0.001 cents per call. Speed: ~200ms.
    """
    try:
        
        from langchain_core.messages import HumanMessage

        llm = ChatGroq(
            model=settings.groq_fast_model,  # llama-3.1-8b-instant — fast and cheap
            api_key=get_next_key(),
            temperature=0,  # deterministic classification
            max_tokens=10,  # we only need {"intent": "analytics"}
        )

        prompt = INTENT_PROMPT.format(
            columns=", ".join(columns[:20]),  # limit columns to avoid token waste
            question=question,
        )

        response = llm.invoke([HumanMessage(content=prompt)])
        raw = response.content.strip()

        # Parse JSON response
        if raw.startswith("```"):
            raw = raw.split("```")[1].strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()

        parsed = json.loads(raw)
        intent_str = parsed.get("intent", "general").lower()

        # Map to enum
        intent_map = {
            "analytics": IntentType.ANALYTICS,
            "visualization": IntentType.VISUALIZATION,
            "forecast": IntentType.FORECAST,
            "anomaly": IntentType.ANOMALY,
            "churn": IntentType.CHURN,
            "general": IntentType.GENERAL,
        }

        intent = intent_map.get(intent_str, IntentType.GENERAL)
        logger.info(f"Intent classified: '{question[:50]}' → {intent.value}")
        return intent

    except Exception as e:
        logger.warning(f"Intent classification failed: {e}. Defaulting to GENERAL.")
        return IntentType.GENERAL
