from enum import Enum


class IntentType(str, Enum):
    ANALYTICS = "analytics"
    VISUALIZATION = "visualization"
    FORECAST = "forecast"
    ANOMALY = "anomaly"
    CHURN = "churn"
    GENERAL = "general"


class FileType(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"


class DatasetStatus(str, Enum):
    UPLOADED = "uploaded"
    PROFILED = "profiled"
    CLEANED = "cleaned"


class MLModelType(str, Enum):
    FORECAST = "forecast"
    ANOMALY = "anomaly"
    CHURN = "churn"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


# Limits
MAX_CHAT_HISTORY = 10
MAX_SUGGESTIONS = 5
MAX_REPORT_CHARTS = 5
MAX_PREVIEW_ROWS = 50
