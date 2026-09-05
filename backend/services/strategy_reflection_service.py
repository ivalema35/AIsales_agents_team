"""Phase 19 Step 19.1-19.4 -- the system's own real learning, applied campaign-based
(2026-09-02, operator's own correction: "har product ke liye nahi, har campaign based data
ko analysis karke strategy banaye" -- not a per-product rollup, a per-DOMAIN pool across
however many real campaigns targeted it). Nothing here is a rewrite of `campaign_service.py`'s
own metrics -- `compute_campaign_metrics()` (Step 17.3) is reused as-is; this module only
groups and reflects on it.

Step 19.6's explicit non-goal: nothing here ever writes to a prompt, a model, or any other
piece of code. A `strategy_insights` row is inert data until a future daily-strategist run
(Step 18.1, via `get_active_insight_for_domain`) reads it and a human approves the plan that
used it.
"""
from __future__ import annotations
import json
from datetime import datetime

from cognition.agent_events import log_agent_event
from cognition.llm_client import call_json, LLMError
from cognition.prompts import STRATEGY_REFLECTION_SYSTEM_PROMPT
from database.models import Campaign, Product, StrategyInsight
from services.campaign_service import compute_campaign_metrics
from services.system_settings import get_bool, get_int, STRATEGY_REFLECTION_ENABLED, STRATEGY_REFLECTION_MIN_SAMPLE_FLOOR
from config import Config


def aggregate_campaign_telemetry(db) -> list[dict]:
    """Every real campaign (any status) with at least one real send, as one telemetry row.
    No new tracking added anywhere -- `target_segment`/`strategy_angle` already live on the
    campaign, and `compute_campaign_metrics()` already derives real sent/opened/replied/hot
    live from outreach_logs/leads (Step 17.3). A campaign with zero sends yet has nothing
    to learn from and is excluded, not counted as a zero data point."""
    rows = []
    for c in db.query(Campaign).all():
        metrics = compute_campaign_metrics(db, c.id)
        if metrics["sent"] == 0:
            continue
        target = json.loads(c.target_segment or "{}")
        domain = target.get("industry")
        if not domain:
            continue  # no real vertical to group by -- nothing to pool this campaign into
        rows.append({
            "campaign_id": c.id, "campaign_name": c.name, "product_id": c.product_id,
            "domain": domain, "strategy_angle": c.strategy_angle, "metrics": metrics,
        })
    return rows


