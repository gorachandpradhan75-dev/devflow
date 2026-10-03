"""CRUD endpoints for services, plus a 'deploy' action."""
from flask import Blueprint, jsonify, request

from extensions import db
from models import Deployment, Service, utc_now
from services.validators import validate_service

services_bp = Blueprint("services", __name__, url_prefix="/api/services")


def validation_error(errors):
    return jsonify({"error": "Validation failed", "details": errors}), 400


@services_bp.get("")
def list_services():
    services = Service.query.order_by(Service.id).all()
    return jsonify([s.to_dict() for s in services])


@services_bp.post("")
def create_service():
    clean, errors = validate_service(request.get_json(silent=True))
    if errors:
        return validation_error(errors)
    if Service.query.filter_by(name=clean["name"]).first():
        return jsonify({"error": "A service with this name already exists"}), 409
    service = Service(**clean)
    db.session.add(service)
    db.session.commit()
    return jsonify(service.to_dict()), 201


@services_bp.get("/<int:service_id>")
def get_service(service_id):
    return jsonify(db.get_or_404(Service, service_id).to_dict())


@services_bp.put("/<int:service_id>")
def update_service(service_id):
    service = db.get_or_404(Service, service_id)
    clean, errors = validate_service(request.get_json(silent=True), partial=True)
    if errors:
        return validation_error(errors)
    new_name = clean.get("name")
    if new_name and new_name != service.name:
        if Service.query.filter_by(name=new_name).first():
            return jsonify({"error": "A service with this name already exists"}), 409
    for field, value in clean.items():
        setattr(service, field, value)
    db.session.commit()
    return jsonify(service.to_dict())


@services_bp.delete("/<int:service_id>")
def delete_service(service_id):
    service = db.get_or_404(Service, service_id)
    db.session.delete(service)
    db.session.commit()
    return "", 204


@services_bp.post("/<int:service_id>/deploy")
def deploy_service(service_id):
    """Record a new deployment of the service's current version."""
    service = db.get_or_404(Service, service_id)
    deployment = Deployment(
        service_id=service.id,
        version=service.version,
        status="success",
        method="Docker Compose",
    )
    service.status = "running"
    service.last_deployed_at = utc_now()
    db.session.add(deployment)
    db.session.commit()
    return jsonify(deployment.to_dict()), 201
