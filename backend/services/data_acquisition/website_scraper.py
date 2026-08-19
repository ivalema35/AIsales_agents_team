"""Pull contact emails off a company's own website.

Why this exists: Hunter's domain-search can only ever return `@thatdomain` addresses.
A large share of Indian SMBs publish a gmail/yahoo address as their real contact -- those
are structurally invisible to Hunter, so relying on it alone leaves such leads with no
contact at all. The company's own site is both the most complete and the most trustworthy
source: it's where they themselves say "write to us here".

Free (no API cost), so it runs before Hunter, not after.
"""
from __future__ import annotations
import logging
import re
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
MAILTO_RE = re.compile(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.I)

TEL_HREF_RE = re.compile(r'href=["\']tel:([^"\']+)["\']', re.I)
WA_HREF_RE = re.compile(
    r'href=["\'][^"\']*(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\+?\d[\d\-\s]{7,15})[^"\']*["\']',
    re.I,
)
# Plain-text fallback: an Indian mobile number quoted in body copy, not inside a link.
# Weakest signal of the three -- more prone to matching order IDs, GSTINs, etc.
#
# Each digit after the first may have an optional single space/dash before it -- plain
# Indian text overwhelmingly writes numbers "97244 09639" or "97244-09639" (5+5), not as
# one unbroken run. A naive \d{9} tail (no allowance for embedded separators) silently
# fails to match that format at all -- found live: a business's own Instagram bio wrote
# their number spaced, an unrelated post happened to write a WRONG number unspaced, and
# the unbroken-digits version won a vote tie it should never have been eligible to enter.
TEXT_MOBILE_RE = re.compile(r"(?<!\d)(?:\+?91[-\s]?)?[6-9](?:[-\s]?\d){9}(?!\d)")

# Real browser headers. Without an Accept header some servers return 406 outright
# (atlantacomputer.in did exactly that) -- this is politeness/compatibility, not evasion.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Anything matching the email shape that isn't a contact address.
_JUNK_SUBSTRINGS = (
    "@sentry", "@wixpress", "@2x.", "@3x.",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js", ".ico",
)
_PLACEHOLDER_DOMAINS = {
    "example.com", "example.org", "domain.com", "yourdomain.com", "email.com",
    "sentry.io", "wix.com", "godaddy.com", "sentry.wixpress.com",
}
_PLACEHOLDER_LOCALS = {
    "your", "youremail", "yourname", "name", "email", "someone", "user",
    "username", "abc", "xyz", "test", "sample", "example", "john.doe", "johndoe",
}
# Role accounts -- real, but nobody's personal inbox.
ROLE_PREFIXES = {
    "info", "admin", "contact", "support", "sales", "enquiry", "enquiries",
    "inquiry", "office", "help", "hello", "mail", "care", "service", "team",
    "noreply", "no-reply", "donotreply",
}
# Never worth contacting.
_NEVER_CONTACT = {"noreply", "no-reply", "donotreply", "do-not-reply", "postmaster", "abuse"}

# Free webmail providers. An SMB's real contact is very often one of these rather than
# an address on their own domain, so these must stay trusted -- but any OTHER corporate
# domain found on the page belongs to someone else (a vendor mentioned in a blog post,
# a partner listing, the web designer's credit) and must never become our contact.
WEBMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.in", "yahoo.in",
    "hotmail.com", "outlook.com", "live.com", "msn.com",
    "rediffmail.com", "rediff.com", "icloud.com", "protonmail.com", "proton.me",
    "zoho.com", "zohomail.com", "aol.com", "mail.com", "gmx.com", "ymail.com",
}


