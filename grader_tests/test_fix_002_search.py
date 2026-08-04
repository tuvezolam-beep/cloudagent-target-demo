def test_search_is_case_insensitive_and_includes_description(client, project_id):
    client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Rotate credentials", "description": "Update the PAYMENT gateway token"},
    )
    client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Payment dashboard", "description": "Add revenue chart"},
    )
    client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Unrelated", "description": "Nothing to see"},
    )

    response = client.get(f"/projects/{project_id}/tasks", params={"query": "payment"})

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert {item["title"] for item in response.json()["items"]} == {
        "Rotate credentials",
        "Payment dashboard",
    }

