"""Phase 11 Step 11.5 (tracker.md A.10) -- resolve the OTHER products an admin chose to
cross-sell alongside the one being pitched.

The admin picks the list explicitly; the agent picks which ONE of them fits a given lead.
That split is the point: the system never has to guess which of our services are worth
offering together, and the agent can never name a service that isn't really ours.
"""
from __future__ import annotations
import json
import logging

from database.models import Product

logger = logging.getLogger(__name__)


def get_cross_sell_products(db, product_id: str) -> list[dict]:
    """Real briefs of the products this product cross-sells, or [] when none is
    configured. Silently skips an id that no longer resolves to a real product -- one
    deleted after being selected must simply stop being offered, not break every send for
    the product that referenced it.

    Deliberately does NOT check `is_active`: that flag gates whether the discovery
    scheduler is actively hunting new leads for a product (jobs/discovery_scheduler.py),
    not whether we still sell it -- a product with discovery paused is still a real thing
    to mention. Filtering on it here would have silently disabled cross-sell for every
    product whenever discovery happened to be off, which is exactly the kind of gap this
    codebase treats as a real bug, not a corner case (found before shipping: every local
    product currently has discovery off).
    """
    product = db.get(Product, product_id)
    if not product:
        return []
    try:
        ids = json.loads(product.cross_sell_product_ids or "[]")
    except (TypeError, ValueError):
        logger.warning("product %s has unparseable cross_sell_product_ids", product_id)
        return []
    if not isinstance(ids, list):
        return []

    briefs = []
    for other_id in ids:
        if other_id == product_id:
            continue          # a product never cross-sells itself
        other = db.get(Product, other_id)
        if not other:
            continue          # deleted since being selected -- quietly stop offering it
        briefs.append({
            "title": other.title,
            "description": other.description,
            "value_proposition": other.value_proposition,
        })
    return briefs
