from fastapi.testclient import TestClient
import pytest

from app.core.exceptions import DatabaseConnectionError
from app.routers import health as health_router


def test_health_check_status_http_200(client: TestClient) -> None:
    """Verifica se /health responde HTTP 200 quando o banco está ativo."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_response_structure_and_headers(
    client: TestClient,
) -> None:
    """Verifica a estrutura do JSON de saúde e os cabeçalhos do middleware."""
    response = client.get("/health")
    body = response.json()

    assert body == {
        "status": "ok",
        "database": "connected",
    }
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers


def test_health_check_database_unavailable_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica se falha na conexão retorna HTTP 503 padronizado."""

    def _raise_db_error() -> bool:
        raise DatabaseConnectionError(
            "Banco de dados indisponível no momento."
        )

    monkeypatch.setattr(
        health_router, "check_database_connection", _raise_db_error
    )

    response = client.get("/health")
    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert body["error"]["message"] == (
        "Banco de dados indisponível no momento."
    )
