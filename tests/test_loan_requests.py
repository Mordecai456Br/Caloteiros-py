import uuid

from fastapi.testclient import TestClient


# ==========================================
# POST /loan-requests
# ==========================================
def test_create_loan_request_success(client: TestClient, created_user: dict) -> None:
    response = client.post(
        "/loan-requests",
        json={
            "user_id": created_user["id"],
            "request_amount": "1500.00",
            "pix_key": "maria@pix.com",
            "installment_count": 3,
            "first_due_date": "2026-12-15",
            "description": "Compra de equipamento",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == created_user["id"]
    assert float(data["request_amount"]) == 1500.00
    assert data["status"] == "pending"
    assert data["approved_at"] is None
    assert data["denied_at"] is None


def test_create_loan_request_missing_required_fields_or_negative_amount(
    client: TestClient, created_user: dict
) -> None:
    missing_resp = client.post(
        "/loan-requests",
        json={"user_id": created_user["id"]},
    )
    assert missing_resp.status_code == 422
    assert missing_resp.json()["error"]["code"] == "VALIDATION_ERROR"

    negative_resp = client.post(
        "/loan-requests",
        json={
            "user_id": created_user["id"],
            "request_amount": "-100.00",
            "pix_key": "chave-pix",
        },
    )
    assert negative_resp.status_code == 422
    assert negative_resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_loan_request_nonexistent_user(client: TestClient) -> None:
    response = client.post(
        "/loan-requests",
        json={
            "user_id": str(uuid.uuid4()),
            "request_amount": "500.00",
            "pix_key": "11999990000",
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


# ==========================================
# GET /loan-requests (Listagem e Filtros)
# ==========================================
def test_list_loan_requests_returns_paginated_items(
    client: TestClient, created_loan_request: dict
) -> None:
    response = client.get("/loan-requests")
    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total"] == 1
    assert body["items"][0]["id"] == created_loan_request["id"]


def test_list_loan_requests_filter_by_status(
    client: TestClient, created_user: dict, created_loan_request: dict
) -> None:
    second = client.post(
        "/loan-requests",
        json={
            "user_id": created_user["id"],
            "request_amount": "800.00",
            "pix_key": "pix2",
        },
    ).json()
    client.patch(f"/loan-requests/{second['id']}/deny")

    pending = client.get("/loan-requests?status=pending")
    assert pending.status_code == 200
    assert pending.json()["pagination"]["total"] == 1
    assert pending.json()["items"][0]["id"] == created_loan_request["id"]

    denied = client.get("/loan-requests?status=denied")
    assert denied.status_code == 200
    assert denied.json()["pagination"]["total"] == 1
    assert denied.json()["items"][0]["id"] == second["id"]


def test_list_loan_requests_filter_by_date_range(
    client: TestClient, created_loan_request: dict
) -> None:
    valid = client.get("/loan-requests?start_date=2020-01-01&end_date=2030-12-31")
    assert valid.status_code == 200
    assert valid.json()["pagination"]["total"] == 1

    invalid = client.get("/loan-requests?start_date=2026-12-31&end_date=2026-01-01")
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"


# ==========================================
# PATCH /loan-requests/{id}/approve e /deny
# ==========================================
def test_approve_loan_request_creates_loan_and_installments_automatically(
    client: TestClient, created_loan_request: dict
) -> None:
    req_id = created_loan_request["id"]
    response = client.patch(
        f"/loan-requests/{req_id}/approve",
        json={"total_to_receive": "1200.00"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["approved_at"] is not None

    # Verifica que o Loan foi criado automaticamente com status 'open'
    loans_resp = client.get("/loans")
    assert loans_resp.status_code == 200
    loans = loans_resp.json()["items"]
    assert len(loans) == 1
    assert loans[0]["loan_request_id"] == req_id
    assert loans[0]["status"] == "open"
    assert float(loans[0]["total_to_receive"]) == 1200.00

    # Verifica que as 2 parcelas foram geradas automaticamente
    inst_resp = client.get(f"/installments?loan_id={loans[0]['id']}")
    assert inst_resp.status_code == 200
    installments = inst_resp.json()["items"]
    assert len(installments) == 2
    assert float(installments[0]["amount"]) == 600.00
    assert float(installments[1]["amount"]) == 600.00


def test_approve_nonexistent_loan_request_returns_404(client: TestClient) -> None:
    response = client.patch(f"/loan-requests/{uuid.uuid4()}/approve")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_approve_already_denied_loan_request_returns_422(
    client: TestClient, created_loan_request: dict
) -> None:
    req_id = created_loan_request["id"]
    deny_resp = client.patch(f"/loan-requests/{req_id}/deny")
    assert deny_resp.status_code == 200
    assert deny_resp.json()["status"] == "denied"

    approve_resp = client.patch(f"/loan-requests/{req_id}/approve")
    assert approve_resp.status_code == 422
    assert approve_resp.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"
