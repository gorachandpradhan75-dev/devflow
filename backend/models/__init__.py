"""Database models: Service, Deployment and PipelineRun."""
from datetime import datetime, timezone

from extensions import db


def utc_now():
    return datetime.now(timezone.utc)


def iso(value):
    return value.isoformat() if value else None


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    version = db.Column(db.String(30), nullable=False)
    environment = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="running")
    description = db.Column(db.String(255), default="")
    last_deployed_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now)

    # Deleting a service also deletes its deployment history.
    deployments = db.relationship(
        "Deployment", backref="service", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "environment": self.environment,
            "status": self.status,
            "description": self.description,
            "last_deployed_at": iso(self.last_deployed_at),
            "created_at": iso(self.created_at),
        }


class Deployment(db.Model):
    __tablename__ = "deployments"

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(
        db.Integer, db.ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    version = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    method = db.Column(db.String(30), nullable=False, default="Docker Compose")
    deployed_at = db.Column(db.DateTime(timezone=True), default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "service_id": self.service_id,
            "service_name": self.service.name if self.service else None,
            "version": self.version,
            "status": self.status,
            "method": self.method,
            "deployed_at": iso(self.deployed_at),
        }


class PipelineRun(db.Model):
    __tablename__ = "pipeline_runs"

    id = db.Column(db.Integer, primary_key=True)
    pipeline_name = db.Column(db.String(80), nullable=False)
    build_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    duration_seconds = db.Column(db.Integer, default=0)
    trigger = db.Column(db.String(40), default="Manual")
    started_at = db.Column(db.DateTime(timezone=True), default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "pipeline_name": self.pipeline_name,
            "build_number": self.build_number,
            "status": self.status,
            "duration_seconds": self.duration_seconds,
            "trigger": self.trigger,
            "started_at": iso(self.started_at),
        }
