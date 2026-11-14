import uuid

from fastapi.testclient import TestClient


# ==========================================
# POST /users (Cadastro)
# ==========================================
def test_create_user_valid(client: TestClient) -> None:
    response = client.post(
        "/users",
        json={
            "name": "João Souza",
            "phone": "11977776666",
            "email": "joao@email.com",
            "notes": "Primeiro cadastro",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "João Souza"
    assert data["phone"] == "11977776666"
    assert data["email"] == "joao@email.com"
    assert uuid.UUID(data["id"])
    assert "created_at" in data


def test_create_user_missing_required_phone(client: TestClient) -> None:
    response = client.post(
        "/users",
        json={"name": "Sem Telefone", "email": "sem@telefone.com"},
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert any("phone" in item["field"] for item in error["details"])


def test_create_user_invalid_data_type(client: TestClient) -> None:
    response = client.post(
        "/users",
        json={"name": "Tipo Inválido", "phone": ["lista", "invalida"]},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# ==========================================
# GET /users (Listagem, Filtro e Paginação)
# ==========================================
def test_list_users_returns_registered_users(client: TestClient) -> None:
    client.post("/users", json={"name": "Ana Costa", "phone": "11911112222"})
    client.post("/users", json={"name": "Carlos Lima", "phone": "11933334444"})

    response = client.get("/users")
    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total"] == 2
    assert len(body["items"]) == 2


def test_list_users_filters_by_name_and_search(client: TestClient) -> None:
    client.post(
        "/users",
        json={
            "name": "Maria Oliveira",
            "phone": "11911111111",
            "email": "maria@x.com",
        },
    )
    client.post(
        "/users",
        json={
            "name": "Pedro Santos",
            "phone": "21999990000",
            "email": "pedro@x.com",
        },
    )

    by_name = client.get("/users?name=Maria")
    assert by_name.status_code == 200
    assert by_name.json()["pagination"]["total"] == 1
    assert by_name.json()["items"][0]["name"] == "Maria Oliveira"

    by_search = client.get("/users?search=2199999")
    assert by_search.status_code == 200
    assert by_search.json()["pagination"]["total"] == 1
    assert by_search.json()["items"][0]["name"] == "Pedro Santos"


def test_list_users_pagination_and_date_validation(client: TestClient) -> None:
    for idx in range(5):
        client.post(
            "/users", json={"name": f"User {idx}", "phone": f"1190000000{idx}"}
        )

    page_1 = client.get("/users?page=1&limit=2")
    assert page_1.status_code == 200
    data = page_1.json()
    assert len(data["items"]) == 2
    assert data["pagination"] == {
        "page": 1,
        "limit": 2,
        "total": 5,
        "pages": 3,
    }

    invalid_dates = client.get(
        "/users?start_date=2026-11-30&end_date=2026-11-01"
    )
    assert invalid_dates.status_code == 422
    assert invalid_dates.json()["error"]["code"] == "VALIDATION_ERROR"


# ==========================================
# GET /users/{user_id} e PATCH /users/{user_id}
# ==========================================
def test_get_user_by_id_found(client: TestClient, created_user: dict) -> None:
    response = client.get(f"/users/{created_user['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created_user["id"]
    assert response.json()["name"] == "Maria Silva"


def test_get_user_by_id_not_found(client: TestClient) -> None:
    random_id = uuid.uuid4()
    response = client.get(f"/users/{random_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_get_user_by_id_invalid_uuid(client: TestClient) -> None:
    response = client.get("/users/nao-e-um-uuid")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_update_user_partial_fields(
    client: TestClient, created_user: dict
) -> None:
    response = client.patch(
        f"/users/{created_user['id']}",
        json={"name": "Maria Silva Atualizada"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Maria Silva Atualizada"
    assert response.json()["phone"] == created_user["phone"]
