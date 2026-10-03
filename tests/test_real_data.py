"""Tests for the 'real data only' behaviour: clean start, then data from real actions."""
import os

SERVICE = {"name": "demo-api", "version": "1.0.0", "environment": "staging"}
RUN = {"pipeline_name": "devflow-pipeline", "build_number": 1,
       "status": "success", "duration_seconds": 120, "trigger": "Jenkins"}


def add_service(client, **overrides):
    return client.post("/api/services", json={**SERVICE, **overrides}).get_json()


# ---- clean start ----------------------------------------------------------
def test_init_sql_contains_no_demo_data():
    path = os.path.join(os.path.dirname(__file__), "..", "database", "init.sql")
    sql = open(path).read().upper()
    assert "CREATE TABLE IF NOT EXISTS SERVICES" in sql
    assert "INSERT INTO" not in sql


def test_empty_database_dashboard_is_all_zero(client):
    stats = client.get("/api/stats").get_json()
    assert stats["total_services"] == 0
    assert stats["active_services"] == 0
    assert stats["total_deployments"] == 0
    assert stats["successful_builds"] == 0
    assert all(d["success"] == 0 and d["failed"] == 0 for d in stats["build_chart"])


def test_empty_database_lists_are_empty(client):
    assert client.get("/api/services").get_json() == []
    assert client.get("/api/deployments").get_json() == []
    assert client.get("/api/pipelines").get_json() == []


# ---- service CRUD changes the database -------------------------------------
def test_service_lifecycle_is_persisted(client):
    created = add_service(client)
    assert client.get(f"/api/services/{created['id']}").get_json()["name"] == "demo-api"
    client.put(f"/api/services/{created['id']}", json={"version": "2.0.0"})
    assert client.get("/api/services").get_json()[0]["version"] == "2.0.0"
    client.delete(f"/api/services/{created['id']}")
    assert client.get("/api/services").get_json() == []
    assert client.get("/api/stats").get_json()["total_services"] == 0


# ---- deployments only come from real actions -------------------------------
def test_creating_a_service_does_not_create_deployments(client):
    add_service(client)
    assert client.get("/api/deployments").get_json() == []


def test_deploy_creates_and_returns_deployment(client):
    service = add_service(client)
    created = client.post(f"/api/services/{service['id']}/deploy").get_json()
    listed = client.get("/api/deployments").get_json()
    assert listed[0]["id"] == created["id"]
    assert listed[0]["version"] == "1.0.0" and listed[0]["status"] == "success"
    assert client.get("/api/stats").get_json()["total_deployments"] == 1


def test_deploy_unknown_service_returns_404(client):
    assert client.post("/api/services/999/deploy").status_code == 404


def test_deleting_service_removes_its_deployments(client):
    service = add_service(client)
    client.post(f"/api/services/{service['id']}/deploy")
    client.delete(f"/api/services/{service['id']}")
    assert client.get("/api/deployments").get_json() == []


# ---- pipeline records ------------------------------------------------------
def test_pipeline_records_are_retrievable(client):
    client.post("/api/pipelines", json=RUN)
    runs = client.get("/api/pipelines").get_json()
    assert len(runs) == 1
    assert runs[0]["build_number"] == 1 and runs[0]["trigger"] == "Jenkins"


# ---- dashboard statistics --------------------------------------------------
def test_dashboard_statistics_reflect_real_data(client):
    running = add_service(client, name="svc-a")
    add_service(client, name="svc-b", status="stopped")
    client.post(f"/api/services/{running['id']}/deploy")
    client.post("/api/pipelines", json=RUN)
    client.post("/api/pipelines", json={**RUN, "build_number": 2, "status": "failed"})

    stats = client.get("/api/stats").get_json()
    assert stats["total_services"] == 2
    assert stats["active_services"] == 1
    assert stats["total_deployments"] == 1
    assert stats["successful_builds"] == 1
    assert stats["failed_builds"] == 1
    today = stats["build_chart"][-1]
    assert today["success"] == 1 and today["failed"] == 1


# ---- docker page honesty ---------------------------------------------------
def test_docker_info_states_where_each_status_comes_from(client):
    containers = client.get("/api/docker").get_json()
    by_name = {c["name"]: c for c in containers}
    assert by_name["devflow-frontend"]["source"] == "docker-compose.yml"
    assert by_name["devflow-frontend"]["status"] == "configured"
    assert by_name["devflow-db"]["source"] == "live database query"
    assert by_name["devflow-db"]["status"] == "running"