def group_by_domain(rows: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """(product_id, domain) -> its real campaign rows -- the pool Step 19.2's floor check
    and Step 19.3's reflection both operate on. Two campaigns for different products that
    happen to share a domain name (e.g. "dental clinics") are deliberately NOT pooled
    together -- what works for one product's pitch says nothing about another's."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        key = (row["product_id"], row["domain"])
        groups.setdefault(key, []).append(row)
    return groups


def _supersede_active(db, product_id: str, domain: str) -> None:
    db.query(StrategyInsight).filter(
        StrategyInsight.product_id == product_id,
        StrategyInsight.domain == domain,
        StrategyInsight.status == "ACTIVE",
    ).update({"status": "SUPERSEDED"})


def run_reflection_cycle(db) -> dict:
    """Step 19.1-19.3, one full pass: aggregate -> group by (product, domain) -> for every
    group that clears STRATEGY_REFLECTION_MIN_SAMPLE_FLOOR's real total sent count, ask for
    a real reflection. Gated by STRATEGY_REFLECTION_ENABLED (default off, same fail-safe
    posture as DAILY_AI_LOOP_ENABLED) -- returns a no-op summary if disabled, never raises,
    so a scheduler tick calling this unconditionally is always safe."""
    if not get_bool(db, STRATEGY_REFLECTION_ENABLED, default=False):
        return {"ran": False, "reason": "disabled"}

    floor = get_int(db, STRATEGY_REFLECTION_MIN_SAMPLE_FLOOR, default=40)
    rows = aggregate_campaign_telemetry(db)
    groups = group_by_domain(rows)

    checked, written, below_floor = 0, 0, 0
    for (product_id, domain), group_rows in groups.items():
        checked += 1
        total_sent = sum(r["metrics"]["sent"] for r in group_rows)
        if total_sent < floor:
            below_floor += 1
            continue

        product = db.get(Product, product_id)
        campaign_summaries = [
            {"name": r["campaign_name"], "strategy_angle": r["strategy_angle"], "metrics": r["metrics"]}
            for r in group_rows
        ]
        prompt = STRATEGY_REFLECTION_SYSTEM_PROMPT + f"""
PRODUCT_BRIEF: {json.dumps({"title": product.title, "description": product.description}, ensure_ascii=False)}
DOMAIN: {json.dumps(domain, ensure_ascii=False)}
CAMPAIGNS: {json.dumps(campaign_summaries, ensure_ascii=False)}
"""
        try:
            data = call_json(prompt, temperature=0.3)
        except LLMError as exc:
            log_agent_event(db, "STRATEGY_REFLECTION", None, "REFLECT", 0.0, "LOW", "EXECUTE",
                            payload={"product_id": product_id, "domain": domain, "error": str(exc)})
            continue

        if not data.get("has_insight"):
            continue
        winning_angle = str(data.get("winning_angle") or "").strip()
        rationale = str(data.get("rationale") or "").strip()
        if not winning_angle or not rationale:
            continue  # required fields missing -- never write a half-formed insight

        losing_angle = data.get("losing_angle")
        confidence = data.get("confidence")

        _supersede_active(db, product_id, domain)
        insight = StrategyInsight(
            product_id=product_id,
            domain=domain,
            winning_angle=winning_angle[:500],
            losing_angle=str(losing_angle).strip()[:500] if losing_angle else None,
            confidence=float(confidence) if isinstance(confidence, (int, float)) else None,
            rationale=rationale[:250],
            status="ACTIVE",
        )
        db.add(insight)
        db.commit()
        written += 1
        log_agent_event(db, "STRATEGY_REFLECTION", None, "INSIGHT_WRITTEN", 1.0, "LOW", "EXECUTE",
                        payload={"product_id": product_id, "domain": domain, "winning_angle": winning_angle})

    return {"ran": True, "domains_checked": checked, "insights_written": written, "below_floor": below_floor}


def get_active_insights_for_product(db, product_id: str) -> list[dict]:
    """Step 19.4 -- what Step 18.1's daily strategist reads, for EVERY domain this product
    has an ACTIVE insight for, not just one already-known domain. This is deliberate: a
    fresh campaign with no target_segment yet doesn't know its own domain until the
    strategist picks one -- these insights are part of what informs that pick (e.g. "dental
    clinics already has a strong, real insight, cake shops doesn't yet"), the same way
    SIBLING_CAMPAIGNS already informs it, not something looked up only after the fact."""
    rows = (
        db.query(StrategyInsight)
        .filter(StrategyInsight.product_id == product_id, StrategyInsight.status == "ACTIVE")
        .order_by(StrategyInsight.created_at.desc())
        .all()
    )
    return [
        {
            "domain": r.domain, "winning_angle": r.winning_angle, "losing_angle": r.losing_angle,
            "confidence": r.confidence, "rationale": r.rationale,
        }
        for r in rows
    ]


def list_active_insights(db, product_id: str | None = None, limit: int = 10) -> list[dict]:
    """Step 19.5 -- human-readable list of the newest ACTIVE insights for the Dashboard
    card (and optional product-scoped views). Read-only: this never writes. Product title
    is joined so the UI can say "for IV Classes" without a second round-trip. SUPERSEDED
    rows are excluded -- only the current winning rule per domain is shown to a human
    (the strategist still sees history via its own internal reads if needed)."""
    from database.models import Product

    query = (
        db.query(StrategyInsight, Product.title)
        .join(Product, Product.id == StrategyInsight.product_id)
        .filter(StrategyInsight.status == "ACTIVE")
    )
    if product_id:
        query = query.filter(StrategyInsight.product_id == product_id)
    rows = query.order_by(StrategyInsight.created_at.desc()).limit(max(1, min(limit, 50))).all()
    return [
        {
            "id": insight.id,
            "product_id": insight.product_id,
            "product_title": product_title,
            "domain": insight.domain,
            "winning_angle": insight.winning_angle,
            "losing_angle": insight.losing_angle,
            "confidence": insight.confidence,
            "rationale": insight.rationale,
            "created_at": str(insight.created_at),
        }
        for insight, product_title in rows
    ]
