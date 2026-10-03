"""CI/CD pipeline records. Jenkins can POST a record at the end of each build."""
from flask import Blueprint, jsonify, request

from extensions import db
from models import PipelineRun
from services.validators import validate_pipeline_run

pipelines_bp = Blueprint("pipelines", __name__, url_prefix="/api/pipelines")


@pipelines_bp.get("")
def list_pipeline_runs():
    runs = PipelineRun.query.order_by(PipelineRun.started_at.desc()).limit(50).all()
    return jsonify([r.to_dict() for r in runs])


@pipelines_bp.post("")
def create_pipeline_run():
    clean, errors = validate_pipeline_run(request.get_json(silent=True))
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400
    run = PipelineRun(**clean)
    db.session.add(run)
    db.session.commit()
    return jsonify(run.to_dict()), 201