def belongs_to_company(email: str, domain: str | None) -> bool:
    """True if the address plausibly belongs to the company whose site we scraped.

    Accepts its own domain (and subdomains), and any free-webmail address. Rejects
    addresses on a different company's domain -- emailing those means contacting a
    completely unrelated business.
    """
    if not domain:
        return True
    email_domain = email.lower().partition("@")[2]
    if email_domain in WEBMAIL_DOMAINS:
        return True
    root = domain.lower().removeprefix("www.")
    return email_domain == root or email_domain.endswith(f".{root}") or root.endswith(f".{email_domain}")


def is_valid_contact_email(email: str) -> bool:
    email = email.lower().strip(".,;:)('\"")
    if any(j in email for j in _JUNK_SUBSTRINGS):
        return False
    if email.count("@") != 1:
        return False
    local, _, domain = email.partition("@")
    if not local or not domain or "." not in domain:
        return False
    if domain in _PLACEHOLDER_DOMAINS or local in _PLACEHOLDER_LOCALS:
        return False
    if local in _NEVER_CONTACT:
        return False
    # a bare version-looking local part ("v1.2") is almost always a false positive
    if re.fullmatch(r"[\d.]+", local):
        return False
    return True


def is_role_account(email: str) -> bool:
    local = email.lower().partition("@")[0]
    base = re.split(r"[._-]", local)[0]
    return local in ROLE_PREFIXES or base in ROLE_PREFIXES


def normalize_mobile(raw: str) -> str | None:
    """'+91 98765 43210' / '098765-43210' / '9876543210' -> '9876543210'.

    Returns None for anything that isn't a valid 10-digit Indian mobile number
    (starts 6-9) once the country code / leading 0 is stripped -- landlines (which
    carry an STD area code and don't fit this shape) are discarded on purpose, not
    just deprioritized: outreach here is WhatsApp-first, and WhatsApp requires a
    mobile number, so a landline is dead weight rather than a weaker lead.
    """
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 10 and digits[0] in "6789":
        return digits
    return None


def _extract_phones(html: str) -> list[dict]:
    """WhatsApp links first (a wa.me link is mobile by definition), then tel: links,
    then a plain-text regex as a last, weaker pass. Order = priority; dedup keeps the
    first (highest-priority) source for a number found multiple ways.
    """
    found = []
    seen = set()

    def add(raw, source):
        mobile = normalize_mobile(raw)
        if mobile and mobile not in seen:
            seen.add(mobile)
            found.append({"phone": mobile, "source": source})

    for m in WA_HREF_RE.finditer(html or ""):
        add(m.group(1), "whatsapp_link")
    for m in TEL_HREF_RE.finditer(html or ""):
        add(m.group(1), "tel_link")
    for m in TEXT_MOBILE_RE.finditer(html or ""):
        add(m.group(0), "text")

    return found


def _extract(html: str, domain: str | None = None) -> list[str]:
    """mailto: links first -- those are unambiguously contact addresses the site owner
    put there on purpose, unlike a stray address in body text.

    Pass `domain` to drop addresses belonging to other companies (vendors quoted in blog
    posts, partner listings, the web designer's credit line).
    """
    ordered = []
    for match in MAILTO_RE.findall(html or "") + EMAIL_RE.findall(html or ""):
        email = match.lower().strip(".,;:)('\"")
        if not is_valid_contact_email(email):
            continue
        if not belongs_to_company(email, domain):
            logger.debug("dropping %s -- belongs to a different domain than %s", email, domain)
            continue
        if email not in ordered:
            ordered.append(email)
    return ordered


