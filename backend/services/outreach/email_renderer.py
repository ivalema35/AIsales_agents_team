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
#
# The design brief is "a real person's well-formatted email, not a campaign", and several
# choices below exist specifically to avoid reading as a marketing template:
#
# - **No colored icon bullets.** A red-dot list next to a green-tick list is one of the
#   most recognisable template signals there is. The two lists are distinguished
#   typographically instead -- a quiet dot for what is wrong, an arrow for what answers
#   it -- which carries the same meaning without looking designed at someone.
# - **Near-black buttons, not a saturated brand colour.** A bright orange/blue CTA reads
#   as an ad; a restrained dark button reads as a link someone meant you to click.
# - **A narrower column.** 560px with 34px padding puts the measure at roughly 65-75
#   characters, which is the comfortable reading range. The earlier 600px card ran wide
#   enough that long lines started to feel like body copy in a newsletter.
# - **Nothing is centred.** Real email is left-aligned; centred text is a layout choice
#   almost only campaigns make.
INK = "#101828"          # primary text
INK_MUTED = "#667085"    # secondary text
RULE = "#e4e7ec"         # hairlines and borders
CANVAS = "#f2f4f7"       # the area around the card
CARD = "#ffffff"
# The real IVinfotech brand navy, taken from their own site rather than invented, so the
# email reads as coming from the same company as the website the CTA points at.
BRAND = "#0b1c3c"
BRAND_SOFT = "#eef2f8"   # tinted panels
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

FONT = ("'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', "
        "Helvetica, Arial, sans-serif")
CARD_WIDTH = 580
BODY_SIZE = 15
LINE_HEIGHT = "1.62"

# An asset's title is written by the operator for their own reference in the dashboard
# ("demo url", "video url") and then appears on a customer-facing button. Caught on the
# first real send: the button genuinely read "demo url". A title that is really a field
# name rather than a label is replaced with the section's proper fallback -- narrow on
# purpose, so a real label like "See our 2-minute walkthrough" is never overridden.
_FIELD_NAME_WORDS = ("url", "link", "asset")


def _label_or_fallback(title: str, fallback: str) -> str:
    t = (title or "").strip()
    if not t:
        return fallback
    words = t.lower().split()
    if len(words) <= 3 and any(w.strip(":-") in _FIELD_NAME_WORDS for w in words):
        return fallback
    return t


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
      <a href="{_e(url)}" style="display: inline-block; padding: 10px 18px; font-family: {FONT};
         font-size: 14px; font-weight: 600; color: {fg}; text-decoration: none; border-radius: 6px;">{_e(label)}</a>
    </td>
  </tr>
</table>"""


def _badge(glyph: str, fg: str, bg: str) -> str:
    """A glyph centred in a soft tinted disc. Built as a fixed-size table cell rather than
    a styled span because line-height/vertical-centring on an inline element is one of the
    least reliable things across mail clients -- a cell with matching width, height and
    line-height centres correctly in all of them."""
    return f"""<table role="presentation" cellpadding="0" cellspacing="0" border="0">
  <tr><td width="24" height="24" align="center" valign="middle" bgcolor="{bg}"
          style="width: 24px; height: 24px; border-radius: 12px; font-family: {FONT};
                 font-size: 13px; line-height: 24px; font-weight: 700; color: {fg};">{glyph}</td></tr>
</table>"""


def _card(inner: str, tint: bool = False, margin_bottom: int = 20) -> str:
    """A bordered, rounded panel. This is the single biggest thing separating a premium
    transactional email from a plain one: content grouped into distinct blocks instead of
    running as one continuous column."""
    bg = BRAND_SOFT if tint else CARD
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="margin: 0 0 {margin_bottom}px 0;">
  <tr><td bgcolor="{bg}" style="padding: 20px 22px; border: 1px solid {RULE};
      border-radius: 10px;">{inner}</td></tr>
</table>"""


def _heading(text: str) -> str:
    return (f'<div style="font-family: {FONT}; font-size: 12px; font-weight: 700; '
            f'letter-spacing: 0.6px; text-transform: uppercase; color: {INK_MUTED}; '
            f'margin: 0 0 14px 0;">{_e(text)}</div>')


