from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status
from src.clients.exceptions import (
    RiotKeyExpiredError,
    RiotRateLimitException,
    RiotServiceUnavailableException,
)


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(RiotKeyExpiredError)
    async def riot_key_expired_handler(
        request: Request, exc: RiotKeyExpiredError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": exc.error_code,
                "detail": exc.message,
            },
        )

    @app.exception_handler(RiotRateLimitException)
    async def riot_rate_limit_handler(
        request: Request, exc: RiotRateLimitException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": exc.error_code,
                "detail": exc.message,
            },
        )

    @app.exception_handler(RiotServiceUnavailableException)
    async def riot_service_unavailable_handler(
        request: Request, exc: RiotServiceUnavailableException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": exc.error_code,
                "detail": exc.message,
            }
        )
