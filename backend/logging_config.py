import json
import logging
import sys
import uuid

from flask import g, request


class JSONFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        try:
            record.request_id = g.request_id
        except RuntimeError:
            record.request_id = None
        return True


def configure_logging(app):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    root.addFilter(RequestIdFilter())

    @app.before_request
    def _assign_request_id():
        g.request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
