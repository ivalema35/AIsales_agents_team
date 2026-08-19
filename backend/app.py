from datetime import timedelta

from flask import Flask, jsonify, request, session
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
from api.auth import auth_bp

# Paths that must stay reachable WITHOUT a login (2026-08-19 auth gate, see api/auth.py):
# the login endpoints themselves, health checks, and the handful of routes real external
# parties hit directly and can never be asked to log in -- Meta's WhatsApp webhook,
# Resend's email-event webhook, and the one-click unsubscribe link a real lead clicks
# from their own inbox. Everything else in the app is real business data (leads,
# products, outreach) and stays behind the gate.
_PUBLIC_PREFIXES = (
    "/health",
    "/api/v1/auth/",
    "/api/v1/inbound/",
    "/api/v1/webhooks/",
    "/unsubscribe/",
)


def create_app():
    app = Flask(__name__)
    configure_logging(app)
    app.secret_key = Config.SECRET_KEY
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    # Real cookie only over HTTPS in production (the VPS deploy) -- would silently never
    # be set by the browser over plain http:// in local dev otherwise.
    app.config["SESSION_COOKIE_SECURE"] = Config.ENV != "development"
    CORS(app, origins=[Config.FRONTEND_ORIGIN], supports_credentials=True)

    @app.before_request
    def require_login():
        if request.method == "OPTIONS" or any(request.path.startswith(p) for p in _PUBLIC_PREFIXES):
            return None
        if not session.get("authenticated"):
            return jsonify({"error": ["login required"]}), 401
        return None

    app.register_blueprint(auth_bp)
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
