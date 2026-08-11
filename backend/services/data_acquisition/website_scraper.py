"""Pull contact emails off a company's own website.

Why this exists: Hunter's domain-search can only ever return `@thatdomain` addresses.
A large share of Indian SMBs publish a gmail/yahoo address as their real contact -- those
are structurally invisible to Hunter, so relying on it alone leaves such leads with no
contact at all. The company's own site is both the most complete and the most trustworthy
source: it's where they themselves say "write to us here".

Free (no API cost), so it runs before Hunter, not after.
"""
import logging
import re
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
MAILTO_RE = re.compile(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.I)

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
