def test_repeating_same_status_is_idempotent(client, project_id):
    task = client.post(
        f"/projects/{project_id}/tasks", json={"title": "Ship release"}
    ).json()

    first = client.patch(
        f"/projects/{project_id}/tasks/{task['id']}/status",
        json={"status": "done"},
    )
    second = client.patch(
        f"/projects/{project_id}/tasks/{task['id']}/status",
        json={"status": "done"},
    )
    audit = client.get(f"/projects/{project_id}/audit-events").json()

    assert first.status_code == second.status_code == 200
    assert second.json()["completed_at"] == first.json()["completed_at"]
    assert len(audit) == 1

