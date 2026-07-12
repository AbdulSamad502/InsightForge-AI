import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


def run_report_task(
    report_id: str,
    dataset_id: str,
    user_id: str,
    session_id: str | None,
    db_url: str,
) -> None:
    logger.info(f"BACKGROUND TASK STARTED FOR REPORT {report_id}")
    """
    Background task: run the full LangGraph report pipeline.
    Creates its own DB session (request session is already closed).
    """


    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.modules.reports.repository import (
            update_report_running, update_report_complete, update_report_failed
        )
        from app.ai.graph.report_graph import report_pipeline
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        logger.info(f"DB SESSION CREATED {report_id}")

        logger.info(f"BEFORE UPDATE RUNNING {report_id}")

        update_report_running(db, report_id)

        logger.info(f"AFTER UPDATE RUNNING {report_id}")
        logger.info(f"REPORT STATUS RUNNING {report_id}")

        db.close()

        logger.info(f"DB CLOSED BEFORE LANGGRAPH {report_id}")

        # Build initial state
        initial_state = {
            "dataset_id": dataset_id,
            "user_id": user_id,
            "session_id": session_id,
            "report_id": report_id,
            "chat_messages": [],
            "dataset_info": {},
            "ml_results": [],
            "chart_paths": [],
            "summary_text": "",
            "key_insights": [],
            "recommendations": [],
            "pdf_path": "",
            "error": None,
            "status": "running",
        }

        logger.info(f"STARTING LANGGRAPH {report_id}")

        final_state = report_pipeline.invoke(initial_state)

        logger.info(f"LANGGRAPH FINISHED {report_id}")

        db = SessionLocal()

        if final_state.get("status") == "complete" and final_state.get("pdf_path"):
            update_report_complete(
                db,
                report_id,
                final_state["pdf_path"]
            )
            logger.info(
                f"Report complete: {report_id} → {final_state['pdf_path']}"
            )

        else:
            error = final_state.get(
                "error",
                "Pipeline completed with unknown status"
            )

            update_report_failed(
                db,
                report_id,
                error
            )

            logger.error(
                f"Report failed: {report_id} → {error}"
            )

    except Exception as e:
        logger.error(f"Report task crashed: {report_id} → {e}", exc_info=True)
        try:
            db2 = SessionLocal()
            update_report_failed(db2, report_id, str(e))
            db2.close()
        except Exception:
            pass
    finally:
        try:
            if db:
                db.close()
        except Exception:
            pass