from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.database import check_database_connection
from app.core.exceptions import DatabaseConnectionError

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
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "database": "disconnected",
                "detail": exc.message,
            },
        )
