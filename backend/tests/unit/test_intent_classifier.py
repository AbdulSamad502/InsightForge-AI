"""
Intent classifier tests.
We mock the Groq LLM call so tests run without API keys.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ── Mock the LLM response ──────────────────────────────────

def make_mock_llm(intent_value: str):
    """Create a mock LLM that returns a specific intent."""
    mock_response = MagicMock()
    mock_response.content = f'{{"intent": "{intent_value}"}}'
    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(return_value=mock_response)
    return mock_llm


SAMPLE_COLUMNS = ["product", "category", "revenue", "quantity", "order_date"]


@pytest.mark.asyncio
async def test_analytics_intent():
    with patch("app.ai.agent.intent_classifier.ChatGroq") as mock:
        mock.return_value = make_mock_llm("analytics")
        from app.ai.agent.intent_classifier import classify_intent
        from app.core.constants import IntentType
        result = await classify_intent("What is the total revenue by category?", SAMPLE_COLUMNS)
        assert result == IntentType.ANALYTICS


@pytest.mark.asyncio
async def test_visualization_intent():
    with patch("app.ai.agent.intent_classifier.ChatGroq") as mock:
        mock.return_value = make_mock_llm("visualization")
        from app.ai.agent.intent_classifier import classify_intent
        from app.core.constants import IntentType
        result = await classify_intent("Show me a bar chart of revenue", SAMPLE_COLUMNS)
        assert result == IntentType.VISUALIZATION


@pytest.mark.asyncio
async def test_forecast_intent():
    with patch("app.ai.agent.intent_classifier.ChatGroq") as mock:
        mock.return_value = make_mock_llm("forecast")
        from app.ai.agent.intent_classifier import classify_intent
        from app.core.constants import IntentType
        result = await classify_intent("Predict next month's revenue", SAMPLE_COLUMNS)
        assert result == IntentType.FORECAST


@pytest.mark.asyncio
async def test_anomaly_intent():
    with patch("app.ai.agent.intent_classifier.ChatGroq") as mock:
        mock.return_value = make_mock_llm("anomaly")
        from app.ai.agent.intent_classifier import classify_intent
        from app.core.constants import IntentType
        result = await classify_intent("Are there any anomalies in the data?", SAMPLE_COLUMNS)
        assert result == IntentType.ANOMALY


@pytest.mark.asyncio
async def test_churn_intent():
    with patch("app.ai.agent.intent_classifier.ChatGroq") as mock:
        mock.return_value = make_mock_llm("churn")
        from app.ai.agent.intent_classifier import classify_intent
        from app.core.constants import IntentType
        result = await classify_intent("Which customers are at risk of churning?", SAMPLE_COLUMNS)
        assert result == IntentType.CHURN


@pytest.mark.asyncio
async def test_general_intent():
    with patch("app.ai.agent.intent_classifier.ChatGroq") as mock:
        mock.return_value = make_mock_llm("general")
        from app.ai.agent.intent_classifier import classify_intent
        from app.core.constants import IntentType
        result = await classify_intent("Hello, how are you?", SAMPLE_COLUMNS)
        assert result == IntentType.GENERAL


@pytest.mark.asyncio
async def test_fallback_on_bad_json():
    """If LLM returns invalid JSON, should fallback to GENERAL."""
    mock_response = MagicMock()
    mock_response.content = "this is not json at all"
    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(return_value=mock_response)

    with patch("app.ai.agent.intent_classifier.ChatGroq") as mock:
        mock.return_value = mock_llm
        from app.ai.agent.intent_classifier import classify_intent
        from app.core.constants import IntentType
        result = await classify_intent("Some question", SAMPLE_COLUMNS)
        assert result == IntentType.GENERAL


@pytest.mark.asyncio
async def test_fallback_on_exception():
    """If LLM raises exception, should fallback to GENERAL."""
    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(side_effect=Exception("API error"))

    with patch("app.ai.agent.intent_classifier.ChatGroq") as mock:
        mock.return_value = mock_llm
        from app.ai.agent.intent_classifier import classify_intent
        from app.core.constants import IntentType
        result = await classify_intent("Some question", SAMPLE_COLUMNS)
        assert result == IntentType.GENERAL


@pytest.mark.asyncio
async def test_unknown_intent_maps_to_general():
    """If LLM returns an unknown intent string, maps to GENERAL."""
    with patch("app.ai.agent.intent_classifier.ChatGroq") as mock:
        mock.return_value = make_mock_llm("unknown_type")
        from app.ai.agent.intent_classifier import classify_intent
        from app.core.constants import IntentType
        result = await classify_intent("Something weird", SAMPLE_COLUMNS)
        assert result == IntentType.GENERAL


@pytest.mark.asyncio
async def test_empty_columns():
    """Should work even with empty column list."""
    with patch("app.ai.agent.intent_classifier.ChatGroq") as mock:
        mock.return_value = make_mock_llm("analytics")
        from app.ai.agent.intent_classifier import classify_intent
        from app.core.constants import IntentType
        result = await classify_intent("Total revenue?", [])
        assert result == IntentType.ANALYTICS