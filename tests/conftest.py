import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import store


@pytest.fixture(autouse=True)
def reset_store():
    store.reset()
    yield
    store.reset()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def project_id(client: TestClient) -> int:
    response = client.post("/projects", json={"name": "Agent Demo"})
    assert response.status_code == 201
    return response.json()["id"]

