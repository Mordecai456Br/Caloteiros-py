from contextlib import asynccontextmanager
import logging
import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.core.database import check_database_connection
from app.core.exceptions import DatabaseConnectionError
from app.routers import health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        check_database_connection()
        logger.info("Conexão com o banco de dados Supabase estabelecida com sucesso!")
    except DatabaseConnectionError as exc:
        logger.error(f"Não foi possível conectar ao banco na inicialização: {exc.message}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.include_router(health.router)


@app.get("/", tags=["Root"])
def root():
    return {"message": f"{settings.APP_NAME} está rodando!"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

