"""Phase 10 Step 10.1 -- region-aware channel routing (tracker.md, MASTER PRD Step 10.1).

Solves a real, live gap: WhatsApp is not reliably usable outside India (the existing
Barber Shop (Canada) product's leads are a live example), but nothing in the system
ever checked a lead's region before queuing a WhatsApp send. `channel_policies` maps
a product's target_country (ISO 3166-1 alpha-2 -- the same code phone_utils.normalize_
phone() already trusts, not the free-text, inconsistently-scraped leads.region_location)
to the channels that are actually appropriate there.

A country with no configured policy is NOT guessed at -- it falls back to EMAIL only,
the one channel with no per-country restriction (MASTER PRD Step 10.1).
"""
from __future__ import annotations
import json

from database.models import ChannelPolicy

ALL_CHANNELS = {"EMAIL", "WHATSAPP"}
DEFAULT_ALLOWED = {"EMAIL"}  # no policy configured -- never guess beyond the universal fallback


def get_allowed_channels(db, country_code: str | None) -> set[str]:
    """The set of channels allowed for this country code. No country_code, no matching
    policy row, or a malformed one all mean "not configured" -> EMAIL-only.
    """
    if not country_code:
        return set(DEFAULT_ALLOWED)
    policy = db.query(ChannelPolicy).filter(
        ChannelPolicy.country_code == country_code.upper()
    ).first()
    if not policy:
        return set(DEFAULT_ALLOWED)
    try:
        allowed = json.loads(policy.allowed_channels)
    except (TypeError, ValueError):
        return set(DEFAULT_ALLOWED)
    channels = {ch for ch in allowed if ch in ALL_CHANNELS}
    return channels or set(DEFAULT_ALLOWED)
