from datetime import UTC, datetime, timedelta


def test_metrics_aggregate_status_and_overdue_tasks(client, project_id):
    yesterday = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    tomorrow = (datetime.now(UTC) + timedelta(days=1)).isoformat()

    task_1 = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Completed", "due_at": yesterday},
    ).json()
    task_2 = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Late", "due_at": yesterday},
    ).json()
    client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Future", "due_at": tomorrow},
    )
    client.patch(
        f"/projects/{project_id}/tasks/{task_1['id']}/status",
        json={"status": "done"},
    )
    client.patch(
        f"/projects/{project_id}/tasks/{task_2['id']}/status",
        json={"status": "in_progress"},
    )

    response = client.get(f"/projects/{project_id}/metrics")

    assert response.status_code == 200
    assert response.json() == {
        "total": 3,
        "by_status": {"todo": 1, "in_progress": 1, "done": 1},
        "overdue": 1,
        "completion_rate": 1 / 3,
    }


def test_empty_project_metrics_are_well_defined(client, project_id):
    response = client.get(f"/projects/{project_id}/metrics")

    assert response.status_code == 200
    assert response.json() == {
        "total": 0,
        "by_status": {"todo": 0, "in_progress": 0, "done": 0},
        "overdue": 0,
        "completion_rate": 0.0,
    }

