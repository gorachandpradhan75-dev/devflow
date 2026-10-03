"""Health, statistics and Docker information endpoints."""
import os
from datetime import timedelta

from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from extensions import db
from models import Deployment, PipelineRun, Service, utc_now

system_bp = Blueprint("system", __name__, url_prefix="/api")


def database_is_up():
    try:
        db.session.execute(text("SELECT 1"))
        return True
    except Exception:
        db.session.rollback()
        return False


@system_bp.get("/health")
def health():
    """Used by Docker healthchecks and the Jenkins 'Health Check' stage."""
    db_up = database_is_up()
    body = {
        "status": "ok" if db_up else "degraded",
        "database": "connected" if db_up else "unavailable",
        "version": current_app.config["APP_VERSION"],
    }
    return jsonify(body), (200 if db_up else 503)


@system_bp.get("/stats")
def stats():
    runs = PipelineRun.query.all()
    since = utc_now() - timedelta(days=6)

    # Build results per day for the last 7 days (used by the dashboard chart).
    days = [(since + timedelta(days=i)).date() for i in range(7)]
    chart = {d.isoformat(): {"success": 0, "failed": 0} for d in days}
    for run in runs:
        if run.started_at is None:
            continue
        key = run.started_at.date().isoformat()
        if key in chart and run.status in ("success", "failed"):
            chart[key][run.status] += 1

    return jsonify({
        "total_services": Service.query.count(),
        "active_services": Service.query.filter_by(status="running").count(),
        "total_deployments": Deployment.query.count(),
        "successful_builds": sum(1 for r in runs if r.status == "success"),
        "failed_builds": sum(1 for r in runs if r.status == "failed"),
        "build_chart": [{"date": d, **v} for d, v in chart.items()],
    })


@system_bp.get("/docker")
def docker_info():
    """Describes the containers defined in docker-compose.yml.

    This is NOT live Docker daemon monitoring. Names, images and ports come from
    the compose configuration. Each entry says how its status was obtained
    ("source"), so the dashboard never presents configuration as live state:
      - backend:  this request was answered by it            -> live
      - database: a real "SELECT 1" is run against it        -> live
      - frontend: cannot be checked from the backend         -> configuration only
    """
    web_port = os.getenv("FRONTEND_PORT", "8095")
    api_port = os.getenv("BACKEND_PORT", "5000")
    db_up = database_is_up()
    return jsonify([
        {"name": "devflow-frontend", "image": "nginx:alpine (built from ./frontend)",
         "status": "configured", "source": "docker-compose.yml",
         "port": f"{web_port}:80", "environment": "production"},
        {"name": "devflow-backend", "image": "python:3.12-slim (built from ./Dockerfile)",
         "status": "running", "source": "live API response",
         "port": f"{api_port}:5000", "environment": "production"},
        {"name": "devflow-db", "image": "postgres:16-alpine",
         "status": "running" if db_up else "unreachable", "source": "live database query",
         "port": "5432 (internal)", "environment": "production"},
    ])
