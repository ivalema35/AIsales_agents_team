import uuid

from sqlalchemy import Column, String, Text, Integer, REAL, DATE, TIMESTAMP, ForeignKey, UniqueConstraint, func

from database.db_config import Base


def _uuid():
    return str(uuid.uuid4())


# 1. PRODUCTS
class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, default=_uuid)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    target_keywords = Column(Text, default="[]")
    value_proposition = Column(Text)
    pain_point_mappings = Column(Text, default="{}")
    priority = Column(Integer, default=1)
    is_active = Column(Integer, default=1)
    target_regions = Column(Text, default="[]")  # JSON array (tracker.md A.2)
    # ISO 3166-1 alpha-2 (e.g. "IN", "CA") -- the default region phone_utils.normalize_
    # phone() parses this product's leads' numbers against. Added after a real bug: a
    # Canadian lead's toll-free number matched the old India-only heuristic by
    # coincidence and would have gotten "91" prepended for WhatsApp -- a message to a
    # fabricated, unrelated number (tracker.md, 2026-08-17).
    target_country = Column(String, default="IN")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 2. LEADS
class Lead(Base):
    __tablename__ = "leads"
    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String, nullable=False)
    website_url = Column(String)
    instagram_url = Column(String)
    facebook_url = Column(String)
    linkedin_url = Column(String)
    primary_email = Column(String)
    primary_phone = Column(String)
    whatsapp_number = Column(String)
    contact_person_name = Column(String)
    contact_person_role = Column(String)
    status = Column(String, default="DISCOVERED")
    # DISCOVERED, ENRICHED, REVIEWED, SCORED, OUTREACHING, OUTREACHED,
    # ENGAGED, HOT_LEAD, CONVERTED, REJECTED
    source = Column(String)
    region_location = Column(String)
    sales_route = Column(String, default="UNASSIGNED")
    # UNASSIGNED, SAAS_PRODUCT, CUSTOM_DEV — set by dual_sales_engine.py (§8.2)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 3. FIRMOGRAPHICS
class LeadFirmographics(Base):
    __tablename__ = "lead_firmographics"
    id = Column(String, primary_key=True, default=_uuid)
    lead_id = Column(String, ForeignKey("leads.id", ondelete="CASCADE"), unique=True, nullable=False)
    linkedin_url = Column(String)
    company_size_range = Column(String)
    industry = Column(String)
    remote_work_indicators = Column(Text, default="{}")
    tech_stack = Column(Text, default="[]")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 4. REVIEW INSIGHTS
