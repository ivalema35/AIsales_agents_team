"""Phase 14 Step 14.4 -- deterministic, non-LLM plain-text rendering of the SAME stored
`content_sections` list Phase 11's HTML renderer (email_renderer.py) draws from, for the
platforms email's own HTML can't be pasted into: WhatsApp / Instagram / Facebook /
LinkedIn. One canonical content object, many renderings (MASTER_DEVELOPMENT_PRD.md Phase
14) -- every branch here only re-formats a section that was already drafted and QC'd for
the real email, never invents or re-derives content.

Explicit MASTER PRD rules followed: URLs render as full plain links (none of these
platforms support a real button the way email does), the video becomes a labelled link,
the contact block is condensed to one line per entry.
"""
from __future__ import annotations


def _bullets(items, prefix="-") -> str:
    return "\n".join(f"{prefix} {item}" for item in items or [] if item)


def _render_one(section: dict) -> str:
    kind = section.get("type")
    if kind == "HOOK":
        return (section.get("text") or "").strip()
    if kind == "PAIN_POINTS":
        return _bullets(section.get("items"))
    if kind == "SOLUTION":
        return _bullets(section.get("items"), prefix="✓")
    if kind == "SERVICES_LIST":
        body = _bullets(section.get("items"), prefix="•")
        return f"What we offer:\n{body}" if body else ""
    if kind == "VIDEO":
        url = section.get("url")
        if not url:
            return ""
        title = section.get("title") or "Watch the video"
        return f"{title}: {url}"
    if kind == "CTA":
        parts = [p for p in (section.get("headline"), section.get("subtext")) if p]
        text = "\n".join(parts)
        url = section.get("button_url")
        if url:
            label = section.get("button_label") or "See the demo"
            text = f"{text}\n{label}: {url}".strip()
        return text
    if kind == "INTEREST":
        yes_url, no_url = section.get("yes_url"), section.get("no_url")
        if not yes_url or not no_url:
            return ""
        prompt = section.get("prompt") or "Would this be worth a look?"
        yes_label = section.get("yes_label") or "Yes, tell me more"
        no_label = section.get("no_label") or "Not right now"
        return f"{prompt}\n{yes_label}: {yes_url}\n{no_label}: {no_url}"
    if kind == "CONTACT":
        heading = section.get("heading") or "Get in touch"
        rows = "\n".join(
            f"{label}: {value}" for label, value, _href in section.get("items") or [] if value
        )
        return f"{heading}\n{rows}" if rows else ""
    if kind == "CROSS_SELL":
        return (section.get("text") or "").strip()
    # Any other asset-backed section (CASE_STUDY, TESTIMONIAL, TEXT_BLOCK, and anything
    # added to ASSET_SECTIONS later) -- same generic url/text fallback
    # email_renderer.py's own _render_section() uses, so a new section type never needs a
    # new branch in both places.
    if section.get("url"):
        title = section.get("title") or "Take a look"
        return f"{title}: {section['url']}"
    if section.get("text"):
        return section["text"].strip()
    return ""


def render_plain_text(sections: list[dict]) -> str:
    """Every platform outside email (WhatsApp/Instagram/Facebook/LinkedIn) shares this one
    rendering -- none of them support HTML or a real button, so there is no real
    per-platform difference to encode."""
    blocks = [b for b in (_render_one(s) for s in sections or []) if b]
    return "\n\n".join(blocks)
