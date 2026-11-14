import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.database import check_database_connection
from app.core.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
def health_check():
    try:
        check_database_connection()
        return {
            "status": "ok",
            "database": "connected",
        }
    except DatabaseConnectionError as exc:
        logger.exception("Database health check failed")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "database": "disconnected",
                "detail": exc.message,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )
