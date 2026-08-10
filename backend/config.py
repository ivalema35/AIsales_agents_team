import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ENV = os.getenv("ENV", "development")
    DB_PATH = os.getenv("DB_PATH", "sales_system.db")
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
    WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
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
