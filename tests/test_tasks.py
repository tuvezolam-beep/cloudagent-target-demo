def create_task(client, project_id, title, **overrides):
    payload = {"title": title, "description": "Demo task", "priority": 3} | overrides
    response = client.post(f"/projects/{project_id}/tasks", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_and_list_tasks(client, project_id):
    create_task(client, project_id, "First task")
    create_task(client, project_id, "Second task")

    response = client.get(f"/projects/{project_id}/tasks")

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert [item["title"] for item in response.json()["items"]] == [
        "First task",
        "Second task",
    ]


def test_duplicate_task_title_is_rejected(client, project_id):
    create_task(client, project_id, "Release API")

    response = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "release api"},
    )

    assert response.status_code == 409


def test_filter_tasks_by_status(client, project_id):
    first = create_task(client, project_id, "Done task")
    create_task(client, project_id, "Pending task")
    client.patch(
        f"/projects/{project_id}/tasks/{first['id']}/status",
        json={"status": "done"},
    )

    response = client.get(f"/projects/{project_id}/tasks", params={"status": "done"})

    assert response.status_code == 200
    assert [item["title"] for item in response.json()["items"]] == ["Done task"]

