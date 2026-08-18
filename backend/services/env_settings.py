"""Dashboard-visible/editable view over the real `.env` file, for every Config value that
isn't already dashboard-hot via system_settings.py (that module's 9 keys stay there --
this is deliberately everything ELSE).

Security boundary (explicit, at the user's request): a secret's actual value is NEVER
sent back to the browser once set, only a masked hint (last 4 chars) + "configured" status
-- this endpoint is write-only for secrets. Non-secret operational values (LLM model name,
sender display name, poll intervals, etc.) are fully read/write, since there's nothing to
protect there.

Important, deliberately surfaced rather than hidden: unlike system_settings.py, `.env`
values are only read by Config at process start (`os.getenv()`, once, on import) -- writing
a new value here updates the FILE, but every already-running process keeps its OLD
in-memory value until it's restarted. The API response says so explicitly per field so the
dashboard can warn the user, instead of silently implying an instant change that hasn't
actually happened (see tracker.md's own repeated "long-running process didn't pick up the
code/config change" lesson this session).
"""
import os
import re

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

# (key, label, hint, category, is_secret, type)
REGISTRY = [
    # --- LLM provider ---
    ("LLM_PROVIDER", "LLM provider", "Which model provider to call first: 'gemini' or 'openai'. Auto-falls-back to the other if the primary's quota is exhausted.", "LLM", False, "str"),
    ("LLM_MODEL", "LLM model", "Model name for the primary provider, e.g. 'gemini-flash-latest'.", "LLM", False, "str"),
    ("GEMINI_API_KEY", "Gemini API key", "From Google AI Studio. Used for every AI agent call unless the provider above is 'openai'.", "LLM", True, "str"),
    ("OPENAI_API_KEY", "OpenAI API key", "Used as the automatic fallback when the primary provider's quota runs out.", "LLM", True, "str"),

    # --- Email / Resend ---
    ("RESEND_API_KEY", "Resend API key", "Used for every real outbound email send (outreach, replies, EOD reports).", "Email", True, "str"),
    ("RESEND_FROM_EMAIL", "Sender email address", "The 'from' address on every outbound email -- must be a verified domain in Resend.", "Email", False, "str"),
    ("RESEND_FROM_NAME", "Sender display name", "e.g. 'Ronak from IVinfotech' -- shown as the sender name in the recipient's inbox.", "Email", False, "str"),
    ("COMPANY_PHYSICAL_ADDRESS", "Company physical address", "Required on every outbound email footer for compliance (CAN-SPAM/similar rules) -- QC checks for this.", "Email", False, "str"),
    ("PUBLIC_BASE_URL", "Public base URL", "Must be a real, internet-reachable URL for the unsubscribe link in outbound emails to work for a real recipient.", "Email", False, "str"),

    # --- WhatsApp ---
    ("WHATSAPP_TOKEN", "WhatsApp API token", "Bearer token for the WhatsApp Business Cloud API (or BSP) -- used for every WhatsApp send.", "WhatsApp", True, "str"),
    ("WHATSAPP_PHONE_ID", "WhatsApp phone number ID", "The Meta/BSP-assigned ID for the sending WhatsApp Business number.", "WhatsApp", False, "str"),
    ("WHATSAPP_WABA_ID", "WhatsApp Business Account ID", "The WABA ID this phone number belongs to.", "WhatsApp", False, "str"),
    ("WHATSAPP_API_BASE_URL", "WhatsApp API base URL", "Meta's own API (graph.facebook.com) or a BSP's mirror of it.", "WhatsApp", False, "str"),
    ("WHATSAPP_API_VERSION", "WhatsApp API version", "e.g. 'v21.0' -- the Graph API version path segment.", "WhatsApp", False, "str"),
    ("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "Webhook verify token", "Any string you choose -- must match exactly what's entered in the Meta/BSP dashboard when registering the inbound webhook.", "WhatsApp", True, "str"),

    # --- Discovery scheduler ---
    ("ICP_STRATEGY_REFRESH_DAYS", "ICP strategy refresh (days)", "How often the AI re-generates a product's target-audience/search-query strategy.", "Discovery", False, "int"),
    ("MAX_DISCOVER_PER_TICK", "Max discoveries per tick", "How many new (query, region) searches can fire in a single scheduler tick, across all products.", "Discovery", False, "int"),
    ("SCHEDULER_POLL_INTERVAL_SECONDS", "Scheduler poll interval (seconds)", "How often the discovery scheduler process wakes up to check for work.", "Discovery", False, "int"),
    ("OUTREACH_TICK_INTERVAL_SECONDS", "Outreach tick interval (seconds)", "How often the autonomous outreach-claiming tick runs (separate from the discovery poll).", "Discovery", False, "int"),
    ("OUTREACH_STAGGER_SECONDS", "Outreach stagger (seconds)", "Gap between each claimed lead's send time within a batch, so a day's sends trickle out instead of bursting.", "Discovery", False, "int"),

    # --- Inbound email ---
    ("INBOUND_EMAIL_HOST", "Inbound email IMAP host", "e.g. 'imap.hostinger.com' -- the mailbox the reply-poller connects to.", "Inbound Email", False, "str"),
    ("INBOUND_EMAIL_PORT", "Inbound email IMAP port", "Usually 993 (IMAP over SSL).", "Inbound Email", False, "int"),
    ("INBOUND_EMAIL_USER", "Inbound email address", "The mailbox address itself -- also usually the outbound sender address.", "Inbound Email", False, "str"),
    ("INBOUND_EMAIL_PASSWORD", "Inbound email password", "Mailbox password (or app-specific password) for IMAP login.", "Inbound Email", True, "str"),
    ("INBOUND_POLL_INTERVAL_SECONDS", "Inbound poll interval (seconds)", "How often the mailbox is checked for new replies.", "Inbound Email", False, "int"),

    # --- Data acquisition ---
    ("SERPER_API_KEY", "Serper API key", "Used for Google Search/Places-style lead discovery queries.", "Data Acquisition", True, "str"),
    ("HUNTER_API_KEY", "Hunter.io API key", "Used to look up @company-domain email addresses during enrichment.", "Data Acquisition", True, "str"),
]

_BY_KEY = {row[0]: row for row in REGISTRY}


def _read_raw_env() -> dict:
    """Parses the real .env file into {key: value}. Doesn't use python-dotenv's own
    loader here -- we want the file's CURRENT on-disk values specifically, not whatever
    os.environ already has cached from process start (those can differ once a value has
    been edited here but the process hasn't restarted yet)."""
    values = {}
    if not os.path.exists(ENV_PATH):
        return values
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "•" * len(value)
    return "•" * 6 + value[-4:]


def list_settings() -> list[dict]:
    current = _read_raw_env()
    result = []
    for key, label, hint, category, is_secret, value_type in REGISTRY:
        raw = current.get(key, "")
        result.append({
            "key": key,
            "label": label,
            "hint": hint,
            "category": category,
            "is_secret": is_secret,
            "type": value_type,
            "configured": bool(raw),
            "value": None if is_secret else raw,
            "masked": _mask(raw) if is_secret else None,
        })
    return result


def update_settings(updates: dict) -> list[str]:
    """Writes each key=value into the real .env file, preserving every other line
    untouched. Returns the list of keys actually written. Raises ValueError for any key
    not in the explicit REGISTRY -- this is a whitelist, never an arbitrary env-var
    write, regardless of what a request body claims."""
    unknown = set(updates) - set(_BY_KEY)
    if unknown:
        raise ValueError(f"unknown/non-editable setting(s): {sorted(unknown)}")

    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

    remaining = dict(updates)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in remaining:
            lines[i] = f"{key}={remaining.pop(key)}\n"

    for key, value in remaining.items():
        lines.append(f"{key}={value}\n")

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return list(updates.keys())
