import io
import sys
import threading
import traceback
import logging
import numpy as np
import pandas as pd
from typing import Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ── What the agent is allowed to use inside exec() ────────
SAFE_BUILTINS = {
    # Basic types
    "len": len, "range": range, "list": list, "dict": dict,
    "str": str, "int": int, "float": float, "bool": bool,
    "tuple": tuple, "set": set, "type": type,
    # Math
    "sum": sum, "min": min, "max": max, "abs": abs,
    "round": round, "sorted": sorted, "enumerate": enumerate,
    "zip": zip, "map": map, "filter": filter,
    # Print — captured, not actually printed
    "print": print,
    # Safe exceptions
    "ValueError": ValueError, "TypeError": TypeError,
    "KeyError": KeyError, "IndexError": IndexError,
}

# ── What is NEVER allowed ──────────────────────────────────
BLOCKED_PATTERNS = [
    "import ",
    "__import__",
    "open(",
    "exec(",
    "eval(",
    "compile(",
    "os.",
    "sys.",
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "pathlib",
    "shutil",
    "glob",
    "__builtins__",
    "__globals__",
    "__locals__",
    "getattr(",
    "setattr(",
    "delattr(",
    "vars(",
    "globals(",
    "locals(",
]

EXECUTION_TIMEOUT_SECONDS = 30


class PandasToolInput(BaseModel):
    code: str = Field(description="Python/pandas code to execute against the dataframe 'df'")


class PandasTool(BaseTool):
    """
    Executes pandas code safely against the user's DataFrame.
    
    The agent writes Python code using 'df' as the variable name.
    This tool executes that code in a restricted sandbox and returns
    the result as a string.
    """
    name: str = "pandas_analysis"
    description: str = (
        "Execute Python/pandas code to analyze the dataframe. "
        "The dataframe is available as 'df'. "
        "Use this for: aggregations, groupby, sorting, filtering, calculations. "
        "Always assign your final result to a variable called 'result'. "
        "Example: result = df.groupby('category')['revenue'].sum()"
    )
    args_schema: type[BaseModel] = PandasToolInput

    # The DataFrame is injected before each use
    _df: pd.DataFrame | None = None

    def set_dataframe(self, df: pd.DataFrame) -> None:
        self._df = df

    def _check_security(self, code: str) -> str | None:
        """Returns an error message if code contains blocked patterns."""
        code_lower = code.lower()
        for pattern in BLOCKED_PATTERNS:
            if pattern.lower() in code_lower:
                return f"Security violation: '{pattern}' is not allowed."
        return None

    def _run(self, code: str) -> str:
        if self._df is None:
            return "Error: No dataframe loaded. Upload a dataset first."

        # Security check
        security_error = self._check_security(code)
        if security_error:
            logger.warning(f"Blocked code execution: {security_error}")
            return f"Error: {security_error}"

        result_container: dict[str, Any] = {"result": None, "error": None}

        def execute():
            try:
                # Capture stdout
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()

                # Build restricted namespace
                namespace = {
                    "__builtins__": SAFE_BUILTINS,
                    "df": self._df.copy(),
                    "pd": pd,
                    "np": np,
                    "result": None,
                }

                exec(code, namespace)

                # Capture any printed output
                printed = sys.stdout.getvalue()
                sys.stdout = old_stdout

                # Get the 'result' variable
                raw_result = namespace.get("result")

                if raw_result is None and printed:
                    result_container["result"] = printed.strip()
                elif isinstance(raw_result, pd.DataFrame):
                    result_container["result"] = raw_result.to_string(max_rows=20)
                elif isinstance(raw_result, pd.Series):
                    result_container["result"] = raw_result.to_string(max_rows=20)
                elif raw_result is not None:
                    result_container["result"] = str(raw_result)
                else:
                    result_container["result"] = "Code executed but no result was assigned to 'result' variable."

            except Exception as e:
                sys.stdout = old_stdout if 'old_stdout' in dir() else sys.stdout
                result_container["error"] = f"{type(e).__name__}: {str(e)}"
                logger.error(f"Pandas execution error: {traceback.format_exc()}")

        # Run with timeout
        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
        thread.join(timeout=EXECUTION_TIMEOUT_SECONDS)

        if thread.is_alive():
            return f"Error: Code execution timed out after {EXECUTION_TIMEOUT_SECONDS} seconds."

        if result_container["error"]:
            return f"Error: {result_container['error']}"

        return result_container["result"] or "No result returned."

    async def _arun(self, code: str) -> str:
        return self._run(code)


# Singleton instance — reused across requests, df injected per request
pandas_tool = PandasTool()