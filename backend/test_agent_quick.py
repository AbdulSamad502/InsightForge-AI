"""
Quick manual test for the agent. Run from backend/ directory.
Delete this file after testing.
"""
import asyncio
import pandas as pd
from app.ai.agent.executor import run_agent
from app.ai.agent.intent_classifier import classify_intent
from app.core.constants import IntentType


async def main():
    # Create a sample DataFrame
    df = pd.DataFrame({
        "product":    ["Laptop", "Phone", "Laptop", "Chair", "Desk", "Headphones"],
        "category":  ["Electronics", "Electronics", "Electronics", "Furniture", "Furniture", "Electronics"],
        "revenue":   [45000, 25000, 45000, 8000, 12000, 3500],
        "quantity":  [2, 5, 2, 3, 1, 10],
        "order_date": ["2024-01-15", "2024-01-16", "2024-01-17", "2024-01-18", "2024-01-19", "2024-01-20"],
    })

    columns = list(df.columns)

    # Test 1: Intent classification
    print("\n=== INTENT CLASSIFICATION TESTS ===")
    test_questions = [
        "What is total revenue by category?",
        "Show me a bar chart of sales",
        "Predict next month's revenue",
        "Are there any anomalies in the data?",
        "Which customers are at risk of churning?",
    ]
    for q in test_questions:
        intent = await classify_intent(q, columns)
        print(f"Q: {q}")
        print(f"   → Intent: {intent.value}\n")

    # Test 2: Full agent run
    print("\n=== FULL AGENT TEST ===")
    question = "What is the total revenue by product category?"
    intent = await classify_intent(question, columns)

    result = await run_agent(
        question=question,
        df=df,
        session_id="test-session-001",
        intent=intent,
    )

    print(f"Question: {question}")
    print(f"Intent: {result['intent']}")
    print(f"Text: {result['text']}")
    print(f"Has chart: {result['chart_json'] is not None}")
    print(f"Insight: {result['insight']}")
    print(f"Recommendation: {result['recommendation']}")


if __name__ == "__main__":
    asyncio.run(main())


