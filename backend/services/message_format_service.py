"""Shared resolution logic for Phase 8's message_formats/content_assets (tracker.md A.7,
Steps 8.1/8.2) -- used by both `api/message_formats.py`'s /resolve endpoint (dashboard
visibility) and `jobs/outreach_handler.py`'s real drafting call, so the two never drift
onto different resolution rules.
"""
from __future__ import annotations

from database.models import ContentAsset, MessageFormat


def resolve_active_format(db, product_id, channel):
    """Resolution order: product+channel ACTIVE format -> global (product_id NULL)
    channel ACTIVE format -> None (today's free-form drafting, unchanged). Returns the
    ORM row itself (or None), not a serialized dict -- callers serialize however they
    need (the API route for the UI, the drafting handler just reads .sections).
    """
    row = None
    if product_id:
        row = (
            db.query(MessageFormat)
            .filter(
                MessageFormat.product_id == product_id,
                MessageFormat.channel == channel,
                MessageFormat.status == "ACTIVE",
            )
            .first()
        )
    if not row:
        row = (
            db.query(MessageFormat)
            .filter(
                MessageFormat.product_id.is_(None),
                MessageFormat.channel == channel,
                MessageFormat.status == "ACTIVE",
            )
            .first()
        )
    return row


def get_available_assets(db, product_id):
    """Every active asset usable for this product: product-scoped ones plus any global
    (product_id NULL) ones. Returns plain dicts (asset_type/title/value) -- exactly what
    the drafting prompt needs, nothing DB-internal (no id/created_at)."""
    query = db.query(ContentAsset).filter(ContentAsset.is_active == 1)
    if product_id:
        query = query.filter(
            (ContentAsset.product_id == product_id) | (ContentAsset.product_id.is_(None))
        )
    else:
        query = query.filter(ContentAsset.product_id.is_(None))
    return [
        {"asset_type": r.asset_type, "title": r.title, "value": r.value}
        for r in query.all()
    ]
