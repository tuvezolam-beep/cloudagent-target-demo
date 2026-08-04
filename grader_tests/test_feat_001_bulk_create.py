def test_bulk_create_returns_all_tasks(client, project_id):
    response = client.post(
        f"/projects/{project_id}/tasks/bulk",
        json={
            "tasks": [
                {"title": "Design API", "priority": 4},
                {"title": "Write docs", "priority": 2},
            ]
        },
    )

    assert response.status_code == 201
    assert [task["title"] for task in response.json()] == ["Design API", "Write docs"]
    assert client.get(f"/projects/{project_id}/tasks").json()["total"] == 2


def test_bulk_create_is_atomic_on_duplicate(client, project_id):
    client.post(f"/projects/{project_id}/tasks", json={"title": "Existing"})

    response = client.post(
        f"/projects/{project_id}/tasks/bulk",
        json={
            "tasks": [
                {"title": "Would otherwise be created"},
                {"title": "existing"},
            ]
        },
    )

    assert response.status_code == 409
    tasks = client.get(f"/projects/{project_id}/tasks").json()["items"]
    assert [task["title"] for task in tasks] == ["Existing"]


def test_bulk_rejects_duplicates_within_request(client, project_id):
    response = client.post(
        f"/projects/{project_id}/tasks/bulk",
        json={"tasks": [{"title": "Same"}, {"title": " same "}]},
    )

    assert response.status_code == 409
    assert client.get(f"/projects/{project_id}/tasks").json()["total"] == 0

