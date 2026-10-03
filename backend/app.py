"""DevFlow Flask application factory."""
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from config import Config
from extensions import db
from routes import register_routes


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    register_routes(app)

    if app.config.get("TESTING"):
        # Production tables are created by database/init.sql; tests build their own.
        with app.app_context():
            db.create_all()

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({"error": error.name}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception("Unhandled error")
        db.session.rollback()
        # Generic message: never leak database details to the client.
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
