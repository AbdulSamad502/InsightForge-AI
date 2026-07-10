"""
Security tests for the pandas sandbox.
These tests verify that malicious code is blocked
and safe code executes correctly.
"""
import pandas as pd
import pytest
from app.ai.tools.pandas_tool import PandasTool


@pytest.fixture
def tool_with_df():
    """PandasTool with a sample DataFrame loaded."""
    tool = PandasTool()
    df = pd.DataFrame({
        "product":  ["Laptop", "Phone", "Chair"],
        "revenue":  [45000, 25000, 8000],
        "quantity": [2, 5, 3],
        "category": ["Electronics", "Electronics", "Furniture"],
    })
    tool.set_dataframe(df)
    return tool


# ════════════════════════════════════════════════════════════
# SECURITY TESTS — these must BLOCK dangerous code
# ════════════════════════════════════════════════════════════

def test_blocks_import_os(tool_with_df):
    """Should block 'import os' attempts."""
    result = tool_with_df._run("import os; result = os.listdir('.')")
    assert "Error" in result or "Security" in result


def test_blocks_import_sys(tool_with_df):
    """Should block 'import sys' attempts."""
    result = tool_with_df._run("import sys; result = sys.path")
    assert "Error" in result or "Security" in result


def test_blocks_open_file(tool_with_df):
    """Should block file reading attempts."""
    result = tool_with_df._run("result = open('.env').read()")
    assert "Error" in result or "Security" in result


def test_blocks_exec(tool_with_df):
    """Should block nested exec() calls."""
    result = tool_with_df._run("exec('import os')")
    assert "Error" in result or "Security" in result


def test_blocks_eval(tool_with_df):
    """Should block eval() calls."""
    result = tool_with_df._run("result = eval('1+1')")
    assert "Error" in result or "Security" in result


def test_blocks_subprocess(tool_with_df):
    """Should block subprocess attempts."""
    result = tool_with_df._run("import subprocess; result = subprocess.run(['ls'])")
    assert "Error" in result or "Security" in result


def test_blocks_dunder_import(tool_with_df):
    """Should block __import__ attempts."""
    result = tool_with_df._run("os = __import__('os'); result = os.getcwd()")
    assert "Error" in result or "Security" in result


def test_blocks_globals_access(tool_with_df):
    """Should block access to globals()."""
    result = tool_with_df._run("result = globals()")
    assert "Error" in result or "Security" in result


# ════════════════════════════════════════════════════════════
# SAFE EXECUTION TESTS — these must SUCCEED
# ════════════════════════════════════════════════════════════

def test_allows_groupby_sum(tool_with_df):
    """Should allow basic groupby operations."""
    result = tool_with_df._run(
        "result = df.groupby('category')['revenue'].sum()"
    )
    assert "Error" not in result
    assert "Electronics" in result or "Furniture" in result


def test_allows_describe(tool_with_df):
    """Should allow df.describe()."""
    result = tool_with_df._run("result = df.describe()")
    assert "Error" not in result
    assert "revenue" in result


def test_allows_sorting(tool_with_df):
    """Should allow sorting operations."""
    result = tool_with_df._run(
        "result = df.sort_values('revenue', ascending=False).head(3)"
    )
    assert "Error" not in result
    assert "Laptop" in result


def test_allows_filtering(tool_with_df):
    """Should allow dataframe filtering."""
    result = tool_with_df._run(
        "result = df[df['category'] == 'Electronics']['revenue'].sum()"
    )
    assert "Error" not in result
    assert "70000" in result


def test_allows_value_counts(tool_with_df):
    """Should allow value_counts()."""
    result = tool_with_df._run("result = df['category'].value_counts()")
    assert "Error" not in result
    assert "Electronics" in result


def test_allows_arithmetic(tool_with_df):
    """Should allow basic arithmetic."""
    result = tool_with_df._run(
        "total = df['revenue'].sum()\nresult = f'Total: {total}'"
    )
    assert "Error" not in result
    assert "78000" in result


def test_no_dataframe_returns_error(tool_with_df):
    """Should handle no dataframe gracefully."""
    empty_tool = PandasTool()
    result = empty_tool._run("result = df.head()")
    assert "Error" in result


def test_missing_result_variable(tool_with_df):
    """Should handle missing 'result' variable gracefully."""
    result = tool_with_df._run("x = df.head()")
    # Should not crash — returns informative message
    assert result is not None
    assert len(result) > 0
