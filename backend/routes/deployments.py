from flask import Blueprint, jsonify

from models import Deployment

deployments_bp = Blueprint("deployments", __name__, url_prefix="/api/deployments")


@deployments_bp.get("")
def list_deployments():
    deployments = Deployment.query.order_by(Deployment.deployed_at.desc()).limit(100).all()
    return jsonify([d.to_dict() for d in deployments])
