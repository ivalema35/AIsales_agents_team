"""Phase 11 Step 11.2 -- renders a structured section list (Step 11.1) into real email HTML.

Every constraint here is imposed by real mail clients, not by preference:

- **Table-based layout, never flex/grid.** Outlook renders through Word's HTML engine and
  ignores modern layout entirely; a flex layout collapses into a single unstyled column.
- **Fully inline styles.** Gmail strips `<style>` blocks in several contexts, and an
  external stylesheet is never fetched at all.
- **No JavaScript, no web fonts, no remote CSS.** Blocked everywhere; a font that fails to
  load silently changes every measurement the design assumed.
- **The layout must read correctly with images disabled**, which is the default in a large
  share of real inboxes. That is why the video block carries a real text link beneath the
  thumbnail rather than relying on the image being a link -- with images off, an
  image-only link is an invisible one.
- **Action URLs render as buttons, never bare links** (the operator's explicit ask). The
  button is a table wrapping an `<a>`, not a styled `<a>` alone, because Outlook ignores
  padding on an inline element and would collapse it to plain text.

Graceful omission (Step 11.3) is inherited rather than re-implemented: this renders
exactly the sections it is given, and Step 11.1 only ever appends a section that has real
content. There is no "empty section" branch here because an empty section never arrives.
"""
from __future__ import annotations
import html
import logging

import requests

from config import Config

logger = logging.getLogger(__name__)

# One place to tune the whole design. Kept as plain constants (not a CSS file) because
# every value below has to end up inlined on an element anyway.
INK = "#1f2937"          # primary text
INK_MUTED = "#6b7280"    # secondary text
RULE = "#e5e7eb"         # hairlines and borders
CANVAS = "#f4f5f7"       # the area around the card
CARD = "#ffffff"
ACCENT = "#1f2937"       # primary button fill
ACCENT_TEXT = "#ffffff"
LINK = "#2563eb"
PAIN_MARK = "#dc2626"
GAIN_MARK = "#059669"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, Helvetica, sans-serif"
CARD_WIDTH = 600


def fetch_video_thumbnail(video_url: str) -> str | None:
    """Real oEmbed lookup (YouTube/Vimeo's own public, no-auth endpoints) for a real
    thumbnail of a real video -- never fabricated, never a generic placeholder. Returns
    None for an unsupported provider or a failed lookup; a missing thumbnail must never
    block a real send, it just means the video renders as a link instead of an image."""
    try:
        if "youtube.com" in video_url or "youtu.be" in video_url:
            resp = requests.get("https://www.youtube.com/oembed",
                                params={"url": video_url, "format": "json"}, timeout=5)
            resp.raise_for_status()
            return resp.json().get("thumbnail_url")
        if "vimeo.com" in video_url:
            resp = requests.get("https://vimeo.com/api/oembed.json",
                                params={"url": video_url}, timeout=5)
            resp.raise_for_status()
            return resp.json().get("thumbnail_url")
    except Exception as exc:  # noqa: BLE001 - display-only, must never break a real send
        logger.warning("video thumbnail lookup failed for %s: %s", video_url, exc)
    return None


def _e(value) -> str:
    return html.escape(str(value or ""))


def _button(url: str, label: str, primary: bool = True) -> str:
    """A table-wrapped button. Outlook ignores padding on an inline `<a>`, so a styled
    anchor alone silently degrades to plain blue text there -- the table cell is what
    actually carries the shape."""
    bg = ACCENT if primary else CARD
    fg = ACCENT_TEXT if primary else INK
    border = "none" if primary else f"1px solid {RULE}"
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 0;">
  <tr>
    <td align="center" bgcolor="{bg}" style="border-radius: 6px; border: {border};">
      <a href="{_e(url)}" style="display: inline-block; padding: 12px 22px; font-family: {FONT};
         font-size: 14px; font-weight: 600; color: {fg}; text-decoration: none; border-radius: 6px;">{_e(label)}</a>
    </td>
  </tr>
