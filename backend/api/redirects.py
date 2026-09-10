"""2026-09-10, real user ask: a WhatsApp template button linking directly to a wa.me/
api.whatsapp.com URL is rejected by Meta/the BSP ("Direct links to WhatsApp aren't
allowed for buttons") -- a blanket rule, independent of which number it points to. The
real business need is still legitimate (routing a lead to a DIFFERENT WhatsApp number
than the automated channel, e.g. a real salesperson) -- the accepted workaround is a
button URL on OUR OWN domain that immediately 302-redirects to the real wa.me link, so
the button's own visible URL domain passes the template-creation check.

Generic (not hardcoded to one number) so any future template's "chat with a specific
number" button reuses this same route -- see MEMORY.md's "Example means generalize" rule.

Deliberately public (no login) -- a real lead's browser/WhatsApp client hits this
directly from a template button, same posture as the interest/unsubscribe links. Must
stay under "/api/" -- production's real webserver only proxies that prefix to Flask
(see reference_production_static_file_serving finding); a bare "/go/..." prefix would
silently never be reached, exactly like the interest/unsubscribe bug this same day.

Real, disclosed risk (told to the user before building this): Meta/the BSP could still
flag or reject a template if their review inspects the redirect's actual destination --
this passes today's automated button-URL check, but is not guaranteed to stay unnoticed
forever. Built only after the user explicitly chose this option knowing that.
"""
from __future__ import annotations
import re

from flask import Blueprint, redirect, request

redirects_bp = Blueprint("redirects", __name__, url_prefix="/api/v1/go")

# wa.me expects a bare international-format number, digits only, no leading '+' -- this
# also doubles as the only real security control here (this route's whole job is to
# redirect somewhere, so it must never forward an arbitrary caller-supplied URL/scheme,
# only ever build a wa.me link from a validated digit string).
_DIGITS_ONLY = re.compile(r"^\d{10,15}$")


@redirects_bp.route("/whatsapp", methods=["GET"])
def whatsapp_redirect():
    to = (request.args.get("to") or "").strip()
    if not _DIGITS_ONLY.match(to):
        return "Invalid WhatsApp number.", 400
    return redirect(f"https://wa.me/{to}", code=302)
