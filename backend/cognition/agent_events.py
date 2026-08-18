from __future__ import annotations
"""Audit log helper -- every autonomous agent decision writes one row here (MASTER §4.2).
This table is simultaneously the audit trail, the self-evaluation record, and the future
KPI source, so every LLM-backed agent call routes through this, not just the ones that
end up executing.
"""
import json
import uuid

from database.models import AgentEvent


def log_agent_event(db, agent, lead_id, action_type, confidence, risk_level, routed_to,
                    payload=None, outcome=None):
    event = AgentEvent(
        id=str(uuid.uuid4()),
        agent=agent,
        lead_id=lead_id,
        action_type=action_type,
        confidence=confidence,
        risk_level=risk_level,
        routed_to=routed_to,
        payload=json.dumps(payload or {}),
        outcome=outcome,
    )
    db.add(event)
    db.commit()
    return event.id
