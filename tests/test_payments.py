from fastapi.testclient import TestClient


# ==========================================
# POST /payments (Total, Parcial e Acima do Saldo)
# ==========================================
def test_create_partial_payment_updates_installment_and_loan_to_in_progress(
    client: TestClient, created_loan_request: dict
) -> None:
    client.patch(
        f"/loan-requests/{created_loan_request['id']}/approve",
        json={"total_to_receive": "1000.00", "installment_count": 2},
    )
    installments = client.get("/installments").json()["items"]
    first_inst = installments[0]

    pay_resp = client.post(
        "/payments",
        json={
            "installment_id": first_inst["id"],
            "amount": "200.00",
            "receipt_key": "PIX-PARCIAL-01",
            "sender_pix_key": "11988887777",
            "description": "Pagamento parcial",
        },
    )
    assert pay_resp.status_code == 201
    assert float(pay_resp.json()["amount"]) == 200.00

    updated_inst = client.get(f"/installments/{first_inst['id']}").json()
    assert updated_inst["status"] == "partially_paid"

    updated_loan = client.get(f"/loans/{first_inst['loan_id']}").json()
    assert float(updated_loan["amount_received"]) == 200.00
    assert updated_loan["status"] == "in progress"


def test_create_full_payment_marks_installment_and_loan_as_paid(
    client: TestClient, created_loan_request: dict
) -> None:
    client.patch(
        f"/loan-requests/{created_loan_request['id']}/approve",
        json={"total_to_receive": "1000.00", "installment_count": 2},
    )
    installments = client.get("/installments").json()["items"]

    for inst in installments:
        resp = client.post(
            "/payments",
            json={
                "installment_id": inst["id"],
                "amount": "500.00",
                "receipt_key": f"PIX-TOTAL-{inst['number']}",
                "sender_pix_key": "11988887777",
            },
        )
        assert resp.status_code == 201
        updated_inst = client.get(f"/installments/{inst['id']}").json()
        assert updated_inst["status"] == "paid"

    loan = client.get(f"/loans/{installments[0]['loan_id']}").json()
    assert float(loan["amount_received"]) == 1000.00
    assert loan["status"] == "paid"


def test_create_payment_above_installment_balance_returns_422(
    client: TestClient, created_loan_request: dict
) -> None:
    client.patch(
        f"/loan-requests/{created_loan_request['id']}/approve",
        json={"total_to_receive": "1000.00", "installment_count": 2},
    )
    first_inst = client.get("/installments").json()["items"][0]

    # Parcela é de 500.00; tentar pagar 600.00 deve violar regra de negócio
    overpay_resp = client.post(
        "/payments",
        json={
            "installment_id": first_inst["id"],
            "amount": "600.00",
            "receipt_key": "PIX-ACIMA",
            "sender_pix_key": "11988887777",
        },
    )
    assert overpay_resp.status_code == 422
    assert overpay_resp.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


# ==========================================
# GET /payments e DELETE /payments/{payment_id}
# ==========================================
def test_list_and_delete_payment_reverts_installment_and_loan_status(
    client: TestClient, created_loan_request: dict
) -> None:
    client.patch(
        f"/loan-requests/{created_loan_request['id']}/approve",
        json={"total_to_receive": "1000.00", "installment_count": 2},
    )
    first_inst = client.get("/installments").json()["items"][0]

    payment = client.post(
        "/payments",
        json={
            "installment_id": first_inst["id"],
            "amount": "500.00",
            "receipt_key": "PIX-ESTORNO",
            "sender_pix_key": "11988887777",
        },
    ).json()

    list_resp = client.get(f"/payments?loan_id={first_inst['loan_id']}")
    assert list_resp.status_code == 200
    assert list_resp.json()["pagination"]["total"] == 1

    del_resp = client.delete(f"/payments/{payment['id']}")
    assert del_resp.status_code == 204

    reverted_inst = client.get(f"/installments/{first_inst['id']}").json()
    assert reverted_inst["status"] == "open"

    reverted_loan = client.get(f"/loans/{first_inst['loan_id']}").json()
    assert float(reverted_loan["amount_received"]) == 0.00
    assert reverted_loan["status"] == "open"
