def test_create_project_trims_name(client):
    response = client.post("/projects", json={"name": "  Demo Project  "})

    assert response.status_code == 201
    assert response.json()["name"] == "Demo Project"


def test_project_names_are_unique_case_insensitively(client):
    assert client.post("/projects", json={"name": "Payments"}).status_code == 201

    response = client.post("/projects", json={"name": "payments"})

    assert response.status_code == 409

