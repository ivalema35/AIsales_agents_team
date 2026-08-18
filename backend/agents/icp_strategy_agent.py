from __future__ import annotations
from __future__ import annotations
"""ICP & Strategy Agent (MASTER §6). Designed in the original PRD but never wired into
the pipeline until tracker.md A.2: reads a product's own brief and decides who to target
and what to search for -- replacing the earlier assumption that a human types city +
keyword combos in by hand every day.

Follows the same pattern as scoring_agent.py: this module only calls the LLM and returns a
defensively-validated result. It does not touch the DB itself -- the caller (jobs/
discovery_scheduler.py) owns persisting it into product_strategies, same separation used
for lead_scores in _handle_score.
"""
import json

from cognition.agent_events import log_agent_event
from cognition.llm_client import call_json, LLMError
from cognition.prompts import ICP_STRATEGY_AGENT_SYSTEM_PROMPT


def generate_strategy(db, product_id: str, product_brief: dict):
    prompt = ICP_STRATEGY_AGENT_SYSTEM_PROMPT + f"""
PRODUCT: {json.dumps(product_brief, ensure_ascii=False)}
"""
    try:
        data = call_json(prompt, temperature=0.3)
    except LLMError as exc:
        log_agent_event(db, "ICP", None, "GENERATE_STRATEGY", 0.0, "LOW", "LLM_FAILED",
                        payload={"product_id": product_id, "error": str(exc)})
        return None

    icp = data.get("icp")
    if not isinstance(icp, dict):
        icp = {}
    icp = {
        "company_size": str(icp.get("company_size", ""))[:100],
        "roles": [str(r)[:60] for r in icp.get("roles", []) if isinstance(r, (str, int, float))][:10],
        "verticals": [str(v)[:60] for v in icp.get("verticals", []) if isinstance(v, (str, int, float))][:10],
    }

    search_queries = data.get("search_queries")
    if not isinstance(search_queries, list):
        search_queries = []
    search_queries = [str(q).strip()[:100] for q in search_queries if str(q).strip()][:15]

    target_complaints = data.get("target_complaints")
    if not isinstance(target_complaints, list):
        target_complaints = []
    target_complaints = [str(c).strip()[:100] for c in target_complaints if str(c).strip()][:15]

    result = {"icp": icp, "search_queries": search_queries, "target_complaints": target_complaints}

    # No confidence field in this prompt's output (MASTER §6) -- this plans a search
    # strategy, it never touches a lead directly, so there's no risky action to gate via
    # the Decision Engine here. Logged for audit only.
    log_agent_event(db, "ICP", None, "GENERATE_STRATEGY", None, "LOW", "EXECUTE",
                    payload={"product_id": product_id, "query_count": len(search_queries)})

    if not search_queries:
        return None  # nothing usable to act on -- caller should not persist an empty strategy

    return result
