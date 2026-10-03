"""Backend API tests (run with: pytest tests -v)."""

NEW_SERVICE = {"name": "demo-api", "version": "1.0.0", "environment": "staging"}


def create(client, **overrides):
    return client.post("/api/services", json={**NEW_SERVICE, **overrides})


# ---- availability / health -------------------------------------------------
def test_api_is_available(client):
    assert client.get("/api/services").status_code == 200


def test_health_reports_database_connected(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["database"] == "connected"


def test_unknown_route_returns_json_404(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert "error" in response.get_json()


# ---- create ---------------------------------------------------------------
def test_create_service(client):
    response = create(client)
    assert response.status_code == 201
    body = response.get_json()
    assert body["name"] == "demo-api"
    assert body["status"] == "running"


def test_create_service_rejects_missing_fields(client):
    response = client.post("/api/services", json={"name": "x"})
    assert response.status_code == 400
    assert "version" in response.get_json()["details"]


def test_create_service_rejects_invalid_environment(client):
    assert create(client, environment="moon").status_code == 400


def test_create_service_rejects_duplicate_name(client):
    create(client)
    assert create(client).status_code == 409


# ---- read -----------------------------------------------------------------
def test_get_and_list_services(client):
    service_id = create(client).get_json()["id"]
    assert client.get(f"/api/services/{service_id}").get_json()["name"] == "demo-api"
    assert len(client.get("/api/services").get_json()) == 1


def test_get_missing_service_returns_404(client):
    assert client.get("/api/services/999").status_code == 404


# ---- update ---------------------------------------------------------------
def test_update_service(client):
    service_id = create(client).get_json()["id"]
    response = client.put(f"/api/services/{service_id}",
                          json={"version": "1.1.0", "status": "stopped"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["version"] == "1.1.0" and body["status"] == "stopped"


def test_update_rejects_invalid_status(client):
    service_id = create(client).get_json()["id"]
    response = client.put(f"/api/services/{service_id}", json={"status": "exploded"})
    assert response.status_code == 400


# ---- delete ---------------------------------------------------------------
def test_delete_service(client):
    service_id = create(client).get_json()["id"]
    assert client.delete(f"/api/services/{service_id}").status_code == 204
    assert client.get(f"/api/services/{service_id}").status_code == 404


# ---- deployments, pipelines, stats ----------------------------------------
def test_deploy_creates_deployment_record(client):
    service_id = create(client).get_json()["id"]
    assert client.post(f"/api/services/{service_id}/deploy").status_code == 201
    history = client.get("/api/deployments").get_json()
    assert len(history) == 1 and history[0]["service_name"] == "demo-api"


def test_pipeline_run_is_recorded_and_counted(client):
    run = {"pipeline_name": "devflow-pipeline", "build_number": 1,
           "status": "success", "duration_seconds": 120, "trigger": "GitHub push"}
    assert client.post("/api/pipelines", json=run).status_code == 201
    assert len(client.get("/api/pipelines").get_json()) == 1
    assert client.get("/api/stats").get_json()["successful_builds"] == 1


def test_pipeline_run_validation(client):
    assert client.post("/api/pipelines", json={"status": "bogus"}).status_code == 400


def test_stats_and_docker_endpoints(client):
    create(client)
    stats = client.get("/api/stats").get_json()
    assert stats["total_services"] == 1 and len(stats["build_chart"]) == 7
    assert len(client.get("/api/docker").get_json()) == 3
