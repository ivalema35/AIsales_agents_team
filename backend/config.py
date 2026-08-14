import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ENV = os.getenv("ENV", "development")
    DB_PATH = os.getenv("DB_PATH", "sales_system.db")
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # LLM provider — swappable, one line to change (tracker.md §A.1)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-flash-latest")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    # Sandbox default until a domain is verified in Resend -- can only send TO the
    # email address the Resend account itself was signed up with (tracker.md §Phase 3).
    RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    RESEND_FROM_NAME = os.getenv("RESEND_FROM_NAME", "")  # e.g. "Ronak from IVinfotech"
    # Must be publicly reachable for a real recipient's unsubscribe click to work --
    # localhost is fine for our own test sends, not for anyone else's inbox.
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:5000")
    # HUMAN_LOCKED: required on every email footer (MASTER §9.1 rule 4 / QC checklist).
    # Placeholder -- set the real registered business address before any real lead is
    # ever emailed; QC will still approve drafts with this placeholder in place today,
    # but the placeholder itself would not be compliant in a real send.
    COMPANY_PHYSICAL_ADDRESS = os.getenv(
        "COMPANY_PHYSICAL_ADDRESS", "IVinfotech -- [SET COMPANY_PHYSICAL_ADDRESS IN .env]")
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
    WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
    WHATSAPP_WABA_ID = os.getenv("WHATSAPP_WABA_ID")
    # This BSP (waba.fortius.in.net) mirrors Meta's real Cloud API path structure
    # exactly (/{version}/{phoneNumberId}/messages) -- confirmed live 2026-08-13 --
    # just fronted by their own API server instead of graph.facebook.com.
    WHATSAPP_API_BASE_URL = os.getenv("WHATSAPP_API_BASE_URL", "https://waba.fortius.in.net")
    WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v21.0")
    # Set when registering the inbound webhook URL in the Meta/BSP dashboard (Step 4.1) --
    # any string you choose, just has to match what you enter there.
    WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

    # Autonomous discovery scheduler (tracker.md A.2 — replaces n8n for Step 3.5)
    ICP_STRATEGY_REFRESH_DAYS = int(os.getenv("ICP_STRATEGY_REFRESH_DAYS", "7"))
    DISCOVERY_COOLDOWN_HOURS = int(os.getenv("DISCOVERY_COOLDOWN_HOURS", "24"))
    MAX_DISCOVER_PER_TICK = int(os.getenv("MAX_DISCOVER_PER_TICK", "3"))
    SCHEDULER_POLL_INTERVAL_SECONDS = int(os.getenv("SCHEDULER_POLL_INTERVAL_SECONDS", "300"))
    OUTREACH_TICK_INTERVAL_SECONDS = int(os.getenv("OUTREACH_TICK_INTERVAL_SECONDS", "3600"))
    # Pacing caps -- global for now (per-product override is a possible future extension,
    # not built since it wasn't needed to close the DoD Gate P3 "pacing caps" item).
    OUTREACH_DAILY_CAP_EMAIL = int(os.getenv("OUTREACH_DAILY_CAP_EMAIL", "40"))
    OUTREACH_DAILY_CAP_WHATSAPP = int(os.getenv("OUTREACH_DAILY_CAP_WHATSAPP", "40"))
    OUTREACH_STAGGER_SECONDS = int(os.getenv("OUTREACH_STAGGER_SECONDS", "90"))
    # Safety kill-switch (added 2026-08-13 during a live process audit): discovery now
    # runs autonomously against real businesses, but the project's own non-negotiable
    # rule is that no real third party gets contacted until the user explicitly says so.
    # Defaults CLOSED -- _run_outreach_tick() in jobs/discovery_scheduler.py must check
    # this before claiming/sending anything real. Deliberately does not gate the
    # already-existing manual test paths (claim_lead_for_outreach called directly, e.g.
    # a self-test lead) -- only the autonomous scheduler's own tick.
    AUTONOMOUS_OUTREACH_ENABLED = os.getenv("AUTONOMOUS_OUTREACH_ENABLED", "false").lower() == "true"

    # Inbound email (Step 4.1) -- IMAP polling of the reply-monitored mailbox, no public
    # webhook URL needed (unlike WhatsApp's inbound webhook).
    INBOUND_EMAIL_HOST = os.getenv("INBOUND_EMAIL_HOST")
    INBOUND_EMAIL_PORT = int(os.getenv("INBOUND_EMAIL_PORT", "993"))
    INBOUND_EMAIL_USER = os.getenv("INBOUND_EMAIL_USER")
    INBOUND_EMAIL_PASSWORD = os.getenv("INBOUND_EMAIL_PASSWORD")
    INBOUND_POLL_INTERVAL_SECONDS = int(os.getenv("INBOUND_POLL_INTERVAL_SECONDS", "120"))

    # Data acquisition (lead discovery / enrichment) — free-tier providers in use
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
    # Not in use yet (require billing even on "free" tier) — left here for later
    SERPAPI_KEY = os.getenv("SERPAPI_KEY")
    PLACES_API_KEY = os.getenv("PLACES_API_KEY")


# Decision Engine thresholds — tune here, not in code paths (MASTER_DEVELOPMENT_PRD.md §4.2)
DECISION_THRESHOLDS = {
    "SCORING":           {"min": 0.70, "route_below": "HUMAN"},
    "STANDARD_OUTREACH": {"min": 0.85, "review": "QC"},
    "INBOUND_REPLY":     {"min": 0.85, "route_below": "HUMAN"},
    "MEETING_BOOKING":   {"min": 0.90, "alert_human": True},
    "CUSTOM_PRICING":    {"min": 0.95, "force": "HUMAN"},   # always human
    "OPT_OUT":           {"force": "IMMEDIATE"},            # 100% rule
}
