def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_freshness(client):
    response = client.get("/meta/freshness")
    assert response.status_code == 200
    body = response.json()
    assert "latest_grade_year" in body
    assert "latest_grade_quarter" in body
    assert "schedule_fetched_at" in body
