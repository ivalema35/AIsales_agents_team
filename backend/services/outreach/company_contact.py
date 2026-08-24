"""Phase 11 Step 11.4 -- the CONTACT section of a structured outreach email, built from
our own dashboard-editable settings.

Deliberately its own module rather than something the drafting agent produces: these are
facts about US, not content written for this lead, and an agent that could author them
could also get one wrong. The agent never sees them and never writes them.
"""
from __future__ import annotations

from services.system_settings import (
    get_str, COMPANY_CONTACT_EMAIL, COMPANY_CONTACT_PHONE,
    COMPANY_WEBSITE_URL, COMPANY_PROFILE_URL,
)

# (settings key, label shown to the lead, how to turn the value into a link)
_ROWS = (
    (COMPANY_CONTACT_EMAIL, "Email", lambda v: f"mailto:{v}"),
    (COMPANY_CONTACT_PHONE, "Phone", lambda v: "tel:" + "".join(
        c for c in v if c.isdigit() or c == "+")),
    (COMPANY_WEBSITE_URL, "Website", lambda v: v),
    (COMPANY_PROFILE_URL, "Company profile", lambda v: v),
)


def _display(key: str, value: str) -> str:
    """A URL is shown without its scheme -- "ivinfotech.com" reads as a company,
    "https://ivinfotech.com/" reads as a machine. The href keeps the full value."""
    if key in (COMPANY_WEBSITE_URL, COMPANY_PROFILE_URL):
        return value.split("://", 1)[-1].rstrip("/")
    return value


def build_contact_section(db, heading: str = "Get in touch") -> dict | None:
    """The CONTACT section, or None when nothing is configured at all.

    Returning None rather than an empty section is what lets Step 11.3's rule do its work
    unchanged: a section that is never appended can never render as an empty card.
    """
    items = []
    for key, label, to_href in _ROWS:
        value = (get_str(db, key, default="") or "").strip()
        if not value:
            continue          # each line is independently optional
        items.append((label, _display(key, value), to_href(value)))
    if not items:
        return None
    return {"type": "CONTACT", "heading": heading, "items": items}
