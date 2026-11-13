<<<<<<< Updated upstream
import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
=======
from fastapi import APIRouter
>>>>>>> Stashed changes

from app.core.database import check_database_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check():
<<<<<<< Updated upstream
    try:
        check_database_connection()
        return {
            "status": "ok",
            "database": "connected",
        }
    except DatabaseConnectionError:
        logger.exception("Database health check failed")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "database": "disconnected",
                "detail": "Erro ao conectar com o banco de dados.",
            },
        )
=======
    check_database_connection()
    return {
        "status": "ok",
        "database": "connected",
    }
>>>>>>> Stashed changes
