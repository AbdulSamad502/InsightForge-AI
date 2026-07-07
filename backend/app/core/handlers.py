import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DataAnalystException,
    DatasetNotFoundError,
    FileTooLargeError,
    InvalidFileError,
    UserAlreadyExistsError,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=401,
            content={
                "error": True,
                "error_code": exc.error_code,
                "message": exc.message,
                "request_id": getattr(request.state, "request_id", ""),
            },
        )

    @app.exception_handler(AuthorizationError)
    async def authz_error_handler(request: Request, exc: AuthorizationError):
        return JSONResponse(
            status_code=403,
            content={
                "error": True,
                "error_code": exc.error_code,
                "message": exc.message,
                "request_id": getattr(request.state, "request_id", ""),
            },
        )

    @app.exception_handler(UserAlreadyExistsError)
    async def user_exists_handler(request: Request, exc: UserAlreadyExistsError):
        return JSONResponse(
            status_code=409,
            content={
                "error": True,
                "error_code": exc.error_code,
                "message": exc.message,
                "request_id": getattr(request.state, "request_id", ""),
            },
        )

    @app.exception_handler(DatasetNotFoundError)
    async def dataset_not_found_handler(request: Request, exc: DatasetNotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                "error": True,
                "error_code": exc.error_code,
                "message": exc.message,
                "request_id": getattr(request.state, "request_id", ""),
            },
        )

    @app.exception_handler(InvalidFileError)
    async def invalid_file_handler(request: Request, exc: InvalidFileError):
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "error_code": exc.error_code,
                "message": exc.message,
                "request_id": getattr(request.state, "request_id", ""),
            },
        )

    @app.exception_handler(FileTooLargeError)
    async def file_too_large_handler(request: Request, exc: FileTooLargeError):
        return JSONResponse(
            status_code=413,
            content={
                "error": True,
                "error_code": exc.error_code,
                "message": exc.message,
                "request_id": getattr(request.state, "request_id", ""),
            },
        )

    @app.exception_handler(DataAnalystException)
    async def generic_handler(request: Request, exc: DataAnalystException):
        logger.error(f"Unhandled DataAnalystException: {exc.detail or exc.message}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "error_code": exc.error_code,
                "message": exc.message,
                "request_id": getattr(request.state, "request_id", ""),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "request_id": getattr(request.state, "request_id", ""),
            },
        )