class LeadReviewInsight(Base):
    __tablename__ = "lead_review_insights"
    id = Column(String, primary_key=True, default=_uuid)
    lead_id = Column(String, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    review_source = Column(String, default="GOOGLE_REVIEWS")
    average_rating = Column(REAL)
    total_reviews_count = Column(Integer)
    pain_points_extracted = Column(Text, default="[]")
    sentiment_score = Column(REAL)
    raw_review_snippets = Column(Text, default="[]")
    analyzed_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 5. LEAD SCORES
class LeadScore(Base):
    __tablename__ = "lead_scores"
    id = Column(String, primary_key=True, default=_uuid)
    lead_id = Column(String, ForeignKey("leads.id", ondelete="CASCADE"), unique=True, nullable=False)
    score = Column(Integer, nullable=False)
    tier = Column(String, nullable=False)  # HOT, WARM, COLD
    confidence = Column(REAL, default=0.0)
    scoring_breakdown = Column(Text, default="{}")
    justification = Column(Text)
    evaluated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 6. OUTREACH CAMPAIGNS
class OutreachCampaign(Base):
    __tablename__ = "outreach_campaigns"
    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    icp_rules = Column(Text, default="{}")
    channel_config = Column(Text, default="{}")
    status = Column(String, default="ACTIVE")  # ACTIVE, PAUSED, RETIRED
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 7. OUTREACH LOGS
class OutreachLog(Base):
    __tablename__ = "outreach_logs"
    id = Column(String, primary_key=True, default=_uuid)
    lead_id = Column(String, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    campaign_id = Column(String, ForeignKey("outreach_campaigns.id", ondelete="SET NULL"))
    variant_id = Column(String)
    channel = Column(String, nullable=False)  # EMAIL, CONTACT_FORM, WHATSAPP
    message_subject = Column(String)
    message_body = Column(Text, nullable=False)
    status = Column(String, nullable=False)  # SENT, FAILED, DELIVERED, BOUNCED
    sent_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    # Provider's own message id -- Meta's wamid for WhatsApp, Resend's email id for
    # EMAIL. Captured at send time so a later read-receipt/open webhook can match back
    # to this exact row (see api/inbound.py's status handling, api/webhooks.py's Resend
    # handler). Real "Seen" tracking -- see tracker.md, no fabricated/estimated value.
    provider_message_id = Column(String)
    read_at = Column(TIMESTAMP)


# 8. INBOUND CONVERSATIONS
class InboundConversation(Base):
    __tablename__ = "inbound_conversations"
    __table_args__ = (
        UniqueConstraint("channel", "provider_message_id", name="uq_inbound_channel_msgid"),
    )
    id = Column(String, primary_key=True, default=_uuid)
    lead_id = Column(String, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String, nullable=False)  # EMAIL, WHATSAPP
    provider_message_id = Column(String)  # idempotency key
    sender_type = Column(String, nullable=False)  # LEAD, AI_AGENT, HUMAN_REP
    message_content = Column(Text, nullable=False)
    intent_detected = Column(String)  # INTERESTED, DEMO_REQUESTED, OBJECTION, STOP, AUTO_REPLY
    confidence = Column(REAL)
    ai_suggested_response = Column(Text)
    is_read = Column(Integer, default=0)  # Dashboard's Recent Replies grid -- "Mark as read"
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 9. SUPPRESSION LIST
class SuppressionEntry(Base):
    __tablename__ = "suppression_list"
    __table_args__ = (
        UniqueConstraint("channel", "identifier", name="uq_suppression_channel_identifier"),
    )
    id = Column(String, primary_key=True, default=_uuid)
    channel = Column(String, nullable=False)  # EMAIL, WHATSAPP
    identifier = Column(String, nullable=False)  # email or phone
    reason = Column(String)  # UNSUBSCRIBE, STOP, BOUNCE, MANUAL
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 10. JOBS
class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=_uuid)
    job_type = Column(String, nullable=False)
    # DISCOVER, ENRICH, REVIEW, SCORE, OUTREACH_EMAIL, OUTREACH_WA, CLASSIFY_INBOUND, ADAPT
    payload = Column(Text, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, CLAIMED, DONE, FAILED, DEAD
    run_after = Column(TIMESTAMP, server_default=func.current_timestamp())
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    last_error = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 11. DAILY REPORTS
class DailyReport(Base):
    __tablename__ = "daily_reports"
    id = Column(String, primary_key=True, default=_uuid)
    report_date = Column(String, unique=True, nullable=False)
    metrics_summary = Column(Text, default="{}")
    executive_summary_text = Column(Text)
    generated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 12. AGENT EVENTS
class AgentEvent(Base):
    __tablename__ = "agent_events"
    id = Column(String, primary_key=True, default=_uuid)
    agent = Column(String, nullable=False)  # ICP, REVIEW, SCORING, OUTREACH, INBOUND, QC
    lead_id = Column(String)
    action_type = Column(String, nullable=False)  # SCORE, DRAFT_OUTREACH, CLASSIFY_INTENT...
    confidence = Column(REAL)
    risk_level = Column(String)  # LOW, MEDIUM, HIGH, CRITICAL
    routed_to = Column(String)  # EXECUTE, QC_REVIEW, HUMAN_ESCALATION, IMMEDIATE
    payload = Column(Text, default="{}")
    outcome = Column(String)  # APPROVED, REJECTED, SENT, ESCALATED...
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 13. CAMPAIGN VARIANTS
class CampaignVariant(Base):
    __tablename__ = "campaign_variants"
    id = Column(String, primary_key=True, default=_uuid)
    campaign_id = Column(String, ForeignKey("outreach_campaigns.id", ondelete="CASCADE"), nullable=False)
    label = Column(String, nullable=False)  # 'A', 'B', ...
    hook_type = Column(String)  # PAIN_POINT, PROOF, TIME_SAVINGS
    subject_template = Column(Text)
    body_template = Column(Text)
    sends = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    allocation_weight = Column(REAL, default=0.5)
    status = Column(String, default="ACTIVE")  # ACTIVE, RETIRED
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 14. KNOWLEDGE MEMORY
class KnowledgeMemory(Base):
    __tablename__ = "knowledge_memory"
    id = Column(String, primary_key=True, default=_uuid)
    category = Column(String, nullable=False)  # OBJECTION_SCRIPT, FAQ, COMPETITOR, WINNING_HOOK
    key = Column(String)  # e.g. objection type / industry
    content = Column(Text, nullable=False)  # JSON or text
    embedding = Column(Text)  # optional: JSON float array
    score = Column(REAL, default=0.0)  # performance weighting
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 15. TEAM CAPACITY (executive add — §8.3)
class TeamCapacity(Base):
    __tablename__ = "team_capacity"
    id = Column(String, primary_key=True, default=_uuid)
    team_name = Column(String, nullable=False)  # 'ONBOARDING', 'DEV_SERVICES'
    total_slots = Column(Integer, nullable=False, default=10)
    occupied_slots = Column(Integer, nullable=False, default=0)
    max_utilization_pct = Column(Integer, default=90)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 16. CLIENT LIFECYCLE (executive add — §8.5)
class ClientLifecycle(Base):
    __tablename__ = "client_lifecycle"
    id = Column(String, primary_key=True, default=_uuid)
    lead_id = Column(String, ForeignKey("leads.id", ondelete="CASCADE"), unique=True, nullable=False)
    onboarding_status = Column(String, default="NOT_STARTED")
    current_mrr = Column(REAL, default=0.0)
    contract_start_date = Column(DATE)
    contract_end_date = Column(DATE)
    upsell_opportunity = Column(Text)
    referral_requested = Column(Integer, default=0)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 17. PRODUCT STRATEGIES (tracker.md A.2 — ICP Strategy Agent output, versioned)
class ProductStrategy(Base):
    __tablename__ = "product_strategies"
    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    icp = Column(Text, default="{}")
    search_queries = Column(Text, default="[]")
    target_complaints = Column(Text, default="[]")
    source = Column(String, nullable=False)  # AI_GENERATED, HUMAN_ADDED
    status = Column(String, default="ACTIVE")  # ACTIVE, SUPERSEDED
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 18. DISCOVERY RUNS (tracker.md A.2 — per product+query+region cooldown tracking)
class DiscoveryRun(Base):
    __tablename__ = "discovery_runs"
    __table_args__ = (
        UniqueConstraint("product_id", "query", "region", name="uq_discovery_run"),
    )
    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    query = Column(String, nullable=False)
    region = Column(String, nullable=False)
    last_run_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 19. SYSTEM SETTINGS (Step 4.4 — dashboard-controlled runtime switches)
class SystemSetting(Base):
    __tablename__ = "system_settings"
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())