# Same HTML scrape_emails()/scrape_phones() already fetch for this domain -- extracting
# social links off it costs nothing extra (no new request), unlike the search-based
# lookup this feeds into for businesses that have no website at all.
#
# Real bug, found live measuring the free-path hit rate on 37 real leads (54% -- wanted
# higher): several sites that genuinely link their own Instagram/Facebook were still
# coming back empty. Root cause -- modern sites increasingly publish their official
# profiles as Schema.org "sameAs" JSON-LD (`"sameAs":["https:\/\/www.facebook.com\/x",...]`)
# or framework SSR-hydration JSON (`"metadata":{"value":"https://instagram.com/x"}`), not
# a plain `<a href="...">` -- a regex anchored on `href=["\']` structurally can't see
# either. Not required anymore: any URL sitting inside a quoted string (JSON strings
# also use quotes) now matches, which covers both.
_SOCIAL_HREF_RES = {
    # Real bug, found live: excluding backslash from the capture class (matching this
    # project's usual "stop at a quote/whitespace" style) broke as soon as a JSON-
    # escaped URL had a SECOND escaped slash later in the path (e.g. a trailing
    # "...\/ekoching_india\/") -- the match ended right before that backslash instead of
    # continuing to the real closing quote, since backslash wasn't a permitted capture
    # character at all. Escaped slashes can appear anywhere in the path, not just right
    # after the domain, so backslash has to stay INSIDE the capture class; only the
    # actual string terminators (quote/whitespace) should stop it.
    "instagram_url": re.compile(r'["\'](https?:\\?/\\?/(?:www\.)?instagram\.com\\?/[^"\'\s]+)["\']', re.I),
    "facebook_url": re.compile(r'["\'](https?:\\?/\\?/(?:www\.|m\.)?facebook\.com\\?/[^"\'\s]+)["\']', re.I),
    "linkedin_url": re.compile(r'["\'](https?:\\?/\\?/(?:www\.)?linkedin\.com\\?/[^"\'\s]+)["\']', re.I),
}

# A link matching the platform's domain isn't necessarily the business's own PROFILE --
# share widgets, login walls, and policy pages match the domain regex too. LinkedIn is
# stricter still: it requires an actual company/personal/school profile path, since a
# generic /pulse/... or /jobs/... link is just a blog citation, not the business's page.
_SOCIAL_JUNK_PATH_PREFIXES = {
    "instagram_url": ("p/", "reel", "stories/", "explore/", "accounts/", "about/",
                       "legal/", "developer/", "directory/", "embed"),
    "facebook_url": ("sharer", "share.php", "plugins/", "policies", "help", "legal",
                      "privacy", "watch/", "groups/", "marketplace/", "business/",
                      "policy.php", "dialog/", "login", "l.php"),
}
# Real bug, found live at scale (not in the original small samples): facebook.com/tr is
# Meta's own conversion-tracking pixel endpoint (`facebook.com/tr?id=...&ev=PageView`,
# embedded by nearly every site running Meta Ads) -- the query string means the path is
# exactly "tr" with NO trailing slash, so the "tr/" prefix above never matched it (a bare
# "tr".startswith("tr/") is False). Checked separately, as an EXACT segment match rather
# than folding a bare "tr" into the prefix tuple -- a real business handle that merely
# STARTS WITH "tr" (e.g. "trueblue...") would wrongly match a "tr" prefix check.
_FACEBOOK_JUNK_EXACT_FIRST_SEGMENT = {"tr"}
_LINKEDIN_PROFILE_PREFIXES = ("company/", "in/", "school/")


