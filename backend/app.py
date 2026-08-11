from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from logging_config import configure_logging
from api.products import products_bp
from api.leads import leads_bp


def create_app():
    app = Flask(__name__)
    configure_logging(app)
    CORS(app, origins=[Config.FRONTEND_ORIGIN])

    app.register_blueprint(products_bp)
    app.register_blueprint(leads_bp)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=(Config.ENV == "development"))
