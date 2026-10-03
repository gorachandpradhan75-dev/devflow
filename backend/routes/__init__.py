from .services import services_bp
from .deployments import deployments_bp
from .pipelines import pipelines_bp
from .system import system_bp


def register_routes(app):
    for blueprint in (services_bp, deployments_bp, pipelines_bp, system_bp):
        app.register_blueprint(blueprint)
