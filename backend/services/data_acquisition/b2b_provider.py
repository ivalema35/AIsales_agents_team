from __future__ import annotations
import requests

from config import Config

HUNTER_DOMAIN_SEARCH_URL = "https://api.hunter.io/v2/domain-search"


class HunterProvider:
    """Domain -> contact enrichment. Not a LeadSourceProvider: it doesn't discover new
    companies, it fills in emails/contacts for a company we already found."""

    def __init__(self, api_key=None, timeout=15):
        self.api_key = api_key or Config.HUNTER_API_KEY
        self.timeout = timeout

    def enrich_domain(self, domain: str) -> list[dict]:
        if not self.api_key:
            raise RuntimeError("HUNTER_API_KEY not configured")

        resp = requests.get(
            HUNTER_DOMAIN_SEARCH_URL,
            params={"domain": domain, "api_key": self.api_key},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})

        return [
            {
                "email": email.get("value"),
                "confidence": email.get("confidence"),
                "first_name": email.get("first_name"),
                "last_name": email.get("last_name"),
                "position": email.get("position"),
            }
            for email in data.get("emails", [])
        ]
