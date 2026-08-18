from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from logging_config import configure_logging
from api.products import products_bp
from api.leads import leads_bp
from api.unsubscribe import unsubscribe_bp
from api.alerts import alerts_bp
from api.settings import settings_bp
from api.inbound import inbound_bp
from api.reports import reports_bp
from api.env_settings import env_settings_bp
from api.analytics import analytics_bp
from api.dashboard import dashboard_bp
from api.webhooks import webhooks_bp


def create_app():
    app = Flask(__name__)
    configure_logging(app)
    CORS(app, origins=[Config.FRONTEND_ORIGIN])

    app.register_blueprint(products_bp)
    app.register_blueprint(leads_bp)
    app.register_blueprint(unsubscribe_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(inbound_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(env_settings_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(webhooks_bp)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=(Config.ENV == "development"))
