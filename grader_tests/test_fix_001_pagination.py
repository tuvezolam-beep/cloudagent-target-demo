def test_pages_never_overlap(client, project_id):
    for number in range(1, 6):
        response = client.post(
            f"/projects/{project_id}/tasks",
            json={"title": f"Task {number}"},
        )
        assert response.status_code == 201

    first_page = client.get(
        f"/projects/{project_id}/tasks", params={"page": 1, "page_size": 2}
    ).json()
    second_page = client.get(
        f"/projects/{project_id}/tasks", params={"page": 2, "page_size": 2}
    ).json()
    third_page = client.get(
        f"/projects/{project_id}/tasks", params={"page": 3, "page_size": 2}
    ).json()

    assert [item["title"] for item in first_page["items"]] == ["Task 1", "Task 2"]
    assert [item["title"] for item in second_page["items"]] == ["Task 3", "Task 4"]
    assert [item["title"] for item in third_page["items"]] == ["Task 5"]
    assert first_page["total"] == second_page["total"] == third_page["total"] == 5