def find_social_links(html: str) -> dict:
    """Instagram/Facebook/LinkedIn profile URLs off a company's own page HTML,
    best-effort, one per platform. Not a full crawl -- these links live in a site's own
    header/footer, which is on every page the rest of this module already fetches.
    """
    found = {}
    for field, pattern in _SOCIAL_HREF_RES.items():
        for match in pattern.finditer(html or ""):
            # JSON string values escape forward slashes ("https:\/\/..."); the pattern
            # above tolerates that so it can match inside JSON-LD/SSR-hydration blobs at
            # all, but urlparse() needs a normal URL -- unescape before parsing.
            raw_url = match.group(1).replace("\\/", "/")
            parsed = urlparse(raw_url)
            path = parsed.path.strip("/")
            if not path:
                continue
            if field == "linkedin_url":
                if not (path + "/").lower().startswith(_LINKEDIN_PROFILE_PREFIXES):
                    continue
                # Real bug, found live: a business's own site had
                # linkedin.com/company/<id>/admin/updates/ embedded in its footer --
                # their own developer had pasted the LinkedIn ADMIN-panel link (visible
                # only when logged in as that page's manager) instead of the public
                # page URL. Structurally matches the company/ prefix check above, but
                # clicking it sends a rep to a LinkedIn login wall, not the business's
                # page -- worthless for outreach. Any "admin" segment anywhere in a
                # linkedin.com path is never part of a real public profile.
                if "admin" in path.lower().split("/"):
                    continue
            elif any(path.lower().startswith(j) for j in _SOCIAL_JUNK_PATH_PREFIXES[field]):
                continue
            elif field == "facebook_url" and path.lower().split("/")[0] in _FACEBOOK_JUNK_EXACT_FIRST_SEGMENT:
                continue
            # Real bug, found live against real business sites: sharer-generated links
            # carry tracking query params (?igsh=..., ?mibextid=..., a nested
            # share_url=... with its own %-encoded querystring) -- keeping those made
            # the stored "clean" profile URL both ugly and, once a trailing slash got
            # appended straight onto the end of a query value, genuinely malformed.
            # Drop query/fragment entirely; the path alone is the actual identifier.
            clean_url = f"{parsed.scheme}://{parsed.netloc}/{path}/"
            found[field] = clean_url
            break  # first genuine match wins -- same "one hit is enough" call as scrape_emails
    return found


def _candidate_urls(domain: str) -> list[str]:
    """Both www and bare (calibersnova.com only answers on www, others only on bare),
    plus the pages SMBs actually put their address on."""
    urls = []
    for host in (f"https://{domain}", f"https://www.{domain}", f"http://{domain}"):
        urls.extend([host, f"{host}/contact", f"{host}/contact-us"])
    return urls


