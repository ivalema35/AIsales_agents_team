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
import base64
import html
import logging
import re
from pathlib import Path

import requests

from config import Config

logger = logging.getLogger(__name__)

# Bundled brand mark (operator-supplied Infotech logo). Served publicly for real sends;
# Daily Review preview embeds it as a data URI so the iframe works without a network fetch.
_LOGO_PATH = Path(__file__).resolve().parents[2] / "static" / "brand" / "ivinfotech-logo.png"
_LOGO_DISPLAY_WIDTH = 168
_LOGO_DISPLAY_HEIGHT = 37
_logo_data_uri_cache: str | None = None

# One place to tune the whole design. Kept as plain constants (not a CSS file) because
# every value below has to end up inlined on an element anyway.
#
# Brief (2026-09-05 polish): still "a real person's well-formatted email", but the open
# must earn a second look in a crowded inbox -- navy brand bar, accent-edged section
# cards, and a clearer CTA -- without tipping into saturated marketing-blast territory.
INK = "#101828"          # primary text
INK_MUTED = "#667085"    # secondary text
RULE = "#e4e7ec"         # hairlines and borders
CANVAS = "#e8ecf2"       # area around the card (slightly cooler, more contrast)
CARD = "#ffffff"
# Real IVinfotech brand navy (from their site) + a warm gold accent for attention
# without reading as a promo orange CTA.
BRAND = "#0b1c3c"
BRAND_SOFT = "#eef2f8"   # tinted panels
GOLD = "#b8892c"         # attention accent (underline, card edge, interest cue)
GOLD_SOFT = "#f8f1e3"
ACCENT = BRAND           # primary button fill
ACCENT_TEXT = "#ffffff"
LINK = "#1552b0"

# Section headings. A premium transactional email groups content under short labels
# rather than running it together (the operator's own Hostinger reference does exactly
# this: "Here are the key details", "Plan details", "Useful resources"). Kept as
# constants so the wording is tunable in one place.
HEADING_PAIN = "What we noticed"
HEADING_SOLUTION = "How we'd fix it"

# Icon badges. A coloured glyph on its own reads as clip-art; the same glyph centred in a
# soft tinted disc reads as a designed component, and it degrades gracefully -- Outlook
# squares the border-radius but keeps the tint, so the meaning survives either way.
WARN_FG, WARN_BG = "#b54708", "#fef3e2"    # amber -- a problem, not an alarm
GAIN_FG, GAIN_BG = "#067647", "#e7f6ef"    # green -- the answer to it
WARN_EDGE = "#f0b96b"
GAIN_EDGE = "#6fcf97"

FONT = ("'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', "
        "Helvetica, Arial, sans-serif")
CARD_WIDTH = 580
BODY_SIZE = 15
LINE_HEIGHT = "1.62"

# An asset's title is written by the operator for their own reference in the dashboard
# ("demo url", "video url", "video_url") and then appears on a customer-facing button.
# Caught on the first real send: the button genuinely read "demo url". A title that is
# really a field name rather than a label is replaced with the section's proper fallback
# -- narrow on purpose, so a real label like "See our 2-minute walkthrough" is never
# overridden.
_FIELD_NAME_WORDS = ("url", "link", "asset")


def _label_or_fallback(title: str, fallback: str) -> str:
    t = (title or "").strip()
    if not t:
        return fallback
    # Underscored field names ("video_url") must split the same as spaced ones ("video url").
    words = t.lower().replace("_", " ").replace("-", " ").split()
    if len(words) <= 3 and any(w.strip(":-") in _FIELD_NAME_WORDS for w in words):
        return fallback
    return t


def _youtube_video_id(video_url: str) -> str | None:
    """Extract a YouTube / Shorts / youtu.be id from a real URL. None if not YouTube."""
    u = video_url or ""
    patterns = (
        r"(?:youtube\.com/watch\?(?:[^#]*&)?v=)([A-Za-z0-9_-]{6,})",
        r"(?:youtu\.be/)([A-Za-z0-9_-]{6,})",
        r"(?:youtube\.com/shorts/)([A-Za-z0-9_-]{6,})",
        r"(?:youtube\.com/embed/)([A-Za-z0-9_-]{6,})",
    )
    for pat in patterns:
        m = re.search(pat, u)
        if m:
            return m.group(1)
    return None


