import logging

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from app.config import Config
from app.extensions import cache, mongo


def create_app(config_class=Config):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.from_object(config_class)
    app.json.sort_keys = False

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}}, expose_headers=["Content-Disposition"])

    mongo.init_app(app)
    cache.init_app(app)

    from app.routes import analytics, auth, health, links, redirect, scanner

    for module in (auth, links, analytics, scanner, health):
        app.register_blueprint(module.bp)
    # registered last so /api/* routes win over the catch-all short code route
    app.register_blueprint(redirect.bp)

    @app.get("/")
    def index():
        return jsonify(name="LinkSense API", docs="/api/health", frontend=app.config["FRONTEND_URL"])

    @app.errorhandler(HTTPException)
    def http_error(err):
        return jsonify(error=err.description or err.name), err.code

    @app.errorhandler(Exception)
    def unhandled(err):
        app.logger.exception("Unhandled error")
        return jsonify(error="Something went wrong on our side"), 500

    if not app.config.get("TESTING"):
        from app.ml import registry

        registry.warm_up()
        if mongo.is_mock and app.config.get("SEED_DEMO"):
            from scripts.seed_demo import DEMO_EMAIL, DEMO_PASSWORD, seed

            seed(mongo.db)
            app.logger.info("Demo data loaded - log in with %s / %s", DEMO_EMAIL, DEMO_PASSWORD)

    return app