def _bullet_list(items, glyph: str, fg: str, bg: str, heading: str = "") -> str:
    """A two-column table per bullet rather than `<ul>`: list-marker styling is one of the
    least consistent things across mail clients, and the marker here carries real meaning
    (a problem vs. an answer to it), so it cannot be left to the client to decide."""
    badge = _badge(glyph, fg, bg)
    last = len(items) - 1
    rows = "".join(f"""
  <tr>
    <td valign="top" width="24" style="padding: 1px 12px {0 if i == last else 12}px 0;">{badge}</td>
    <td valign="top" style="padding: 0 0 {0 if i == last else 12}px 0; font-family: {FONT};
        font-size: {BODY_SIZE}px; line-height: {LINE_HEIGHT}; color: {INK};">{_e(item)}</td>
  </tr>""" for i, item in enumerate(items))
    body = f"""<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">{rows}
</table>"""
    return _card((_heading(heading) if heading else "") + body)


def _para(text: str, size: int = BODY_SIZE, color: str = INK, margin: str = "0 0 20px 0") -> str:
    return (f'<p style="margin: {margin}; font-family: {FONT}; font-size: {size}px; '
            f'line-height: {LINE_HEIGHT}; color: {color};">{_e(text)}</p>')


def _render_video(section: dict) -> str:
    url = section.get("url", "")
    title = _label_or_fallback(section.get("title"), "Watch the walkthrough")
    thumbnail = fetch_video_thumbnail(url)
    # Deliberately NOT full width. A hero-sized image is the single loudest campaign
    # signal in an email; at ~380px it reads as something a person attached, which is
    # what it actually is.
    thumb_width = 400
    image_html = ""
    if thumbnail:
        image_html = f"""
      <a href="{_e(url)}" style="text-decoration: none; display: block;">
        <img src="{_e(thumbnail)}" alt="{_e(title)}" width="{thumb_width}"
             style="display: block; width: 100%; max-width: {thumb_width}px; height: auto;
                    border-radius: 8px 8px 0 0;">
      </a>"""
    # With images disabled the thumbnail is invisible, so the caption row below it is not
    # a nicety -- it is the only thing that survives. Always present, never conditional on
    # the image being missing, and it carries the play glyph so the row still reads as a
    # video rather than a stray link.
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0"
       style="margin: 0 0 24px 0; max-width: {thumb_width}px;">
  <tr>
    <td style="border: 1px solid {RULE}; border-radius: 8px;">{image_html}
      <a href="{_e(url)}" style="display: block; padding: 11px 14px; font-family: {FONT};
         font-size: 14px; font-weight: 600; color: {LINK}; text-decoration: none;
         border-top: 1px solid {RULE};">&#9658;&nbsp;&nbsp;{_e(title)}</a>
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
    """A softly tinted panel with a hairline, not a saturated banner. It needs enough
    presence to read as the one thing being asked, without becoming the loud coloured
    block that makes an email look bought rather than written."""
    headline = section.get("headline")
    subtext = section.get("subtext")
    button_url = section.get("button_url")
    inner = ""
    if headline:
        inner += (f'<div style="font-family: {FONT}; font-size: {BODY_SIZE + 1}px; font-weight: 600; '
                  f'color: {INK}; margin: 0 0 6px 0;">{_e(headline)}</div>')
    if subtext:
        inner += (f'<div style="font-family: {FONT}; font-size: 14px; line-height: {LINE_HEIGHT}; '
                  f'color: {INK_MUTED}; margin: 0 0 16px 0;">{_e(subtext)}</div>')
    if button_url:
        inner += _button(button_url,
                         _label_or_fallback(section.get("button_label"), "See the demo"))
    return _card(inner, tint=True)


