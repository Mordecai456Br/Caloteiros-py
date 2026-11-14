from collections.abc import Generator
from datetime import date
from decimal import Decimal
import os
import uuid

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.core.database import Base, get_db
from app.main import app
from app.routers import health as health_router

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

if TEST_DATABASE_URL.startswith("sqlite"):
    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def _configure_sqlite(dbapi_connection, connection_record) -> None:
        dbapi_connection.create_function(
            "gen_random_uuid", 0, lambda: str(uuid.uuid4())
        )
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(autouse=True)
def setup_test_database(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None, None, None]:
    """Recria as tabelas em um banco isolado antes de cada teste."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    monkeypatch.setattr(
        health_router, "check_database_connection", lambda: True
    )
    monkeypatch.setattr("app.main.check_database_connection", lambda: True)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def created_user(client: TestClient) -> dict:
    response = client.post(
        "/users",
        json={
            "name": "Maria Silva",
            "phone": "11988887777",
            "email": "maria@teste.com",
            "notes": "Cliente confiável",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def created_loan_request(client: TestClient, created_user: dict) -> dict:
    response = client.post(
        "/loan-requests",
        json={
            "user_id": created_user["id"],
            "request_amount": str(Decimal("1000.00")),
            "pix_key": "11988887777",
            "installment_count": 2,
            "first_due_date": str(date(2026, 12, 10)),
            "description": "Empréstimo pessoal",
        },
    )
    assert response.status_code == 201
    return response.json()
