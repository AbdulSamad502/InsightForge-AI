from typing import TypedDict, Any


class ReportState(TypedDict):
    """
    Shared state passed between all nodes in the report LangGraph pipeline.
    Each node reads from and writes to this state.
    """
    # Input (set before graph runs)
    dataset_id: str
    user_id: str
    session_id: str | None      # optional: pull insights from a specific session
    report_id: str              # the DB record ID to update when done

    # Populated by gather_insights node
    chat_messages: list[dict]   # last 20 messages from chat history
    dataset_info: dict          # row_count, col_count, filename, columns

    # Populated by check_ml node
    ml_results: list[dict]      # ML results if exist for this dataset

    # Populated by generate_charts node
    chart_paths: list[str]      # absolute paths to exported PNG files

    # Populated by write_summary node
    summary_text: str           # LLM-generated executive summary
    key_insights: list[str]     # top 5 business insights from chat
    recommendations: list[str]  # top 3 recommendations

    # Populated by compile_pdf node
    pdf_path: str               # absolute path to final PDF

    # Error handling
    error: str | None           # set if any node fails
    status: str                 # "running" | "complete" | "failed"