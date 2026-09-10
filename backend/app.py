from datetime import timedelta

from flask import Flask, jsonify, request, session
from flask_cors import CORS

from config import Config
from logging_config import configure_logging
from api.products import products_bp
from api.leads import leads_bp
from api.unsubscribe import unsubscribe_bp
from api.interest import interest_bp
from api.alerts import alerts_bp
from api.settings import settings_bp
from api.inbound import inbound_bp
from api.reports import reports_bp
from api.env_settings import env_settings_bp
from api.analytics import analytics_bp
from api.dashboard import dashboard_bp
from api.webhooks import webhooks_bp
from api.system import system_bp
from api.auth import auth_bp
from api.message_formats import message_formats_bp
from api.content_assets import content_assets_bp
from api.whatsapp_templates import whatsapp_templates_bp
from api.social_queue import social_queue_bp
from api.prospects import prospects_bp
from api.knowledge_base import knowledge_base_bp
from api.campaigns import campaigns_bp
from api.strategy_insights import strategy_insights_bp
from api.todos import todos_bp
from api.redirects import redirects_bp

# Paths that must stay reachable WITHOUT a login (2026-08-19 auth gate, see api/auth.py):
# the login endpoints themselves, health checks, and the handful of routes real external
# parties hit directly and can never be asked to log in -- Meta's WhatsApp webhook,
# Resend's email-event webhook, the one-click unsubscribe link, and (Phase 12 Step 12.2)
# the HMAC-verified Yes/No interest link -- all clicked by a real lead from their own
# inbox. Everything else in the app is real business data (leads, products, outreach)
# and stays behind the gate.
# 2026-09-10: unsubscribe/interest moved from bare "/unsubscribe"/"/interest" to under
# "/api/v1/" -- production's real webserver only proxies "/api/" to Flask, so the old
# bare prefixes were NEVER actually reachable in production (silently served the SPA
# shell instead -- a real, live bug, see api/interest.py's own docstring for the fix).
_PUBLIC_PREFIXES = (
    "/health",
    "/api/v1/auth/",
    "/api/v1/inbound/",
    "/api/v1/webhooks/",
    "/api/v1/unsubscribe/",
    "/api/v1/interest/",
    # A real lead's WhatsApp client hits this straight from a template button (2026-09-10).
    "/api/v1/go/",
    # Brand logo used in outbound email HTML -- recipients' mail clients must fetch this
    # without a CRM session cookie (2026-09-05).
    "/static/brand/",
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
    app.register_blueprint(interest_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(inbound_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(env_settings_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(webhooks_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(message_formats_bp)
    app.register_blueprint(content_assets_bp)
    app.register_blueprint(whatsapp_templates_bp)
    app.register_blueprint(social_queue_bp)
    app.register_blueprint(prospects_bp)
    app.register_blueprint(knowledge_base_bp)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(strategy_insights_bp)
    app.register_blueprint(todos_bp)
    app.register_blueprint(redirects_bp)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    return app


if __name__ == "__main__":
    app = create_app()
    # threaded=True only in dev: the built-in Werkzeug server is single-threaded by default
    # and serialises every request. That was mostly invisible before Step 6.2/6.3 -- now the
    # nav's SystemStatusDot and the /system page both poll /api/v1/system/live continuously
    # in the background, on top of normal page traffic, and a serialised dev server can
    # queue/delay those enough to make the UI look laggier than it really is. Production is
    # unaffected -- it's served by gunicorn's multiple worker processes (bos-api.service),
    # never by this app.run() call at all.
    app.run(debug=(Config.ENV == "development"), threaded=(Config.ENV == "development"))