</table>"""


def _bullet_list(items, mark: str, mark_color: str) -> str:
    """A two-column table per bullet rather than `<ul>`: list-marker styling is one of the
    least consistent things across mail clients, and the marker here is carrying real
    meaning (a problem vs. an answer to it), so it cannot be left to the client."""
    rows = "".join(f"""
  <tr>
    <td valign="top" style="padding: 0 10px 10px 0; font-family: {FONT}; font-size: 15px;
        line-height: 1.5; color: {mark_color}; font-weight: 700;">{mark}</td>
    <td valign="top" style="padding: 0 0 10px 0; font-family: {FONT}; font-size: 15px;
        line-height: 1.5; color: {INK};">{_e(item)}</td>
  </tr>""" for item in items)
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="margin: 0 0 18px 0;">{rows}
</table>"""


def _para(text: str, size: int = 16, color: str = INK, margin: str = "0 0 18px 0") -> str:
    return (f'<p style="margin: {margin}; font-family: {FONT}; font-size: {size}px; '
            f'line-height: 1.6; color: {color};">{_e(text)}</p>')


def _render_video(section: dict) -> str:
    url = section.get("url", "")
    title = section.get("title") or "Watch the video"
    thumbnail = fetch_video_thumbnail(url)
    # With images disabled the thumbnail is invisible, so the text link below it is not a
    # nicety -- it is the only thing that survives. It is always present, never
    # conditional on the image being missing.
    image_html = ""
    if thumbnail:
        image_html = f"""
  <a href="{_e(url)}" style="text-decoration: none;">
    <img src="{_e(thumbnail)}" alt="{_e(title)}" width="{CARD_WIDTH - 64}"
         style="display: block; width: 100%; max-width: {CARD_WIDTH - 64}px; height: auto;
                border-radius: 8px; border: 1px solid {RULE};">
  </a>"""
    return f"""
<div style="margin: 0 0 20px 0;">{image_html}
  <a href="{_e(url)}" style="display: inline-block; margin-top: 8px; font-family: {FONT};
     font-size: 14px; color: {LINK}; text-decoration: none;">&#9654;&nbsp;{_e(title)}</a>
</div>"""


def _render_quote(section: dict) -> str:
    """Text-kind asset sections (a testimonial, a text block). A left rule rather than
    quotation marks, so it reads as a quote without the renderer inventing punctuation
    around content it did not write."""
    title = section.get("title")
    title_html = (f'<div style="font-family: {FONT}; font-size: 12px; color: {INK_MUTED}; '
                  f'margin-top: 8px;">{_e(title)}</div>') if title else ""
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="margin: 0 0 20px 0;">
  <tr>
    <td style="padding: 2px 0 2px 16px; border-left: 3px solid {RULE};">
      <div style="font-family: {FONT}; font-size: 15px; line-height: 1.6; color: {INK};
           font-style: italic;">{_e(section.get('text'))}</div>{title_html}
    </td>
  </tr>
</table>"""


def _render_cta(section: dict) -> str:
    headline = section.get("headline")
    subtext = section.get("subtext")
    button_url = section.get("button_url")
    inner = ""
    if headline:
        inner += (f'<div style="font-family: {FONT}; font-size: 17px; font-weight: 700; '
                  f'color: {INK}; margin: 0 0 6px 0;">{_e(headline)}</div>')
    if subtext:
        inner += (f'<div style="font-family: {FONT}; font-size: 14px; line-height: 1.5; '
                  f'color: {INK_MUTED}; margin: 0 0 14px 0;">{_e(subtext)}</div>')
    if button_url:
        inner += _button(button_url, section.get("button_label") or "See the demo")
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="margin: 4px 0 20px 0; background: {CANVAS}; border-radius: 8px;">
  <tr><td style="padding: 20px;">{inner}</td></tr>
</table>"""


def _render_interest(section: dict) -> str:
    """Phase 12 supplies real signed URLs. Rendered only when they exist -- a dead
    Yes/No pair would be worse than no question at all."""
    yes_url, no_url = section.get("yes_url"), section.get("no_url")
    if not yes_url or not no_url:
        return ""
    prompt = section.get("prompt") or "Would this be worth a look?"
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="margin: 0 0 20px 0; border-top: 1px solid {RULE}; border-bottom: 1px solid {RULE};">
  <tr><td style="padding: 18px 0;">
    <div style="font-family: {FONT}; font-size: 15px; color: {INK}; margin: 0 0 12px 0;">{_e(prompt)}</div>
    <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
      <td style="padding-right: 10px;">{_button(yes_url, section.get('yes_label') or "Yes, tell me more")}</td>
      <td>{_button(no_url, section.get('no_label') or "Not right now", primary=False)}</td>
    </tr></table>
  </td></tr>
