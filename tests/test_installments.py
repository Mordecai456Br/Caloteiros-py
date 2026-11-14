from datetime import date, timedelta

from fastapi.testclient import TestClient


# ==========================================
# GET /installments (Listagem e Filtros)
# ==========================================
def test_list_installments_returns_generated_installments(
    client: TestClient, created_loan_request: dict
) -> None:
    client.patch(
        f"/loan-requests/{created_loan_request['id']}/approve",
        json={"total_to_receive": "1000.00", "installment_count": 2},
    )

    response = client.get("/installments")
    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total"] == 2
    assert [item["number"] for item in body["items"]] == [1, 2]
    assert all(item["status"] == "open" for item in body["items"])


def test_list_installments_filter_by_status_pending_and_overdue(
    client: TestClient, created_user: dict
) -> None:
    past_due = str(date.today() - timedelta(days=10))
    req = client.post(
        "/loan-requests",
        json={
            "user_id": created_user["id"],
            "request_amount": "500.00",
            "pix_key": "pix-atraso",
            "installment_count": 1,
            "first_due_date": past_due,
        },
    ).json()
    client.patch(f"/loan-requests/{req['id']}/approve")

    pending_resp = client.get("/installments?status=pending")
    assert pending_resp.status_code == 200
    assert pending_resp.json()["pagination"]["total"] == 1

    overdue_resp = client.get("/installments?status=overdue")
    assert overdue_resp.status_code == 200
    assert overdue_resp.json()["pagination"]["total"] == 1
    assert overdue_resp.json()["items"][0]["due_date"] == past_due


def test_list_installments_filter_by_due_date_range(
    client: TestClient, created_loan_request: dict
) -> None:
    client.patch(
        f"/loan-requests/{created_loan_request['id']}/approve",
        json={
            "total_to_receive": "1000.00",
            "installment_count": 2,
            "first_due_date": "2026-12-10",
        },
    )

    dec_only = client.get(
        "/installments?start_date=2026-12-01&end_date=2026-12-31"
    )
    assert dec_only.status_code == 200
    assert dec_only.json()["pagination"]["total"] == 1
    assert dec_only.json()["items"][0]["due_date"] == "2026-12-10"


# ==========================================
# PATCH /installments/{installment_id}
# ==========================================
def test_update_installment_amount_recalculates_loan_total(
    client: TestClient, created_loan_request: dict
) -> None:
    client.patch(
        f"/loan-requests/{created_loan_request['id']}/approve",
        json={"total_to_receive": "1000.00", "installment_count": 2},
    )
    installments = client.get("/installments").json()["items"]
    first_inst = installments[0]

    patch_resp = client.patch(
        f"/installments/{first_inst['id']}",
        json={"amount": "650.00", "due_date": "2026-12-20"},
    )
    assert patch_resp.status_code == 200
    assert float(patch_resp.json()["amount"]) == 650.00
    assert patch_resp.json()["due_date"] == "2026-12-20"

    loan = client.get(f"/loans/{first_inst['loan_id']}").json()
    assert float(loan["total_to_receive"]) == 1150.00


def test_update_installment_amount_less_than_paid_returns_422(
    client: TestClient, created_loan_request: dict
) -> None:
    client.patch(
        f"/loan-requests/{created_loan_request['id']}/approve",
        json={"total_to_receive": "1000.00", "installment_count": 2},
    )
    first_inst = client.get("/installments").json()["items"][0]

    client.post(
        "/payments",
        json={
            "installment_id": first_inst["id"],
            "amount": "300.00",
            "receipt_key": "COMP-300",
            "sender_pix_key": "11988887777",
        },
    )

    resp = client.patch(
        f"/installments/{first_inst['id']}",
        json={"amount": "200.00"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"
