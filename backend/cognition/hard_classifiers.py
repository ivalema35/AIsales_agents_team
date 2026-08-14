"""Hard pre-classifiers (MASTER Phase 4 / Step 4.2) -- deterministic, rule-based checks
that run BEFORE any LLM call on an inbound reply. No AI involved on purpose: the 100%
rule for OPT_OUT (see tracker.md's non-negotiable rules) means opt-out detection must
never depend on a model being available, fast, or right -- a plain keyword match is more
reliable for this one job than an LLM call would be. Auto-reply detection exists so a
vacation responder can never get mistaken for a genuine "interested" signal downstream.

Pure functions, no DB dependency -- same style as cognition/decision_engine.py.
"""
import re

# Deliberately includes "not interested" per MASTER's own Step 4.2 spec ("STOP/
# unsubscribe/not interested -> suppress immediately"), not just literal STOP -- a lead
# who says they're not interested gets treated as an opt-out, not left for the AI to
# maybe-interpret. Word-boundary matched, case-insensitive, so "unsubscribe" doesn't
# also match "subscribed" etc.
_OPTOUT_PATTERNS = [
    r"\bstop\b",
    r"\bunsubscribe\b",
    r"\bnot interested\b",
    r"\bno longer interested\b",
    r"\bremove me\b",
    r"\btake me off\b",
    r"\bdo not contact\b",
    r"\bdon'?t contact me\b",
    r"\bopt[\s-]?out\b",
    r"\bno thanks?\b",
    r"\bplease stop\b",
]
_OPTOUT_RE = re.compile("|".join(_OPTOUT_PATTERNS), re.IGNORECASE)

# Body-text signals -- the only option for WhatsApp (no headers); a fallback for email
# when the more reliable header check below doesn't fire (not every autoresponder sets
# the standard headers correctly).
_AUTOREPLY_PATTERNS = [
    r"\bout of (the )?office\b",
    r"\bauto(-|matic)?[\s-]?reply\b",
    r"\bautomated response\b",
    r"\bautomatic reply\b",
    r"\bcurrently (away|unavailable|on leave)\b",
    r"\bi'?m (currently )?on (vacation|leave|holiday)\b",
    r"\bvacation responder\b",
    r"\bwill be back\b",
    r"\breturn(ing)? to (the )?office\b",
]
_AUTOREPLY_RE = re.compile("|".join(_AUTOREPLY_PATTERNS), re.IGNORECASE)

# RFC 3834 / common mail-client headers that mark a message as an automatic response --
# far more reliable than body text when available (email only; WhatsApp payloads never
# have these). A header hit alone is enough, no body-text corroboration needed.
_AUTOREPLY_HEADER_KEYS = ("Auto-Submitted", "X-Autoreply", "X-Autorespond", "X-Auto-Response-Suppress")

# A plain-text reply quotes the original message below it by convention (Gmail/Apple
# Mail/Outlook all do this by default) -- and our own outreach emails always include an
# "Unsubscribe" footer, so a genuinely positive reply that just keeps the quote intact
# would otherwise contain the literal word "unsubscribe" and get misread as the SENDER's
# own opt-out below. Cut the body off at the first sign of quoted content before any
# keyword match runs.
_QUOTE_START_RE = re.compile(
    r"\r?\n\s*>|"                             # a quoted line (starts with '>')
    r"\r?\n\s*On .{0,150}?wrote:\s*\r?\n|"     # Gmail/Apple-style "On ... wrote:"
    r"\r?\n-{2,}\s*Original Message\s*-{2,}|"  # Outlook "-----Original Message-----"
    r"\r?\n_{5,}",                             # Outlook separator line
    re.IGNORECASE,
)


def _strip_quoted_reply(text: str) -> str:
    if not text:
        return text
    match = _QUOTE_START_RE.search(text)
    return text[:match.start()] if match else text


def is_optout(text: str) -> bool:
    stripped = _strip_quoted_reply(text)
    return bool(stripped) and bool(_OPTOUT_RE.search(stripped))


def is_autoreply(text: str, email_headers: dict | None = None) -> bool:
    if email_headers:
        auto_submitted = str(email_headers.get("Auto-Submitted", "")).lower()
        if auto_submitted and not auto_submitted.startswith("no"):
            return True
        if any(email_headers.get(k) for k in _AUTOREPLY_HEADER_KEYS if k != "Auto-Submitted"):
            return True
    stripped = _strip_quoted_reply(text)
    return bool(stripped) and bool(_AUTOREPLY_RE.search(stripped))


# Step 4.3's is_high_risk gate for route_action("INBOUND_REPLY", ...) -- pricing/legal/
# hostile replies always go to a human regardless of the AI classifier's own confidence,
# matching the project's non-negotiable "custom pricing/negotiation always human" rule.
# Deliberately deterministic, not an AI judgment call, for the same 100%-rule reasoning
# as is_optout: this gate must never depend on the classifier being right.
_HIGH_RISK_PATTERNS = [
    r"\bprice\b", r"\bpricing\b", r"\bcost\b", r"\bquote\b", r"\bquotation\b",
    r"\bdiscount\b", r"\bhow much\b", r"\bbudget\b",
    r"\blegal\b", r"\blawyer\b", r"\battorney\b", r"\bsue\b", r"\blawsuit\b",
    r"\bcomplaint\b", r"\bconsumer forum\b", r"\bfraud\b", r"\bscam\b",
    r"\bstupid\b", r"\bidiot\b", r"\bharass\b", r"\bthreat\b",
]
_HIGH_RISK_RE = re.compile("|".join(_HIGH_RISK_PATTERNS), re.IGNORECASE)


def looks_pricing_or_legal(text: str) -> bool:
    stripped = _strip_quoted_reply(text)
    return bool(stripped) and bool(_HIGH_RISK_RE.search(stripped))
