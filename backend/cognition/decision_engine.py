"""The single gate every autonomous action passes through (MASTER §4.2). Thresholds live
in config.py's DECISION_THRESHOLDS, not scattered through agent code, so tuning a cutoff
is a one-line config change.
"""


def route_action(category: str, confidence: float, is_high_risk: bool = False) -> str:
    """Returns EXECUTE | QC_REVIEW | HUMAN_ESCALATION | IMMEDIATE_EXECUTE.

    OPT_OUT bypasses everything (100% rule -- suppress before any other processing).
    CUSTOM_PRICING and anything explicitly flagged high-risk always goes to a human,
    regardless of how confident the agent is. Below that, confidence alone decides:
    <0.70 -> a human looks at it, 0.70-0.85 -> QC reviews it, >=0.85 -> proceeds.
    """
    if category == "OPT_OUT":
        return "IMMEDIATE_EXECUTE"
    if category == "CUSTOM_PRICING" or is_high_risk:
        return "HUMAN_ESCALATION"
    if confidence < 0.70:
        return "HUMAN_ESCALATION"
    if category in ("STANDARD_OUTREACH",) or confidence < 0.85:
        return "QC_REVIEW"
    return "EXECUTE"
