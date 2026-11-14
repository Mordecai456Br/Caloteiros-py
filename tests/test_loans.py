import uuid

from fastapi.testclient import TestClient


# ==========================================
# POST /loans
# ==========================================
def test_create_loan_valid(client: TestClient, created_loan_request: dict) -> None:
    response = client.post(
        "/loans",
        json={
            "loan_request_id": created_loan_request["id"],
            "principal_amount": "1000.00",
            "total_to_receive": "1150.00",
            "load_date": "2026-11-14",
            "installment_count": 2,
            "first_due_date": "2026-12-14",
            "notes": "Contrato assinado",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["loan_request_id"] == created_loan_request["id"]
    assert float(data["principal_amount"]) == 1000.00
    assert float(data["total_to_receive"]) == 1150.00
    assert float(data["amount_received"]) == 0.00
    assert data["status"] == "open"


def test_create_loan_invalid_zero_or_negative_amount(
    client: TestClient, created_loan_request: dict
) -> None:
    response = client.post(
        "/loans",
        json={
            "loan_request_id": created_loan_request["id"],
            "principal_amount": "0.00",
            "total_to_receive": "-500.00",
            "load_date": "2026-11-14",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_loan_nonexistent_loan_request(client: TestClient) -> None:
    response = client.post(
        "/loans",
        json={
            "loan_request_id": str(uuid.uuid4()),
            "principal_amount": "1000.00",
            "total_to_receive": "1100.00",
            "load_date": "2026-11-14",
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_create_duplicate_loan_for_same_request_returns_409(
    client: TestClient, created_loan_request: dict
) -> None:
    payload = {
        "loan_request_id": created_loan_request["id"],
        "principal_amount": "1000.00",
        "total_to_receive": "1100.00",
        "load_date": "2026-11-14",
    }
    first = client.post("/loans", json=payload)
    assert first.status_code == 201

    duplicate = client.post("/loans", json=payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "RESOURCE_CONFLICT"


# ==========================================
# GET /loans e GET /loans/{loan_id}
# ==========================================
def test_list_loans_and_filter_by_status_active(
    client: TestClient, created_loan_request: dict
) -> None:
    client.patch(f"/loan-requests/{created_loan_request['id']}/approve")

    active_resp = client.get("/loans?status=active")
    assert active_resp.status_code == 200
    assert active_resp.json()["pagination"]["total"] == 1
    assert active_resp.json()["items"][0]["status"] == "open"


def test_list_loans_filter_by_amount_range_and_validation(
    client: TestClient, created_loan_request: dict
) -> None:
    client.patch(f"/loan-requests/{created_loan_request['id']}/approve")

    in_range = client.get("/loans?min_amount=500&max_amount=1500")
    assert in_range.status_code == 200
    assert in_range.json()["pagination"]["total"] == 1

    out_of_range = client.get("/loans?min_amount=2000&max_amount=3000")
    assert out_of_range.status_code == 200
    assert out_of_range.json()["pagination"]["total"] == 0

    invalid_range = client.get("/loans?min_amount=3000&max_amount=500")
    assert invalid_range.status_code == 422
    assert invalid_range.json()["error"]["code"] == "VALIDATION_ERROR"


def test_get_loan_by_id_found_and_not_found(
    client: TestClient, created_loan_request: dict
) -> None:
    client.patch(f"/loan-requests/{created_loan_request['id']}/approve")
    loan_id = client.get("/loans").json()["items"][0]["id"]

    found = client.get(f"/loans/{loan_id}")
    assert found.status_code == 200
    assert found.json()["id"] == loan_id

    not_found = client.get(f"/loans/{uuid.uuid4()}")
    assert not_found.status_code == 404
    assert not_found.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
