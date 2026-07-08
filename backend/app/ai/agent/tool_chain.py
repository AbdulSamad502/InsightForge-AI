import logging
from langchain.tools import BaseTool
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)

_PLACEHOLDER_RESULTS = frozenset({"result", "`result`"})


class ToolChainState:
    """Tracks outputs within a single agent run for downstream tool calls."""

    def __init__(self, df_columns: str, user_question: str):
        self.df_columns = df_columns
        self.user_question = user_question
        self.last_pandas_output: str | None = None


def _is_placeholder_result(value: str) -> bool:
    normalized = value.strip().strip("`")
    return normalized.lower() in _PLACEHOLDER_RESULTS


def _resolve_insight_result(result: str, state: ToolChainState) -> str:
    if _is_placeholder_result(result):
        if state.last_pandas_output:
            logger.info(
                "Tool chain: replaced placeholder result with pandas_analysis output"
            )
            return state.last_pandas_output
        logger.warning(
            "Tool chain: generate_insight received placeholder 'result' "
            "but no pandas_analysis output is available"
        )
    return result


def _wrap_pandas_tool(tool: BaseTool, state: ToolChainState) -> BaseTool:
    def _run(code: str) -> str:
        output = tool._run(code)
        if isinstance(output, str) and not output.startswith("Error"):
            state.last_pandas_output = output
        return output

    async def _arun(code: str) -> str:
        output = await tool._arun(code)
        if isinstance(output, str) and not output.startswith("Error"):
            state.last_pandas_output = output
        return output

    return StructuredTool.from_function(
        func=_run,
        coroutine=_arun,
        name=tool.name,
        description=tool.description,
        args_schema=tool.args_schema,
    )


def _wrap_insight_tool(tool: BaseTool, state: ToolChainState) -> BaseTool:
    def _run(question: str, result: str, columns: str) -> str:
        resolved_result = _resolve_insight_result(result, state)
        resolved_columns = columns or state.df_columns
        resolved_question = question or state.user_question
        return tool._run(
            question=resolved_question,
            result=resolved_result,
            columns=resolved_columns,
        )

    async def _arun(question: str, result: str, columns: str) -> str:
        resolved_result = _resolve_insight_result(result, state)
        resolved_columns = columns or state.df_columns
        resolved_question = question or state.user_question
        return await tool._arun(
            question=resolved_question,
            result=resolved_result,
            columns=resolved_columns,
        )

    return StructuredTool.from_function(
        func=_run,
        coroutine=_arun,
        name=tool.name,
        description=tool.description,
        args_schema=tool.args_schema,
    )


def build_chained_tools(
    tools: list[BaseTool],
    df_columns: str,
    user_question: str,
) -> list[BaseTool]:
    """Wrap agent tools so pandas output flows into downstream insight calls."""
    state = ToolChainState(df_columns=df_columns, user_question=user_question)

    chained: list[BaseTool] = []
    for tool in tools:
        if tool.name == "pandas_analysis":
            chained.append(_wrap_pandas_tool(tool, state))
        elif tool.name == "generate_insight":
            chained.append(_wrap_insight_tool(tool, state))
        else:
            chained.append(tool)
    return chained