</table>"""


def _render_contact(section: dict) -> str:
    """Step 11.4 supplies these from settings. Each line is independently optional, so a
    business that has not filled in (say) a profile link simply has one fewer line."""
    rows = ""
    for label, value, href in section.get("items") or []:
        shown = (f'<a href="{_e(href)}" style="color: {LINK}; text-decoration: none;">{_e(value)}</a>'
                 if href else _e(value))
        rows += f"""
  <tr>
    <td valign="top" style="padding: 0 12px 6px 0; font-family: {FONT}; font-size: 13px;
        color: {INK_MUTED}; white-space: nowrap;">{_e(label)}</td>
    <td valign="top" style="padding: 0 0 6px 0; font-family: {FONT}; font-size: 13px;
        color: {INK};">{shown}</td>
  </tr>"""
    if not rows:
        return ""
    heading = section.get("heading") or "Get in touch"
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="margin: 0 0 4px 0; border-top: 1px solid {RULE};">
  <tr><td style="padding: 18px 0 0 0;">
    <div style="font-family: {FONT}; font-size: 13px; font-weight: 700; color: {INK};
         margin: 0 0 10px 0;">{_e(heading)}</div>
    <table role="presentation" cellpadding="0" cellspacing="0" border="0">{rows}
    </table>
  </td></tr>
</table>"""


def _render_section(section: dict) -> str:
    kind = section.get("type")
    if kind == "HOOK":
        return _para(section.get("text"), size=16)
    if kind == "PAIN_POINTS":
        return _bullet_list(section.get("items") or [], "&#9679;", PAIN_MARK)
    if kind == "SOLUTION":
        return _bullet_list(section.get("items") or [], "&#10003;", GAIN_MARK)
    if kind == "VIDEO":
        return _render_video(section)
    if kind == "CTA":
        return _render_cta(section)
    if kind == "INTEREST":
        return _render_interest(section)
    if kind == "CONTACT":
        return _render_contact(section)
    # Any other asset-backed section, including ones added to ASSET_SECTIONS later: a
    # url-kind renders as a button, a text-kind as a quote. Handled generically on
    # purpose -- a new optional section should not need a new branch here either.
    if section.get("url"):
        return f'<div style="margin: 0 0 20px 0;">{_button(section["url"], section.get("title") or "Take a look", primary=False)}</div>'
    if section.get("text"):
        return _render_quote(section)
    return ""


def render_email_html(sections: list[dict], unsubscribe_url: str,
                      company_address: str | None = None) -> str:
    """The full email document. `sections` is Step 11.1's ordered list; the compliance
    footer is appended here and is never the agent's responsibility -- the same rule
    email_service._build_footer() already enforces for the plain-text part."""
    body = "".join(_render_section(s) for s in sections or [])
    address = _e(company_address if company_address is not None else Config.COMPANY_PHYSICAL_ADDRESS)
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin: 0; padding: 0; background: {CANVAS};">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background: {CANVAS};">
  <tr>
    <td align="center" style="padding: 24px 12px;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="{CARD_WIDTH}"
             style="width: 100%; max-width: {CARD_WIDTH}px; background: {CARD};
                    border: 1px solid {RULE}; border-radius: 12px;">
        <tr><td style="padding: 32px;">{body}</td></tr>
        <tr>
          <td style="padding: 18px 32px 24px 32px; border-top: 1px solid {RULE};">
            <div style="font-family: {FONT}; font-size: 12px; line-height: 1.5; color: {INK_MUTED};">{address}</div>
            <div style="margin-top: 10px;">
              <a href="{_e(unsubscribe_url)}" style="font-family: {FONT}; font-size: 12px;
                 color: {INK_MUTED};">Unsubscribe</a>
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>"""
