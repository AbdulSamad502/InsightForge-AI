import json
import logging
import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session

from app.modules.ml import repository
from app.modules.ml.engines.forecast import ForecastEngine
from app.modules.ml.engines.anomaly import AnomalyEngine
from app.modules.ml.engines.churn import ChurnEngine
from app.modules.datasets.repository import get_dataset_by_id
from app.core.exceptions import DatasetNotFoundError, MLModelError

logger = logging.getLogger(__name__)


def _load_df(dataset_id: str, user_id: str, db: Session) -> pd.DataFrame:
    """Load dataset file into a DataFrame."""
    dataset = get_dataset_by_id(db, dataset_id)
    if not dataset or dataset.user_id != user_id:
        raise DatasetNotFoundError(dataset_id)
    file_path = Path(dataset.file_path)
    if not file_path.exists():
        raise DatasetNotFoundError(dataset_id)
    if dataset.file_type == "csv":
        return pd.read_csv(file_path, low_memory=False)
    return pd.read_excel(file_path, engine="openpyxl")


# ── Background task functions ──────────────────────────────
# These are called by FastAPI BackgroundTasks — they run AFTER
# the HTTP response is sent (202 Accepted).
# They get their own DB session since the request session is closed.

def run_forecast_task(
    task_id: str,
    dataset_id: str,
    user_id: str,
    target_column: str,
    date_column: str | None,
    n_periods: int,
    db_url: str,
) -> None:
    """Background task: train forecast model and save results."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        repository.update_result_running(db, task_id)

        df = _load_df(dataset_id, user_id, db)

        engine_obj = ForecastEngine()
        train_metrics = engine_obj.fit(df, target_column, date_column)
        predictions = engine_obj.predict(n_periods)
        chart_json = engine_obj.get_chart(predictions)

        result_data = {**train_metrics, **predictions}
        chart_dict = json.loads(chart_json) if chart_json and chart_json != "{}" else None

        repository.update_result_complete(db, task_id, result_data, chart_dict)
        logger.info(f"Forecast task complete: {task_id}")

    except Exception as e:
        logger.error(f"Forecast task failed {task_id}: {e}", exc_info=True)
        repository.update_result_failed(db, task_id, str(e))
    finally:
        db.close()


def run_anomaly_task(
    task_id: str,
    dataset_id: str,
    user_id: str,
    target_column: str,
    db_url: str,
) -> None:
    """Background task: run anomaly detection and save results."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        repository.update_result_running(db, task_id)

        df = _load_df(dataset_id, user_id, db)

        engine_obj = AnomalyEngine()
        engine_obj.fit_predict(df, target_column)
        summary = engine_obj.get_summary()
        chart_json = engine_obj.get_chart()

        chart_dict = json.loads(chart_json) if chart_json and chart_json != "{}" else None
        repository.update_result_complete(db, task_id, summary, chart_dict)
        logger.info(f"Anomaly task complete: {task_id}")

    except Exception as e:
        logger.error(f"Anomaly task failed {task_id}: {e}", exc_info=True)
        repository.update_result_failed(db, task_id, str(e))
    finally:
        db.close()


def run_churn_task(
    task_id: str,
    dataset_id: str,
    user_id: str,
    target_column: str,
    db_url: str,
) -> None:
    """Background task: train churn model and save results."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        repository.update_result_running(db, task_id)

        df = _load_df(dataset_id, user_id, db)

        engine_obj = ChurnEngine()
        train_metrics = engine_obj.fit(df, target_column)
        segments = engine_obj.predict_segments(df)
        feature_importance = engine_obj.get_feature_importance()
        chart_json = engine_obj.get_chart()

        result_data = {
            **train_metrics,
            "top_at_risk_customers": segments[:10],
            "feature_importance": feature_importance,
        }
        chart_dict = json.loads(chart_json) if chart_json and chart_json != "{}" else None

        repository.update_result_complete(db, task_id, result_data, chart_dict)
        logger.info(f"Churn task complete: {task_id}")

    except Exception as e:
        logger.error(f"Churn task failed {task_id}: {e}", exc_info=True)
        repository.update_result_failed(db, task_id, str(e))
    finally:
        db.close()