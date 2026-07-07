class DataAnalystException(Exception):
    """Base exception for all project errors."""
    def __init__(self, message: str, detail: str = "", error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.detail = detail
        self.error_code = error_code
        super().__init__(message)


class AuthenticationError(DataAnalystException):
    def __init__(self, message: str = "Authentication failed."):
        super().__init__(message, error_code="AUTHENTICATION_ERROR")


class AuthorizationError(DataAnalystException):
    def __init__(self, message: str = "You do not have permission."):
        super().__init__(message, error_code="AUTHORIZATION_ERROR")


class UserAlreadyExistsError(DataAnalystException):
    def __init__(self, email: str):
        super().__init__(
            f"User with email {email} already exists.",
            error_code="USER_ALREADY_EXISTS"
        )


class DatasetNotFoundError(DataAnalystException):
    def __init__(self, dataset_id: str = ""):
        super().__init__(
            "Dataset not found.",
            detail=f"dataset_id={dataset_id}",
            error_code="DATASET_NOT_FOUND"
        )


class InvalidFileError(DataAnalystException):
    def __init__(self, message: str = "Invalid file."):
        super().__init__(message, error_code="INVALID_FILE")


class FileTooLargeError(DataAnalystException):
    def __init__(self, max_mb: int = 50):
        super().__init__(
            f"File exceeds maximum size of {max_mb}MB.",
            error_code="FILE_TOO_LARGE"
        )


class AgentError(DataAnalystException):
    def __init__(self, message: str = "AI agent encountered an error."):
        super().__init__(message, error_code="AGENT_ERROR")


class MLModelError(DataAnalystException):
    def __init__(self, message: str = "ML model failed."):
        super().__init__(message, error_code="ML_MODEL_ERROR")


class ReportGenerationError(DataAnalystException):
    def __init__(self, message: str = "Report generation failed."):
        super().__init__(message, error_code="REPORT_GENERATION_ERROR")
