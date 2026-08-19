"""Login (2026-08-19) -- single shared admin credential, session-cookie based. Not a
multi-user account system: this exists to keep strangers out of a CRM that handles real
lead data and can trigger real outreach sends, not to model per-team-member permissions
(no such requirement exists yet).
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash

from config import Config

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    # Constant-time-safe either way: check_password_hash always runs even when the
    # username is wrong, so a wrong-username response takes the same time as a
    # wrong-password one -- doesn't leak which part was incorrect via timing.
    valid_user = username == Config.ADMIN_USERNAME
    valid_pass = bool(Config.ADMIN_PASSWORD_HASH) and check_password_hash(
        Config.ADMIN_PASSWORD_HASH, password)

    if not (valid_user and valid_pass):
        return jsonify({"error": ["invalid username or password"]}), 401

    session.clear()
    session["authenticated"] = True
    session.permanent = True  # honors PERMANENT_SESSION_LIFETIME (app.py), not browser-close
    return jsonify({"ok": True})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@auth_bp.route("/me", methods=["GET"])
def me():
    return jsonify({"authenticated": bool(session.get("authenticated"))})
