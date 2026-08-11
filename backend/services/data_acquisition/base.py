from abc import ABC, abstractmethod


class LeadSourceProvider(ABC):
    """Contract every discovery provider must satisfy. discover() always returns a list
    of plain dicts in this shape (missing fields = None), regardless of which upstream
    API produced them -- callers never branch on provider identity."""

    @abstractmethod
    def discover(self, query: str, location: str | None = None) -> list[dict]:
        ...


def empty_lead(**overrides) -> dict:
    lead = {
        "company_name": None,
        "website_url": None,
        "primary_email": None,
        "primary_phone": None,
        "region_location": None,
        "source": None,
        # signals carried through discovery but not stored on `leads` -- rating and
        # rating_count belong in lead_review_insights (written by the review agent),
        # google_cid is the handle needed to fetch the actual review text
        "rating": None,
        "rating_count": None,
        "category": None,
        "google_cid": None,
    }
    lead.update(overrides)
    return lead