def _fetch(url: str, timeout: int):
    try:
        resp = requests.get(url, timeout=timeout, headers=HEADERS, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception as exc:  # noqa: BLE001 - an unreachable site is normal, not exceptional
        logger.debug("fetch failed %s: %s", url, type(exc).__name__)
        return None


def scrape_emails(domain: str, timeout=12, max_pages=4) -> list[str]:
    """Return contact emails found on the company's own site, best-effort.

    Stops at the first page that yields anything -- one hit is enough and repeatedly
    hitting a small business's site for marginal extra addresses isn't worth it.
    """
    if not domain:
        return []

    found = []
    pages_tried = 0
    for url in _candidate_urls(domain):
        if pages_tried >= max_pages:
            break
        html = _fetch(url, timeout)
        if html is None:
            continue
        pages_tried += 1
        for email in _extract(html, domain=domain):
            if email not in found:
                found.append(email)
        if found:
            logger.info("website scrape %s -> %s (from %s)", domain, found, url)
            return found

    logger.info("website scrape %s -> nothing found (%d pages reachable)", domain, pages_tried)
    return found


def scrape_phones(domain: str, timeout=12, max_pages=4) -> list[dict]:
    """Return WhatsApp-capable mobile numbers found on the company's own site,
    best-effort. Mirrors scrape_emails()'s page-walking; kept as a separate pass
    (rather than merged into one fetch) so the already-tested email path stays
    untouched.
    """
    if not domain:
        return []

    found = []
    seen = set()
    pages_tried = 0
    for url in _candidate_urls(domain):
        if pages_tried >= max_pages:
            break
        html = _fetch(url, timeout)
        if html is None:
            continue
        pages_tried += 1
        for entry in _extract_phones(html):
            if entry["phone"] not in seen:
                seen.add(entry["phone"])
                found.append(entry)
        if found:
            logger.info("phone scrape %s -> %s (from %s)", domain, found, url)
            return found

    logger.info("phone scrape %s -> nothing found (%d pages reachable)", domain, pages_tried)
    return found


def scrape_social_links(domain: str, timeout=12, max_pages=4) -> dict:
    """Instagram/Facebook/LinkedIn profile URLs found on the company's own site,
    best-effort. A separate fetch pass from scrape_emails()/scrape_phones() (not a
    shared one) -- deliberately, so this new lookup can't risk regressing either of
    those two already-verified paths real outreach depends on.
    """
    if not domain:
        return {}

    found = {}
    pages_tried = 0
    for url in _candidate_urls(domain):
        if pages_tried >= max_pages or len(found) == 3:
            break
        html = _fetch(url, timeout)
        if html is None:
            continue
        pages_tried += 1
        for field, value in find_social_links(html).items():
            found.setdefault(field, value)

    if found:
        logger.info("website social scrape %s -> %s", domain, found)
    else:
        logger.info("website social scrape %s -> nothing found (%d pages reachable)", domain, pages_tried)
    return found


async def scrape_emails_rendered(domain: str) -> list[str]:
    """Playwright fallback for JS-rendered sites where plain HTML has no addresses.
    Only worth calling when scrape_emails() came back empty -- it's ~100x the cost.
    Note: it cannot help when the site refuses our IP outright (wiceindia.com does).
    """
    from services.data_acquisition.playwright_fallback import fetch_rendered

    for url in (f"https://{domain}", f"https://www.{domain}"):
        try:
            html = await fetch_rendered(url, timeout=20000)
        except Exception as exc:  # noqa: BLE001
            logger.debug("rendered fetch failed %s: %s", url, type(exc).__name__)
            continue
        emails = _extract(html, domain=domain)
        if emails:
            logger.info("rendered scrape %s -> %s", domain, emails)
            return emails
    return []


def rank_candidates(website_emails, hunter_contacts, domain=None):
    """Order contacts best-first for cold outreach.

    Ranking rationale (deliverability is a hard PRD constraint -- bounce rate must stay
    under 2%, so a *reachable* address beats a *senior-sounding* one):
      1. named person on the company's own site  -- real human, self-published, current
      2. role account on their own site          -- monitored inbox, self-published
      3. Hunter contact with a real name/position -- real human, but third-party sourced
      4. Hunter generic/role account             -- weakest signal
    """
    site_set = set(website_emails)
    candidates = []

    hunter_by_email = {}
    for c in hunter_contacts or []:
        if c.get("email"):
            hunter_by_email[c["email"].lower()] = c

    for email in website_emails:
        hunter_match = hunter_by_email.get(email, {})
        has_name = bool(hunter_match.get("first_name") or hunter_match.get("last_name"))
        role = is_role_account(email)
        candidates.append({
            "email": email,
            "source": "WEBSITE",
            "tier": 2 if role and not has_name else 1,
            "confidence": hunter_match.get("confidence"),
            "first_name": hunter_match.get("first_name"),
            "last_name": hunter_match.get("last_name"),
            "position": hunter_match.get("position"),
        })

    for c in hunter_contacts or []:
        email = (c.get("email") or "").lower()
        if not email or email in site_set:
            continue
        if not is_valid_contact_email(email):
            continue
        if not belongs_to_company(email, domain):
            continue
        has_name = bool(c.get("first_name") or c.get("last_name"))
        candidates.append({
            "email": email,
            "source": "HUNTER",
            "tier": 3 if has_name else 4,
            "confidence": c.get("confidence"),
            "first_name": c.get("first_name"),
            "last_name": c.get("last_name"),
            "position": c.get("position"),
        })

    # within a tier, higher Hunter confidence first; unknown confidence sorts last
    candidates.sort(key=lambda c: (c["tier"], -(c["confidence"] or 0)))
    return candidates


def domain_from_url(website_url):
    if not website_url:
        return None
    netloc = urlparse(website_url).netloc or urlparse(f"//{website_url}").netloc
    if not netloc:
        return None
    return netloc.split(":")[0].removeprefix("www.") or None
