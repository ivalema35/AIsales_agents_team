from __future__ import annotations
"""Country-aware phone number normalization, using Google's `phonenumbers` library
(the standard, well-tested implementation of this exact problem) instead of hand-rolled
digit-count regexes.

Built after a real, live safety bug: `website_scraper.normalize_mobile()` accepted ANY
10-digit string starting with 6-9 as "a valid Indian mobile", with no actual country
awareness. A real Canadian lead's toll-free number, `(877) 418-2581`, happened to satisfy
that exact shape (877... -> 8774182581) and would have had "91" prepended for a WhatsApp
send -- a real message to a fabricated, unrelated number, not the lead at all. Found live,
2026-08-17, while onboarding the first non-Indian product (Barber shop management
software, target Edmonton, Canada).
"""
import phonenumbers


def normalize_phone(raw: str, country_hint: str = "IN") -> str | None:
    """Parses `raw` using `country_hint` (ISO 3166-1 alpha-2, e.g. "IN"/"CA") as the
    default region for numbers with no explicit country code, validates it's a real,
    dialable number, and returns Meta Cloud API's own convention for a `to` value:
    country code + national number, digits only, no leading '+'.

    Returns None for anything unparseable or invalid -- callers already treat None as
    "no usable phone", the same contract normalize_mobile() had.
    """
    if not raw:
        return None
    try:
        parsed = phonenumbers.parse(raw, country_hint)
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_valid_number(parsed):
        return None
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164).lstrip("+")