def _youtube_is_shorts(video_url: str) -> bool:
    return "/shorts/" in (video_url or "").lower()


def _jpeg_dimensions(url: str) -> tuple[int, int] | None:
    """Width, height from a remote JPEG's SOF marker (first ~64KB). None on failure."""
    try:
        resp = requests.get(url, timeout=5, stream=True)
        resp.raise_for_status()
        buf = b""
        for chunk in resp.iter_content(65536):
            buf += chunk
            if len(buf) >= 65536:
                break
        i = 0
        while i < len(buf) - 8:
            if buf[i] == 0xFF and buf[i + 1] in (0xC0, 0xC1, 0xC2):
                h = int.from_bytes(buf[i + 5:i + 7], "big")
                w = int.from_bytes(buf[i + 7:i + 9], "big")
                return w, h
            i += 1
    except Exception:  # noqa: BLE001 - display-only probe
        return None
    return None


def resolve_video_thumb(video_url: str) -> tuple[str | None, str]:
    """Return (thumbnail_url, layout) where layout is 'portrait' (9:16) or 'landscape'.

    YouTube Shorts (and any vertical oar2 still) get the real 9:16 `oar2.jpg` — NOT
    `hqdefault`, which YouTube paints with blur pillarboxes inside a 16:9 frame (caught
    live 2026-09-09). Landscape watch URLs keep `hqdefault`.
    """
    try:
        if "youtube.com" in video_url or "youtu.be" in video_url:
            vid = _youtube_video_id(video_url)
            if not vid:
                resp = requests.get("https://www.youtube.com/oembed",
                                    params={"url": video_url, "format": "json"}, timeout=5)
                resp.raise_for_status()
                thumb = resp.json().get("thumbnail_url")
                return (thumb, "landscape") if thumb else (None, "landscape")
            oar = f"https://i.ytimg.com/vi/{vid}/oar2.jpg"
            if _youtube_is_shorts(video_url):
                return oar, "portrait"
            dims = _jpeg_dimensions(oar)
            if dims and dims[1] > dims[0]:
                return oar, "portrait"
            return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg", "landscape"
        if "vimeo.com" in video_url:
            resp = requests.get("https://vimeo.com/api/oembed.json",
                                params={"url": video_url}, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            thumb = data.get("thumbnail_url")
            w, h = data.get("thumbnail_width") or 0, data.get("thumbnail_height") or 0
            layout = "portrait" if h > w else "landscape"
            return (thumb, layout) if thumb else (None, "landscape")
    except Exception as exc:  # noqa: BLE001 - display-only, must never break a real send
        logger.warning("video thumbnail lookup failed for %s: %s", video_url, exc)
    return None, "landscape"


def fetch_video_thumbnail(video_url: str) -> str | None:
    """Backward-compatible helper — URL only. Prefer `resolve_video_thumb` for layout."""
    thumb, _layout = resolve_video_thumb(video_url)
    return thumb


def _e(value) -> str:
    return html.escape(str(value or ""))


def _button(url: str, label: str, primary: bool = True) -> str:
    """A table-wrapped button. Outlook ignores padding on an inline `<a>`, so a styled
    anchor alone silently degrades to plain blue text there -- the table cell is what
    actually carries the shape. Sized to earn a click without reading as a promo blast."""
    bg = ACCENT if primary else CARD
    fg = ACCENT_TEXT if primary else INK
    border = "none" if primary else f"1px solid {RULE}"
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 0;">
  <tr>
    <td align="center" bgcolor="{bg}" style="border-radius: 8px; border: {border};">
      <a href="{_e(url)}" style="display: inline-block; padding: 12px 22px; font-family: {FONT};
         font-size: 15px; font-weight: 700; color: {fg}; text-decoration: none; border-radius: 8px;
         letter-spacing: 0.1px;">{_e(label)}</a>
    </td>
  </tr>
</table>"""


def _badge(glyph: str, fg: str, bg: str) -> str:
    """A glyph centred in a soft tinted disc. Built as a fixed-size table cell rather than
    a styled span because line-height/vertical-centring on an inline element is one of the
    least reliable things across mail clients -- a cell with matching width, height and
    line-height centres correctly in all of them."""
    return f"""<table role="presentation" cellpadding="0" cellspacing="0" border="0">
  <tr><td width="26" height="26" align="center" valign="middle" bgcolor="{bg}"
          style="width: 26px; height: 26px; border-radius: 13px; font-family: {FONT};
                 font-size: 13px; line-height: 26px; font-weight: 700; color: {fg};">{glyph}</td></tr>
</table>"""


def _card(inner: str, tint: bool = False, margin_bottom: int = 20,
          edge: str | None = None, panel_bg: str | None = None) -> str:
    """A bordered, rounded panel. Optional `edge` paints a 4px left accent strip so pain /
    solution / CTA blocks read as distinct at a glance in a crowded inbox."""
    bg = panel_bg if panel_bg is not None else (BRAND_SOFT if tint else CARD)
    if edge:
        return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="margin: 0 0 {margin_bottom}px 0;">
  <tr>
    <td width="4" bgcolor="{edge}" style="width: 4px; background: {edge};
        border-radius: 10px 0 0 10px; font-size: 0; line-height: 0;">&nbsp;</td>
    <td bgcolor="{bg}" style="padding: 18px 20px; border: 1px solid {RULE}; border-left: none;
        border-radius: 0 10px 10px 0;">{inner}</td>
  </tr>
</table>"""
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="margin: 0 0 {margin_bottom}px 0;">
  <tr><td bgcolor="{bg}" style="padding: 20px 22px; border: 1px solid {RULE};
      border-radius: 10px;">{inner}</td></tr>
</table>"""


def _heading(text: str, color: str = INK_MUTED) -> str:
    return (f'<div style="font-family: {FONT}; font-size: 12px; font-weight: 700; '
            f'letter-spacing: 0.7px; text-transform: uppercase; color: {color}; '
            f'margin: 0 0 14px 0;">{_e(text)}</div>')


def _bullet_list(items, glyph: str, fg: str, bg: str, heading: str = "",
                 edge: str | None = None, panel_bg: str | None = None,
                 heading_color: str = INK_MUTED) -> str:
    """A two-column table per bullet rather than `<ul>`: list-marker styling is one of the
    least consistent things across mail clients, and the marker here carries real meaning
    (a problem vs. an answer to it), so it cannot be left to the client to decide."""
    badge = _badge(glyph, fg, bg)
    last = len(items) - 1
    rows = "".join(f"""
  <tr>
    <td valign="top" width="26" style="padding: 1px 12px {0 if i == last else 12}px 0;">{badge}</td>
    <td valign="top" style="padding: 0 0 {0 if i == last else 12}px 0; font-family: {FONT};
        font-size: {BODY_SIZE}px; line-height: {LINE_HEIGHT}; color: {INK}; font-weight: 500;">{_e(item)}</td>
  </tr>""" for i, item in enumerate(items))
    body = f"""<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">{rows}
</table>"""
    return _card((_heading(heading, heading_color) if heading else "") + body,
                 edge=edge, panel_bg=panel_bg)


def _para(text: str, size: int = BODY_SIZE, color: str = INK, margin: str = "0 0 20px 0") -> str:
    return (f'<p style="margin: {margin}; font-family: {FONT}; font-size: {size}px; '
            f'line-height: {LINE_HEIGHT}; color: {color};">{_e(text)}</p>')


def _prose_block(items, heading: str = "", edge: str | None = None,
                 panel_bg: str | None = None, heading_color: str = INK_MUTED) -> str:
    """Phase 16 Step 16.4 -- the model-chosen alternative to _bullet_list() for a product
    whose admin wants a shorter, plain-text-reading style. Same safe, pre-built card as
    _bullet_list() (still table-based, still inline-styled, still one real email-safe
    primitive), just the points woven into one flowing paragraph instead of separate
    badge rows -- never raw model-authored markup either way."""
    text = " ".join(item.rstrip(".") + "." for item in items)
    inner = (_heading(heading, heading_color) if heading else "") + _para(text, margin="0")
    return _card(inner, edge=edge, panel_bg=panel_bg)


def _render_video(section: dict) -> str:
    """Clickable video card — portrait (9:16) or landscape, matching the real video.

    2026-09-09: Shorts must use `oar2.jpg` (true 9:16) inside a phone-width card. Using
    `hqdefault` stretches a blur-pillarboxed 16:9 still across the email and looks broken.
    Caption never shows raw field names (`video_url`). Images-off still leaves the CTA.
    """
    url = section.get("url", "")
    title = _label_or_fallback(section.get("title"), "Watch the video")
    thumbnail, layout = resolve_video_thumb(url)
    portrait = layout == "portrait"
    # Portrait ≈ phone preview; landscape ≈ near content width.
    thumb_width = 280 if portrait else 520
    image_html = ""
    if thumbnail:
        image_html = f"""
      <a href="{_e(url)}" style="text-decoration: none; display: block; line-height: 0;">
        <img src="{_e(thumbnail)}" alt="{_e(title)}" width="{thumb_width}"
             style="display: block; width: 100%; max-width: {thumb_width}px; height: auto;
                    border: 0; outline: none; text-decoration: none;">
      </a>"""
    eyebrow = "Short video" if portrait else "Video"
    # Outer table centers a portrait phone-card; landscape stays full content width.
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="margin: 0 0 26px 0;">
  <tr>
    <td align="center">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0"
             width="{thumb_width}" style="width: 100%; max-width: {thumb_width}px;">
        <tr>
          <td style="border: 1px solid {RULE}; border-radius: 14px; overflow: hidden;
                     box-shadow: 0 8px 24px rgba(11,28,60,0.12); background: {CARD};">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td bgcolor="{BRAND}" style="background: {BRAND}; padding: 10px 14px 8px 14px;">
                  <div style="font-family: {FONT}; font-size: 10px; font-weight: 700;
                       letter-spacing: 1.2px; text-transform: uppercase; color: {GOLD};">
                    {eyebrow}
                  </div>
                </td>
              </tr>
            </table>
            {image_html}
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td bgcolor="{GOLD}" style="background: {GOLD}; height: 3px; font-size: 0;
                    line-height: 0;">&nbsp;</td>
              </tr>
              <tr>
                <td bgcolor="{BRAND}" style="background: {BRAND}; padding: 16px 14px;">
                  <a href="{_e(url)}" style="display: block; text-align: center;
                     font-family: {FONT}; font-size: 15px; font-weight: 700;
                     color: {ACCENT_TEXT}; text-decoration: none; letter-spacing: 0.2px;">
                    <span style="display: inline-block; width: 28px; height: 28px;
                          line-height: 28px; text-align: center; border-radius: 14px;
                          background: {GOLD}; color: {BRAND}; font-size: 12px;
                          margin-right: 10px; vertical-align: middle;">&#9658;</span>
                    <span style="vertical-align: middle;">{_e(title)}</span>
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>"""


def _render_quote(section: dict) -> str:
    """Text-kind asset sections (a testimonial, a text block). A left rule rather than
    quotation marks, so it reads as a quote without the renderer inventing punctuation
    around content it did not write."""
    title = section.get("title")
    title_html = (f'<div style="font-family: {FONT}; font-size: 12px; color: {INK_MUTED}; '
                  f'margin-top: 7px;">{_e(title)}</div>') if title else ""
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="margin: 0 0 22px 0;">
  <tr>
    <td style="padding: 2px 0 2px 15px; border-left: 2px solid {RULE};">
      <div style="font-family: {FONT}; font-size: {BODY_SIZE}px; line-height: {LINE_HEIGHT};
           color: {INK_MUTED};">{_e(section.get('text'))}</div>{title_html}
    </td>
  </tr>
</table>"""


def _render_cta(section: dict) -> str:
    """CTA as the visual climax: gold-edged navy-soft panel + bold primary button, so the
    ask is unmistakable without a saturated banner that reads as bought ads."""
    headline = section.get("headline")
    subtext = section.get("subtext")
    button_url = section.get("button_url")
    inner = ""
    if headline:
        inner += (f'<div style="font-family: {FONT}; font-size: {BODY_SIZE + 2}px; font-weight: 700; '
                  f'color: {BRAND}; margin: 0 0 6px 0;">{_e(headline)}</div>')
    if subtext:
        inner += (f'<div style="font-family: {FONT}; font-size: 14px; line-height: {LINE_HEIGHT}; '
                  f'color: {INK_MUTED}; margin: 0 0 16px 0;">{_e(subtext)}</div>')
    if button_url:
        inner += _button(button_url,
                         _label_or_fallback(section.get("button_label"), "See the demo"))
    return _card(inner, edge=GOLD, panel_bg=BRAND_SOFT)


def _render_interest(section: dict) -> str:
    """Phase 12 supplies real signed URLs. Rendered only when they exist -- a dead
    Yes/No pair would be worse than no question at all. Framed as a clear decision strip
    so it doesn't get lost under the body."""
    yes_url, no_url = section.get("yes_url"), section.get("no_url")
    if not yes_url or not no_url:
        return ""
    prompt = section.get("prompt") or "Would this be worth a look?"
    inner = (
        f'<div style="font-family: {FONT}; font-size: {BODY_SIZE + 1}px; font-weight: 600; '
        f'color: {INK}; margin: 0 0 14px 0;">{_e(prompt)}</div>'
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td style="padding-right: 10px;">{_button(yes_url, section.get("yes_label") or "Yes, tell me more")}</td>'
        f'<td>{_button(no_url, section.get("no_label") or "Not right now", primary=False)}</td>'
        f'</tr></table>'
    )
    return _card(inner, edge=BRAND, panel_bg=GOLD_SOFT, margin_bottom=22)


def _render_cross_sell(section: dict) -> str:
    """A small, brand-tinted callout -- highlighted enough to be noticed on its own, but
    still deliberately smaller and quieter than the CTA panel above it, so it reads as a
    secondary note rather than competing with the actual pitch."""
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 0 0 20px 0;">
  <tr>
    <td bgcolor="{BRAND_SOFT}" style="padding: 12px 14px; border-radius: 8px; border-left: 3px solid {GOLD};">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
        <td valign="middle" style="padding-right: 8px; font-family: {FONT}; font-size: 13px;
            font-weight: 700; color: {GOLD};">+</td>
        <td valign="middle" style="font-family: {FONT}; font-size: 13px; font-weight: 600;
            color: {BRAND};">{_e(section.get('text'))}</td>
      </tr></table>
    </td>
  </tr>
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
    inner = (_heading(heading) +
             f'<table role="presentation" cellpadding="0" cellspacing="0" border="0">{rows}</table>')
    return _card(inner, margin_bottom=4)


def _render_section(section: dict) -> str:
    kind = section.get("type")
    if kind == "HOOK":
        return _para(section.get("text"), size=BODY_SIZE + 1, margin="0 0 22px 0")
    if kind == "PAIN_POINTS":
        items = section.get("items") or []
        if section.get("layout") == "PROSE":
            return _prose_block(items, heading=HEADING_PAIN, edge=WARN_EDGE,
                               panel_bg=WARN_BG, heading_color=WARN_FG)
        # A plain "!" rather than the warning-sign character. U+26A0 is an emoji
        # codepoint, and the text-presentation selector that is supposed to suppress that
        # is widely ignored -- so it kept rendering as a client's own glossy multi-colour
        # triangle, which is exactly the non-flat look this design is avoiding, and in a
        # palette the design never chose. An exclamation in a tinted disc is the standard
        # flat warning treatment and can never be substituted for an emoji.
        return _bullet_list(items, "!", WARN_FG, WARN_BG, heading=HEADING_PAIN,
                            edge=WARN_EDGE, panel_bg="#fffaf3", heading_color=WARN_FG)
    if kind == "SOLUTION":
        items = section.get("items") or []
        if section.get("layout") == "PROSE":
            return _prose_block(items, heading=HEADING_SOLUTION, edge=GAIN_EDGE,
                               panel_bg=GAIN_BG, heading_color=GAIN_FG)
        # U+2713 is not an emoji codepoint, so it stays flat and takes our own colour.
        return _bullet_list(items, "&#10003;", GAIN_FG, GAIN_BG, heading=HEADING_SOLUTION,
                            edge=GAIN_EDGE, panel_bg="#f3faf6", heading_color=GAIN_FG)
    if kind == "VIDEO":
        return _render_video(section)
    if kind == "CTA":
        return _render_cta(section)
    if kind == "INTEREST":
        return _render_interest(section)
    if kind == "CONTACT":
        return _render_contact(section)
    if kind == "CROSS_SELL":
        return _render_cross_sell(section)
    if kind == "SERVICES_LIST":
        # Phase 13 Step 13.1 -- Level 3's standing-offer bullet list. Neutral brand tint
        # (not the amber "problem"/green "answer" colors PAIN_POINTS/SOLUTION use) --
        # this is reference information, not a claim about the lead, and a plain bullet
        # glyph rather than a badge icon keeps it reading as a quiet reference list, not
        # another pitch.
        return _bullet_list(section.get("items") or [], "&#8226;", BRAND, BRAND_SOFT,
                            heading="What we offer", edge=BRAND, panel_bg=BRAND_SOFT)
    # Any other asset-backed section, including ones added to ASSET_SECTIONS later: a
    # url-kind renders as a button, a text-kind as a quote. Handled generically on
    # purpose -- a new optional section should not need a new branch here either.
    if section.get("url"):
        label = _label_or_fallback(section.get("title"), "Take a look")
        return f'<div style="margin: 0 0 22px 0;">{_button(section["url"], label, primary=False)}</div>'
    if section.get("text"):
        return _render_quote(section)
    return ""


def _brand_wordmark(size: int = 17, color: str = BRAND) -> str:
    """Text fallback for the brand mark -- always renders with images blocked, so the
    footer (and img alt text) still identify who this is from."""
    return (f'<span style="font-family: {FONT}; font-size: {size}px; font-weight: 700; '
            f'letter-spacing: -0.2px; color: {color};">IV<span style="font-weight: 400;">infotech</span></span>')


def _logo_public_url() -> str:
    # 2026-09-10, real live bug fixed: production's webserver only proxies "/api/" to
    # Flask (see reference_production_static_file_serving finding) -- "/static/..." was
    # never actually reachable, so this logo has been a broken image in every real
    # outbound email since it was added, confirmed live by a user-shared screenshot.
    # Moved the file to frontend/public/brand/ so Vite copies it into every build's
    # frontend/dist/brand/ automatically -- the one path this webserver demonstrably
    # does serve (same pattern already proven for the uploads/ folder).
    return f"{Config.PUBLIC_BASE_URL.rstrip('/')}/brand/ivinfotech-logo.png"


def _logo_data_uri() -> str | None:
    """Base64-embed the logo for CRM preview iframes (srcDoc can't reliably load auth-
    gated or cross-origin assets). Real sends use the public URL -- Gmail strips data URIs.
    Returns None (never raises) if the asset file is ever missing/unreadable -- a real
    lead's send, and this campaign's whole Daily Review preview, must never 500 just
    because one logo file didn't make it into a deploy; the header falls back to the
    existing text wordmark instead (see _header())."""
    global _logo_data_uri_cache
    if _logo_data_uri_cache is None:
        try:
            raw = _LOGO_PATH.read_bytes()
        except OSError:
            return None
        _logo_data_uri_cache = "data:image/png;base64," + base64.b64encode(raw).decode("ascii")
    return _logo_data_uri_cache


def _logo_img(logo_src: str) -> str:
    return (
        f'<img src="{_e(logo_src)}" alt="IVinfotech" width="{_LOGO_DISPLAY_WIDTH}" '
        f'height="{_LOGO_DISPLAY_HEIGHT}" style="display: block; width: {_LOGO_DISPLAY_WIDTH}px; '
        f'height: {_LOGO_DISPLAY_HEIGHT}px; border: 0; outline: none; text-decoration: none;">'
    )


def _header(logo_src: str | None) -> str:
    """White brand strip with the real Infotech logo (dark mark needs a light ground),
    capped by the gold accent line so the open still grabs attention. Falls back to the
    existing text wordmark if logo_src is falsy (e.g. the asset file was missing) --
    never lets a missing image break the header/whole send."""
    mark = _logo_img(logo_src) if logo_src else _brand_wordmark(20, BRAND)
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
  <tr>
    <td bgcolor="{CARD}" style="background: {CARD}; padding: 20px 28px 18px 28px;">
      {mark}
    </td>
  </tr>
  <tr>
    <td bgcolor="{GOLD}" style="background: {GOLD}; height: 3px; font-size: 0; line-height: 0;">&nbsp;</td>
  </tr>
</table>"""


def pick_header_image_url(content_assets) -> str | None:
    """Best IMAGE_URL for the email header banner (product or global).

    2026-09-09: IMAGE_URL is a banner under the logo strip — not an ASSET_SECTIONS mid-body
    block. A product may have both a WhatsApp header and an Email Header; we prefer titles
    that look like email banners, then any non-WhatsApp title, then the first IMAGE_URL.
    Missing asset = no banner (graceful omission), never a fabricated image.
    """
    images = []
    for asset in content_assets or []:
        if not isinstance(asset, dict):
            continue
        if asset.get("asset_type") != "IMAGE_URL":
            continue
        value = (asset.get("value") or "").strip()
        if value:
            images.append(asset)
    if not images:
        return None

    def _title(a: dict) -> str:
        return (a.get("title") or "").strip().lower()

    for asset in images:
        t = _title(asset)
        if "email" in t or "banner" in t:
            return (asset.get("value") or "").strip()
    for asset in images:
        t = _title(asset)
        if "whatsapp" not in t and not t.startswith("wa ") and "wa header" not in t:
            return (asset.get("value") or "").strip()
    return (images[0].get("value") or "").strip() or None


def _header_image_data_uri(url: str) -> str | None:
    """Embed a local public/upload image for Daily Review iframe (same idea as logo).

    Real sends keep an absolute http(s) URL so mail clients can fetch it. Preview iframes
    often cannot load relative paths from srcDoc, so we prefer a data URI when the file
    exists under frontend/public, frontend/dist, or backend/static.
    """
    from urllib.parse import urlparse

    raw = (url or "").strip()
    if not raw or raw.startswith("data:"):
        return None
    path_part = urlparse(raw).path if raw.startswith("http") else raw
    if not path_part.startswith("/"):
        return None
    rel = path_part.lstrip("/")
    repo_root = Path(__file__).resolve().parents[3]
    candidates = (
        repo_root / "frontend" / "public" / rel,
        repo_root / "frontend" / "dist" / rel,
        Path(__file__).resolve().parents[2] / "static" / rel,
    )
    for candidate in candidates:
        try:
            if not candidate.is_file():
                continue
            if candidate.stat().st_size > 2_000_000:
                continue
            data = candidate.read_bytes()
            suffix = candidate.suffix.lower().lstrip(".")
            mime = {
                "png": "image/png",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "gif": "image/gif",
                "webp": "image/webp",
            }.get(suffix, "image/png")
            return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
        except OSError:
            continue
    return None


def resolve_image_src_for_email(url: str, *, for_preview: bool = False) -> str:
    """Absolute URL for real sends; preview may embed a local file as data URI.

    Relative paths like `/uploads/...` or `/wa-header-....png` are joined to PUBLIC_BASE_URL
    so outbound mail clients can fetch them.
    """
    u = (url or "").strip()
    if not u:
        return ""
    if u.startswith("data:"):
        return u
    if for_preview:
        embedded = _header_image_data_uri(u)
        if embedded:
            return embedded
    if u.startswith("http://") or u.startswith("https://"):
        return u
    base = (Config.PUBLIC_BASE_URL or "").rstrip("/")
    if u.startswith("/"):
        return f"{base}{u}" if base else u
    return f"{base}/{u}" if base else u


def _hero_banner(image_src: str) -> str:
    """Full-bleed product header image under the logo/gold strip. Table-based, images-off
    safe (alt text); never required for the email to render."""
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
  <tr>
    <td style="padding: 0; line-height: 0; font-size: 0;">
      <img src="{_e(image_src)}" alt="" width="{CARD_WIDTH}"
           style="display: block; width: 100%; max-width: {CARD_WIDTH}px; height: auto;
                  border: 0; outline: none; text-decoration: none;">
    </td>
  </tr>
</table>"""


def _headline(text: str) -> str:
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="margin: 0 0 18px 0;">
  <tr>
    <td style="padding: 0 0 12px 0;">
      <div style="font-family: {FONT}; font-size: 24px; line-height: 1.28; font-weight: 700;
           color: {BRAND};">{_e(text)}</div>
    </td>
  </tr>
  <tr>
    <td width="56" bgcolor="{GOLD}" style="width: 56px; height: 3px; background: {GOLD};
        font-size: 0; line-height: 0; border-radius: 2px;">&nbsp;</td>
  </tr>
</table>"""


def render_email_html(sections: list[dict], unsubscribe_url: str,
                      company_address: str | None = None, headline: str | None = None,
                      for_preview: bool = False, header_image_url: str | None = None) -> str:
    """The full email document. `sections` is Step 11.1's ordered list; the compliance
    footer is appended here and is never the agent's responsibility -- the same rule
    email_service._build_footer() already enforces for the plain-text part.

    `headline` is normally the subject line, shown again as the page's own heading. That
    repetition is deliberate and is what almost every well-made transactional email does:
    the subject is gone from view the moment the message is opened, so without it the
    reader has no title to anchor on and the email opens mid-sentence.

    `for_preview=True` embeds the logo as a data URI (Daily Review iframe). Real sends
    leave it False so the public `/static/brand/` URL is used -- deliverable inboxes.

    `header_image_url` (2026-09-09): optional product IMAGE_URL banner under the logo strip.
    Omitted when the product has no active IMAGE_URL asset.
    """
    logo_src = _logo_data_uri() if for_preview else _logo_public_url()
    banner_html = ""
    if header_image_url:
        src = resolve_image_src_for_email(header_image_url, for_preview=for_preview)
        if src:
            banner_html = _hero_banner(src)
    inner = ""
    if headline:
        inner += _headline(headline)
    inner += "".join(_render_section(s) for s in sections or [])
    address = _e(company_address if company_address is not None else Config.COMPANY_PHYSICAL_ADDRESS)
    # Brand strip sits flush to the top of the card. Compliance footer sits OUTSIDE.
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin: 0; padding: 0; background: {CANVAS}; -webkit-font-smoothing: antialiased;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background: {CANVAS};">
  <tr>
    <td align="center" style="padding: 28px 12px 36px 12px;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="{CARD_WIDTH}"
             style="width: 100%; max-width: {CARD_WIDTH}px;">
        <tr>
          <td style="background: {CARD}; border: 1px solid {RULE}; border-radius: 12px;
                     overflow: hidden; box-shadow: 0 4px 14px rgba(11,28,60,0.08);">
            {_header(logo_src)}
            {banner_html}
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td style="padding: 28px 30px 30px 30px;">{inner}</td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td align="center" style="padding: 22px 34px 0 34px;">
            <div style="margin: 0 0 8px 0;">{_brand_wordmark(14, INK_MUTED)}</div>
            <div style="font-family: {FONT}; font-size: 12px; line-height: 1.6; color: {INK_MUTED};">{address}</div>
            <div style="margin-top: 8px;">
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