def _render_interest(section: dict) -> str:
    """Phase 12 supplies real signed URLs. Rendered only when they exist -- a dead
    Yes/No pair would be worse than no question at all."""
    yes_url, no_url = section.get("yes_url"), section.get("no_url")
    if not yes_url or not no_url:
        return ""
    prompt = section.get("prompt") or "Would this be worth a look?"
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="margin: 0 0 22px 0; border-top: 1px solid {RULE};">
  <tr><td style="padding: 20px 0 0 0;">
    <div style="font-family: {FONT}; font-size: {BODY_SIZE}px; color: {INK}; margin: 0 0 12px 0;">{_e(prompt)}</div>
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
    inner = (_heading(heading) +
             f'<table role="presentation" cellpadding="0" cellspacing="0" border="0">{rows}</table>')
    return _card(inner, margin_bottom=4)


def _render_section(section: dict) -> str:
    kind = section.get("type")
    if kind == "HOOK":
        return _para(section.get("text"), size=BODY_SIZE + 1, margin="0 0 22px 0")
    if kind == "PAIN_POINTS":
        # A plain "!" rather than the warning-sign character. U+26A0 is an emoji
        # codepoint, and the text-presentation selector that is supposed to suppress that
        # is widely ignored -- so it kept rendering as a client's own glossy multi-colour
        # triangle, which is exactly the non-flat look this design is avoiding, and in a
        # palette the design never chose. An exclamation in a tinted disc is the standard
        # flat warning treatment and can never be substituted for an emoji.
        return _bullet_list(section.get("items") or [], "!", WARN_FG, WARN_BG,
                            heading=HEADING_PAIN)
    if kind == "SOLUTION":
        # U+2713 is not an emoji codepoint, so it stays flat and takes our own colour.
        return _bullet_list(section.get("items") or [], "&#10003;", GAIN_FG, GAIN_BG,
                            heading=HEADING_SOLUTION)
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
        label = _label_or_fallback(section.get("title"), "Take a look")
        return f'<div style="margin: 0 0 22px 0;">{_button(section["url"], label, primary=False)}</div>'
    if section.get("text"):
        return _render_quote(section)
    return ""


def _brand_wordmark(size: int = 17, color: str = BRAND) -> str:
    """A styled text wordmark, deliberately NOT an image. A remote logo is invisible in
    every inbox that blocks images by default -- which for a first email from an unknown
    sender is most of them -- so the one element that identifies who this is from would be
    the first thing to disappear. Text always renders."""
    return (f'<span style="font-family: {FONT}; font-size: {size}px; font-weight: 700; '
            f'letter-spacing: -0.2px; color: {color};">IV<span style="font-weight: 400;">infotech</span></span>')


def _header() -> str:
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="margin: 0 0 24px 0;">
  <tr><td style="padding: 0 0 18px 0; border-bottom: 1px solid {RULE};">{_brand_wordmark()}</td></tr>
</table>"""


def _headline(text: str) -> str:
    return (f'<div style="font-family: {FONT}; font-size: 22px; line-height: 1.32; '
            f'font-weight: 700; color: {INK}; margin: 0 0 14px 0;">{_e(text)}</div>')


def render_email_html(sections: list[dict], unsubscribe_url: str,
                      company_address: str | None = None, headline: str | None = None) -> str:
    """The full email document. `sections` is Step 11.1's ordered list; the compliance
    footer is appended here and is never the agent's responsibility -- the same rule
    email_service._build_footer() already enforces for the plain-text part.

    `headline` is normally the subject line, shown again as the page's own heading. That
    repetition is deliberate and is what almost every well-made transactional email does:
    the subject is gone from view the moment the message is opened, so without it the
    reader has no title to anchor on and the email opens mid-sentence.
    """
    body = _header()
    if headline:
        body += _headline(headline)
    body += "".join(_render_section(s) for s in sections or [])
    address = _e(company_address if company_address is not None else Config.COMPANY_PHYSICAL_ADDRESS)
    # The compliance block sits OUTSIDE the white card, the way a mail client's own
    # footer does, rather than inside it as another section of the message. It keeps the
    # legally-required text present and findable without letting it read as part of what
    # the sender wrote.
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
                     padding: 36px 34px 32px 34px; box-shadow: 0 1px 3px rgba(16,24,40,0.04);">{body}</td>
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
