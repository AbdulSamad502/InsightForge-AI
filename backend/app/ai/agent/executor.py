import logging
import pandas as pd
from pathlib import Path
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.core.config import settings,key_rotator
from app.ai.tools.registry import ToolRegistry
from app.ai.tools.pandas_tool import pandas_tool
from app.ai.tools.chart_tool import chart_tool
from app.ai.tools.ml_tool import ml_tool
from app.ai.tools.insight_tool import insight_tool
from app.ai.agent.memory import get_memory
from app.ai.agent.tool_chain import build_chained_tools
from app.core.constants import IntentType
from app.core.key_manager import get_next_key

logger = logging.getLogger(__name__)

# ── Load system prompt ─────────────────────────────────────
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "analytics.md"
_SYSTEM_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")


# ── Register all tools ─────────────────────────────────────
ToolRegistry.register(pandas_tool)
ToolRegistry.register(chart_tool)
ToolRegistry.register(insight_tool)
ToolRegistry.register(ml_tool)

logger.info(f"Tools registered: {ToolRegistry.list_names()}")

_DATE_COLUMN_KEYWORDS = ("date", "time", "created", "updated", "timestamp", "datetime")


def _normalize_categorical_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip, lowercase, and title-case string columns before groupby operations."""
    normalized = df.copy()
    for col in normalized.select_dtypes(include=["object", "string"]).columns:
        if any(kw in col.lower() for kw in _DATE_COLUMN_KEYWORDS):
            continue
        normalized[col] = normalized[col].map(
            lambda x: x.strip().lower().title() if isinstance(x, str) else x
        )
    return normalized


def _strip_structured_sections(text: str) -> str:
    """Remove insight, recommendation, and embedded chart JSON from agent output."""
    if not text:
        return text

    for marker in ("\n\nINSIGHT:", "\nINSIGHT:", "\n\nRECOMMENDATION:", "\nRECOMMENDATION:"):
        if marker in text:
            text = text.split(marker, 1)[0]

    plotly_start = text.find('{"data"')
    if plotly_start != -1:
        text = text[:plotly_start]

    return text.strip()


def _format_direct_answer(pandas_output: str) -> str:
    """Format pandas tool output as a concise answer with numbers."""
    raw = pandas_output.strip()
    if not raw:
        return raw

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(lines) == 1:
        return lines[0]

    pairs: list[str] = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 2:
            try:
                float(parts[-1].replace(",", ""))
                label = " ".join(parts[:-1])
                pairs.append(f"{label}: {parts[-1]}")
                continue
            except ValueError:
                pass
        if line.lower() not in {"name", "dtype", "category", "index"}:
            pairs.append(line)

    return "; ".join(pairs) if pairs else raw


def _build_response_text(pandas_output: str | None, agent_output: str) -> str:
    if pandas_output and not pandas_output.startswith("Error"):
        return _format_direct_answer(pandas_output)
    return _strip_structured_sections(agent_output) or "I was unable to answer that question."


def _build_df_schema(df: pd.DataFrame) -> str:
    """Minimal schema — column names and types only."""
    lines = [f"Shape: {df.shape[0]} rows × {df.shape[1]} cols", "Columns:"]
    for col in df.columns:
        dtype = "num" if pd.api.types.is_numeric_dtype(df[col]) else "text"
        lines.append(f"  {col} ({dtype})")
    return "\n".join(lines)


def _build_intent_hint(intent: IntentType) -> str:
    """Add intent context to help the agent choose the right tool first."""
    hints = {
        IntentType.ANALYTICS: "The user wants data analysis. Start with pandas_analysis.",
        IntentType.VISUALIZATION: "The user wants a chart. Use pandas_analysis first, then generate_chart.",
        IntentType.FORECAST: "The user wants forecasting. Use run_ml_model with model_type='forecast'.",
        IntentType.ANOMALY: "The user wants anomaly detection. Use run_ml_model with model_type='anomaly'.",
        IntentType.CHURN: "The user wants churn analysis. Use run_ml_model with model_type='churn'.",
        IntentType.GENERAL: "Answer using pandas_analysis if data-related.",
    }
    return hints.get(intent, "")


async def run_agent(
    question: str,
    df: pd.DataFrame,
    session_id: str,
    intent: IntentType = IntentType.GENERAL,
    dataset_id: str = "",
)-> dict:
    """
    Main entry point for the AI agent.
    
    Returns:
    {
        "text": str,           # agent's text response
        "chart_json": str|None, # Plotly JSON if chart was generated
        "insight": str|None,   # business insight
        "recommendation": str|None, # actionable recommendation
        "intent": str,
        "code_used": str|None,
    }
    """

    # Inject the current DataFrame into tools that need it
    df = _normalize_categorical_columns(df)
    pandas_tool.set_dataframe(df)
    chart_tool.set_dataframe(df)
    ml_tool.set_context(
    token="",
    dataset_id=dataset_id
    )

    # Build schema string for system prompt
    df_schema = _build_df_schema(df)
    intent_hint = _build_intent_hint(intent)
    # Use replace, not .format() — analytics.md contains Python f-string examples
    # like {result:.2f} that .format() would treat as missing placeholders.
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.replace("{df_schema}", df_schema)
    if intent_hint:
        system_prompt += f"\n\nCURRENT INTENT HINT: {intent_hint}"

    # Build LangChain prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Build LLM
    llm = ChatGroq(
        model=settings.groq_main_model,
        api_key=get_next_key(),
        temperature=0.1,
        max_tokens=500,
    )

    # Build agent — wrap tools so pandas output chains into generate_insight
    df_columns = ", ".join(df.columns)
    tools = build_chained_tools(
        ToolRegistry.get_all(),
        df_columns=df_columns,
        user_question=question,
    )
    agent = create_tool_calling_agent(llm, tools, prompt)

    # Build executor
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,  # logs each step to console — great for debugging
        max_iterations=6,  # prevent infinite loops
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    # Get session memory
    memory = get_memory(session_id)
    chat_history = memory.chat_memory.messages if memory.chat_memory.messages else []

    try:
        response = await executor.ainvoke({
            "input": question,
            "chat_history": chat_history,
        })

        # Parse intermediate steps to extract tool outputs
        chart_json = None
        insight_text = None
        recommendation_text = None
        code_used = None
        pandas_output = None

        for step in response.get("intermediate_steps", []):
            tool_name = step[0].tool if hasattr(step[0], 'tool') else ""
            tool_output = step[1] if len(step) > 1 else ""

            if tool_name == "pandas_analysis":
                code_used = step[0].tool_input.get("code", "") if hasattr(step[0], 'tool_input') else ""
                if tool_output and not str(tool_output).startswith("Error"):
                    pandas_output = str(tool_output)

            elif tool_name == "generate_chart":
                # Chart tool returns Plotly JSON
                if tool_output and not tool_output.startswith("Error"):
                    chart_json = tool_output

            elif tool_name == "generate_insight":
                # Parse INSIGHT: ... RECOMMENDATION: ... format
                if tool_output and "INSIGHT:" in tool_output:
                    parts = tool_output.split("RECOMMENDATION:")
                    insight_text = parts[0].replace("INSIGHT:", "").strip()
                    if len(parts) > 1:
                        recommendation_text = parts[1].strip()

        agent_output = response.get("output", "")
        text = _build_response_text(pandas_output, agent_output)

        # Save to memory — direct answer only, not insight/recommendation
        memory.chat_memory.add_user_message(question)
        memory.chat_memory.add_ai_message(text)

        return {
            "text": text,
            "chart_json": chart_json,
            "insight": insight_text,
            "recommendation": recommendation_text,
            "intent": intent.value,
            "code_used": code_used,
        }

    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        return {
            "text": f"I encountered an error analyzing your data: {str(e)}. Please try rephrasing your question.",
            "chart_json": None,
            "insight": None,
            "recommendation": None,
            "intent": intent.value,
            "code_used": None,
        }
