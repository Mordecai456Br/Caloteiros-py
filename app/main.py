from contextlib import asynccontextmanager
import logging
import time
import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

from app.core.config import settings
from app.core.database import check_database_connection
from app.core.exceptions import AppException, DatabaseConnectionError
from app.routers import (
    health,
    installments,
    loan_requests,
    loans,
    payments,
    users,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HTTP_STATUS_CODE_MAP = {
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "RESOURCE_NOT_FOUND",
    409: "RESOURCE_CONFLICT",
    422: "VALIDATION_ERROR",
    503: "DATABASE_UNAVAILABLE",
}


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: object = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
            }
        },
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        check_database_connection()
        logger.info("Conexão com o banco Supabase estabelecida com sucesso!")
    except DatabaseConnectionError as exc:
        logger.error(
            "Não foi possível conectar ao banco na inicialização: %s",
            exc.message,
        )
    yield


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
    logger.info(
        "[%s] %s %s -> %s (%.2fms)",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request, exc: AppException
) -> JSONResponse:
    return _error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code = HTTP_STATUS_CODE_MAP.get(exc.status_code, "HTTP_ERROR")
    message = (
        exc.detail if isinstance(exc.detail, str) else "Erro na requisição."
    )
    details = exc.detail if not isinstance(exc.detail, str) else None
    return _error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
        details=details,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    sanitized_errors = [
        {
            "field": ".".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg", "Valor inválido."),
            "type": err.get("type", "value_error"),
        }
        for err in exc.errors()
    ]
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="VALIDATION_ERROR",
        message="Dados de entrada inválidos.",
        details=sanitized_errors,
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    logger.warning("IntegrityError capturado: %s", exc)
    return _error_response(
        status_code=status.HTTP_409_CONFLICT,
        code="RESOURCE_CONFLICT",
        message="Conflito de integridade ao processar os dados.",
        details=None,
    )


@app.exception_handler(OperationalError)
async def operational_error_handler(
    request: Request, exc: OperationalError
) -> JSONResponse:
    logger.error("OperationalError no banco de dados: %s", exc)
    return _error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code="DATABASE_UNAVAILABLE",
        message="Banco de dados indisponível no momento.",
        details=None,
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    logger.error("Erro de banco de dados: %s", exc)
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="Erro interno ao processar operação no banco de dados.",
        details=None,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception("Erro inesperado não tratado: %s", exc)
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="Ocorreu um erro interno inesperado.",
        details=None,
    )


app.include_router(health.router)
app.include_router(users.router)
app.include_router(loan_requests.router)
app.include_router(loans.router)
app.include_router(installments.router)
app.include_router(payments.router)


@app.get("/", tags=["Root"])
def root():
    return {"message": f"{settings.APP_NAME} está rodando!"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
