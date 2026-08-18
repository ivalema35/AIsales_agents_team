"""Suppression enforcement -- MASTER's non-negotiable 100% rule: a STOP, unsubscribe,
bounce, or manual block, once recorded, blocks a channel+identifier PERMANENTLY.

is_suppressed() must be called immediately before every single send, unconditionally --
no other check (QC approval, high confidence, anything) substitutes for this one. This
module is deliberately the only place that reads/writes `suppression_list`, so every
future send path (Step 3.3 email, 3.4 WhatsApp, and Phase 4's inbound STOP handler) goes
through the exact same normalization and the exact same table.
"""
import uuid

from sqlalchemy.exc import IntegrityError

from database.models import SuppressionEntry
from services.data_acquisition.website_scraper import normalize_mobile

VALID_REASONS = {"UNSUBSCRIBE", "STOP", "BOUNCE", "MANUAL"}


def normalize_identifier(channel: str, identifier: str):
    """Same normalization rule used everywhere else in this project for each channel,
    so a suppression recorded one way is never missed by a check written another way
    (e.g. 'ABC@Gmail.com' suppressed must still block a later send to 'abc@gmail.com').
    """
    if not identifier:
        return None
    if channel == "EMAIL":
        return identifier.strip().lower()
    if channel == "WHATSAPP":
        mobile = normalize_mobile(identifier)
        if mobile:
            return mobile
        # couldn't normalize to a clean Indian-mobile shape -- fall back to digits-only
        # rather than silently drop it. Erring toward MORE suppression coverage, not less.
        digits = "".join(c for c in identifier if c.isdigit())
        return digits or None
    return identifier.strip()


def is_suppressed(db, channel: str, identifier: str) -> bool:
    normalized = normalize_identifier(channel, identifier)
    if not normalized:
        return False
    return db.query(SuppressionEntry).filter(
        SuppressionEntry.channel == channel,
        SuppressionEntry.identifier == normalized,
    ).first() is not None


def add_suppression(db, channel: str, identifier: str, reason: str) -> bool:
    """Idempotent: suppressing an already-suppressed identifier is a no-op, not an
    error -- a STOP reply can arrive more than once, a bounce can land after a manual
    suppression already exists, etc. Returns True if a new row was created, False if it
    was already suppressed (including a concurrent add racing this one -- relies on the
    table's own UniqueConstraint(channel, identifier) as the source of truth rather than
    a check-then-insert, which would have a race window).
    """
    if reason not in VALID_REASONS:
        raise ValueError(f"invalid suppression reason: {reason!r} (expected one of {VALID_REASONS})")

    normalized = normalize_identifier(channel, identifier)
    if not normalized:
        raise ValueError(f"cannot suppress an empty/unusable identifier for channel {channel!r}")

    db.add(SuppressionEntry(
        id=str(uuid.uuid4()),
        channel=channel,
        identifier=normalized,
        reason=reason,
    ))
    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False
