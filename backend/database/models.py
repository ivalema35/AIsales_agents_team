import secrets
import uuid

from sqlalchemy import Column, String, Text, Integer, REAL, DATE, TIMESTAMP, ForeignKey, UniqueConstraint, func

from database.db_config import Base


def _uuid():
    return str(uuid.uuid4())


def _reference_code():
    # Phase 12 Step 12.1 -- a short, operator-quotable id for alerts/conversation ("Ref:
    # LD-3F9A2B1C"), since the real Lead.id UUID is correct for the DB but useless in a
    # message a human reads. 8 hex chars (4.29B space) makes a collision practically
    # impossible at this project's real lead volume -- the DB-level UNIQUE index (see
    # schema.sql) is the actual backstop, not a retry loop here.
    return "LD-" + secrets.token_hex(4).upper()


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
    # Phase 7 Step 7.1 -- human-set boundaries the AI works freely inside, same precedent
    # as target_regions (tracker.md A.2): a human names WHICH business categories/roles to
    # go after, the AI decides the actual queries/matches within that. Both optional; an
    # empty list means "unchanged from today" everywhere they're read.
    target_business_categories = Column(Text, default="[]")  # JSON array
    target_person_roles = Column(Text, default="[]")         # JSON array
    # Phase 9 Step 9.3 -- day-offsets between follow-up touches, e.g. [3,7]. Empty = no
    # follow-ups for this product (today's single-touch behavior, unchanged).
    followup_cadence_days = Column(Text, default="[]")       # JSON array of integers
    # Phase 11 Step 11.5 (tracker.md A.10) -- other products the admin chose to cross-sell
    # alongside this one. Empty = no cross-sell, today's behavior unchanged.
    cross_sell_product_ids = Column(Text, default="[]")      # JSON array of product ids
    # Phase 16 Step 16.4 -- free-text guidelines (same "shape, not rigid template"
    # precedent as message_formats.sections, tracker.md A.7), NOT a fixed dropdown enum,
    # e.g. "Urgent & ROI-driven, short and punchy" or "Formal HTML email with bullet
    # points". NULL/empty = today's unchanged default drafting behavior. Once Phase 17's
    # campaigns exist, a campaign's own strategy_angle becomes an ADDITIONAL directive
    # source layered on top of these, not a replacement for them.
    default_tone = Column(Text)
    default_format = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 2. LEADS
class Lead(Base):
    __tablename__ = "leads"
    id = Column(String, primary_key=True, default=_uuid)
    reference_code = Column(String, unique=True, default=_reference_code)
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
    # Phase 17 Step 17.1 -- nullable, and deliberately so: every lead the existing
    # autonomous discovery pipeline creates has no campaign context and keeps this NULL,
    # behaving byte-identically to before this column existed (P17 DoD).
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="SET NULL"))
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
    open_count = Column(Integer, default=0)  # Step 9.4 -- real count of email.opened events
    # Phase 8 Step 8.4 -- JSON array of every subject-line candidate the Outreach Agent
    # generated for this send, not just the one it picked (message_subject). Selection
    # here is still AI judgment, not performance-driven (no send history exists yet to
    # learn from) -- Phase 9 reads this column back to measure candidates retrospectively.
    subject_candidates = Column(Text)
    # Phase 14 Step 14.4 -- the exact Step 11.1 structured section list (JSON) this EMAIL
    # was rendered from -- the one canonical content object every cross-channel copy
    # rendering reads from (services/outreach/text_renderer.py), never a second LLM call.
    # NULL for WHATSAPP rows (no structured sections exist for that channel) and for any
    # EMAIL row sent before this column existed -- old sends are never backfilled.
    content_sections = Column(Text)


# 2026-09-07, real bug found live: every volume/analytics/escalation query that needs
# "was this message actually dispatched" was checking `status == "SENT"` literally -- but
# a webhook (api/webhooks.py's Resend handler, api/inbound.py's WhatsApp status handler)
# advances a real send's status to DELIVERED (or BOUNCED) as soon as the provider confirms
# it, often within seconds. A real WhatsApp message that reached DELIVERED before a
# metrics/to-do check ran was silently invisible everywhere that checked `== "SENT"` --
# it looked like nothing had been sent at all. SENT/DELIVERED/BOUNCED all mean the send
# left our system successfully (a bounce is a real delivery attempt that failed
# downstream, not a send that failed on our end); only FAILED means it never went out.
SUCCESSFULLY_SENT_STATUSES = ("SENT", "DELIVERED", "BOUNCED")


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
        UniqueConstraint("campaign_id", "query", "region", name="uq_discovery_run_v2"),
    )
    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    query = Column(String, nullable=False)
    region = Column(String, nullable=False)
    # Step 17.7 (2026-09-02) -- discovery is now campaign-driven: the (query, region) pair
    # comes straight from one campaign's own target_segment, so cooldown tracking is scoped
    # per-campaign, not per-product -- two campaigns for the same product that happen to
    # share a query/region must NOT share one cooldown clock. Nullable: a legacy row (from
    # before this column existed) or a manually-enqueued job with no campaign context still
    # has somewhere to live.
    #
    # 2026-09-08/09, real live incident: the constraint above was left on
    # (product_id, query, region) for a week after this comment first called that a "low-
    # probability" risk -- it materialized for real once the auto-create-campaign-on-approve
    # flow made it easy for the AI to suggest a second campaign for the same product with an
    # overlapping (query, region). The resulting IntegrityError wasn't caught anywhere in
    # discovery_scheduler.py's tick loop, so it poisoned that loop's whole DB session --
    # every later statement on it (including the process's own heartbeat write) then failed
    # too, and the scheduler sat silently DOWN for 16 hours until a human noticed and
    # restarted it. `migrate.py`'s `_fix_discovery_run_constraint()` rebuilds this table on
    # any DB still carrying the old constraint name; a fresh install picks up
    # `uq_discovery_run_v2` directly from `schema.sql`. See also
    # jobs/discovery_scheduler.py's own `_run_discovery_tick()` for the added
    # try/except+rollback that now stops any future per-row failure from cascading the
    # same way, regardless of its cause.
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="CASCADE"))
    last_run_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 19. SYSTEM SETTINGS (Step 4.4 — dashboard-controlled runtime switches)
class SystemSetting(Base):
    __tablename__ = "system_settings"
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 20. SYSTEM HEARTBEATS (Phase 6 Step 6.1 — liveness of the long-running processes)
class SystemHeartbeat(Base):
    __tablename__ = "system_heartbeats"
    process_name = Column(String, primary_key=True)
    status = Column(String, nullable=False, default="RUNNING")  # RUNNING, IDLE, ERROR
    detail = Column(Text, default="{}")
    # Per-process expected beat rate — these loops run at very different speeds (2s to 300s),
    # so staleness must be judged per process, never against one global window. See schema.sql.
    expected_interval_seconds = Column(Integer, nullable=False, default=60)
    last_seen_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    started_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 21. LEAD CONTACTS (Phase 7 Step 7.3 — multiple people per lead; leads.primary_email/
# primary_phone/contact_person_name/_role stay unchanged as the canonical outreach
# target, this table is purely additive. Populated later by Step 7.4 (Hunter's
# discarded contact fields) and Step 7.5 (role-targeted LinkedIn person discovery).)
class LeadContact(Base):
    __tablename__ = "lead_contacts"
    id = Column(String, primary_key=True, default=_uuid)
    lead_id = Column(String, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String)
    role = Column(String)
    seniority = Column(String)
    department = Column(String)
    email = Column(String)
    phone = Column(String)
    linkedin_url = Column(String)
    is_decision_maker = Column(Integer, default=0)
    source = Column(String)  # e.g. "HUNTER", "LINKEDIN"
    confidence = Column(REAL)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 22. MESSAGE FORMATS (Phase 8 Step 8.1 — admin-authored message STRUCTURE. See
# tracker.md A.7: `sections` is an ordered list of GUIDELINES the AI follows while
# writing its own adaptive draft, never literal template pieces it fills in. Versioned
# like ProductStrategy (status ACTIVE/SUPERSEDED, never overwritten).)
class MessageFormat(Base):
    __tablename__ = "message_formats"
    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"))  # NULL = global default
    channel = Column(String, nullable=False)  # "EMAIL" or "WHATSAPP"
    sections = Column(Text, nullable=False)  # JSON array of guideline strings, ordered
    version = Column(Integer, nullable=False, default=1)
    status = Column(String, default="ACTIVE")  # ACTIVE, SUPERSEDED
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 23. CONTENT ASSETS (Phase 8 Step 8.2 — the AI SELECTS from this library, never
# invents a URL. A format slot with no matching active asset renders without that
# slot rather than fabricating one.)
class ContentAsset(Base):
    __tablename__ = "content_assets"
    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"))  # NULL = any product
    asset_type = Column(String, nullable=False)  # DEMO_URL, VIDEO_URL, CASE_STUDY, TESTIMONIAL, TEXT_BLOCK
    title = Column(String, nullable=False)
    value = Column(Text, nullable=False)  # the URL, or the text itself for TEXT_BLOCK
    tags = Column(Text, default="[]")  # JSON array
    is_active = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 24. OUTREACH SEQUENCES (Phase 9 Step 9.3 -- per-lead+channel follow-up cadence state.
# Only ever created when the lead's product has a real cadence configured; every send it
# drives goes through the exact same OUTREACH_EMAIL/OUTREACH_WA handlers as a fresh
# touch, so suppression/QC/pacing apply identically at every step.)
class OutreachSequence(Base):
    __tablename__ = "outreach_sequences"
    id = Column(String, primary_key=True, default=_uuid)
    lead_id = Column(String, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String, nullable=False)  # "EMAIL" or "WHATSAPP"
    original_sent_at = Column(TIMESTAMP, nullable=False)
    next_step = Column(Integer, nullable=False, default=2)
    max_steps = Column(Integer, nullable=False)
    next_run_at = Column(TIMESTAMP, nullable=False)
    status = Column(String, default="ACTIVE")  # ACTIVE, CLAIMED, COMPLETED, STOPPED
    terminal_reason = Column(String)  # REPLIED, SUPPRESSED, MAX_STEPS_REACHED
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 25. WHATSAPP TEMPLATES (Phase 9 Step 9.5 -- mirrors each template's real Meta-side
# approval state; `purpose` FOLLOW_UP closes the real gap found live testing Step 9.3,
# where a WhatsApp follow-up had to resend the exact same first-touch template.)
class WhatsappTemplate(Base):
    __tablename__ = "whatsapp_templates"
    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False, unique=True)
    language = Column(String, nullable=False, default="en")
    category = Column(String, nullable=False)  # MARKETING, UTILITY, AUTHENTICATION
    purpose = Column(String, nullable=False, default="FIRST_TOUCH")  # FIRST_TOUCH, FOLLOW_UP
    followup_level = Column(Integer)  # Phase 13 Step 13.2 -- 1/2/3, only meaningful when purpose=FOLLOW_UP
    # A static URL button baked into the approved template (no {{n}} suffix, so no
    # per-send parameter needed) -- null = no button, unchanged behavior.
    button_url = Column(String)
    button_label = Column(String)
    # 2026-09-10, real user ask: Meta's own real limit is up to 2 URL buttons per
    # template (verified against Meta's live docs, not assumed) -- a second, independent
    # static URL button, same shape/rules as the first. Null = only one button (or none).
    button_2_url = Column(String)
    button_2_label = Column(String)
    body_text = Column(Text, nullable=False)
    variable_labels = Column(Text, default="[]")  # JSON array
    # DRAFT, PENDING, APPROVED, REJECTED, ADMIN_REJECTED -- see schema.sql for the full
    # meaning of each (Step 9.6 added DRAFT/ADMIN_REJECTED for AI-authored templates).
    status = Column(String, default="PENDING")
    rejection_reason = Column(Text)
    meta_template_id = Column(String)
    # NULL = shared/global (every product may use it); set = only that product may.
    product_id = Column(String, ForeignKey("products.id"))
    is_active = Column(Integer, default=1)  # manual kill-switch, independent of Meta's own status
    origin = Column(String, default="ADMIN")  # ADMIN (dashboard form) or AI (Step 9.6 draft)
    reasoning = Column(Text)  # only for origin=AI -- the drafting agent's own explanation
    # 2026-09-09, real user ask: a human-requested template (a specific campaign's own
    # "Ask AI for a template" click) must never come back empty just because QC vetoed
    # every attempt -- nothing reaches Meta without an explicit human approve anyway, so
    # QC's concerns become a visible caution on the DRAFT instead of a silent block.
    # Kept separate from `reasoning` (the AI's OWN explanation) so the UI can show them
    # as two distinct things: what the AI believes vs. what QC flagged for human review.
    qc_caution = Column(Text)
    # JSON {"reason": ..., "campaign_strategy_angle": ...} -- the real grounding this draft
    # was written from, kept so a later human feedback revision (revise_draft_template)
    # can stay grounded in the same real signal/campaign angle instead of starting blind.
    draft_context = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    # 2026-09-08, real finding: no model anywhere in this file has `onupdate` on its own
    # updated_at, so it silently never changes past insert time on a plain ORM write
    # (only a few job_queue.py raw-SQL statements explicitly set it themselves). Added
    # here specifically because get_approved_first_touch_template()/get_approved_followup_
    # template() order candidates by THIS column to break ties when more than one template
    # is scoped to the same product -- without onupdate, reassigning product_id (the new
    # Daily Review picker) wouldn't actually move a template to the front of that order.
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())


class ChannelPolicy(Base):
    __tablename__ = "channel_policies"
    id = Column(String, primary_key=True, default=_uuid)
    country_code = Column(String, nullable=False, unique=True)  # ISO 3166-1 alpha-2, e.g. "IN", "CA"
    allowed_channels = Column(Text, nullable=False, default="[]")  # JSON array
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


class SocialMessageQueue(Base):
    __tablename__ = "social_message_queue"
    id = Column(String, primary_key=True, default=_uuid)
    lead_id = Column(String, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String, nullable=False)  # LINKEDIN, INSTAGRAM, FACEBOOK
    message_text = Column(Text, nullable=False)
    reasoning = Column(Text)
    status = Column(String, default="QUEUED")  # QUEUED, SENT, DISMISSED
    sent_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 29. INTEREST RESPONSES (Phase 12 Step 12.2/12.3) -- one row per real Yes/No click.
# UNIQUE(outreach_log_id, response) is what makes a double-click, a mail-scanner
# prefetch, or a browser retry idempotent AT THE DB LEVEL (catch IntegrityError, same
# posture as inbound_conversations' own dedup constraint) rather than a race-prone
# check-then-insert in application code. The SAME send can carry both a YES and a NO row
# (a lead who changes their mind) -- only a repeat of the SAME response is a duplicate.
class InterestResponse(Base):
    __tablename__ = "interest_responses"
    id = Column(String, primary_key=True, default=_uuid)
    lead_id = Column(String, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    outreach_log_id = Column(String, ForeignKey("outreach_logs.id", ondelete="CASCADE"), nullable=False)
    response = Column(String, nullable=False)  # YES or NO
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    __table_args__ = (UniqueConstraint("outreach_log_id", "response"),)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 30. PROSPECTS (Phase 15 Step 15(B).1) -- person-level, no parent lead. Deliberately NOT
# rows in `leads`: a prospect never went through discovery/scoring/ICP matching, so mixing
# it into that table would corrupt every funnel metric the analytics layer computes.
class Prospect(Base):
    __tablename__ = "prospects"
    id = Column(String, primary_key=True, default=_uuid)
    search_id = Column(String, ForeignKey("prospect_searches.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String)
    headline = Column(String)  # the raw title/role text found alongside the match
    linkedin_url = Column(String, nullable=False)
    current_company = Column(String)
    location_text = Column(String)  # raw location signal found, not a verified field
    email = Column(String)
    phone = Column(String)
    source = Column(String, nullable=False)  # e.g. "SERPER_XRAY"
    confidence = Column(REAL)
    enrichment_status = Column(String, default="DISCOVERED")  # DISCOVERED, ENRICHED, NO_CONTACT_FOUND
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    __table_args__ = (UniqueConstraint("linkedin_url"),)


# 31. PROSPECT SEARCHES (Phase 15 Step 15(B).2) -- one row per real search run: the
# criteria, the provider, how many real results it found, and the real spend incurred --
# the source of truth run_prospect_search() checks BEFORE the next search, so a configured
# budget genuinely blocks the next run rather than only warning after the fact.
class ProspectSearch(Base):
    __tablename__ = "prospect_searches"
    id = Column(String, primary_key=True, default=_uuid)
    criteria_text = Column(String, nullable=False)  # the raw human criteria, e.g. "AI developer in Mehsana, 3 years experience"
    role_keywords = Column(String)
    location = Column(String)
    provider = Column(String, nullable=False)  # "SERPER_XRAY"
    result_count = Column(Integer, default=0)
    spend = Column(REAL, default=0.0)  # real cost incurred, from the admin-configured per-search rate
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 32. KNOWLEDGE BASE ITEMS (Phase 16 Step 16.1/16.2/16.8) -- product facts, objection
# answers, real proof, and (Step 16.8, human-approved only) marketing assets the AI
# selects from when replying or drafting -- never a prompt it paraphrases. Zero-
# fabrication rule: this table has exactly one write path, api/knowledge_base.py's
# admin-facing CRUD -- no LLM call anywhere in this codebase inserts a row here.
class KnowledgeBaseItem(Base):
    __tablename__ = "knowledge_base_items"
    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    kind = Column(String, nullable=False)  # FACT, OBJECTION, PROOF, MARKETING_ASSET
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 33. CAMPAIGNS (Phase 17 Step 17.1) -- a dated, strategy-angled grouping layered on top
# of the existing pipeline, never a second targeting system. `target_segment` is a free
# JSON object set by a human at creation (or, once Phase 18 exists, proposed by the AI
# planner) -- deliberately NOT validated against the product's own target_regions/
# target_business_categories/target_person_roles (revised 2026-09-01, tracker.md): the
# operator wants a campaign able to genuinely explore a segment outside the product's
# standing config, with oversight coming from human review, not a schema constraint.
class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    scheduled_date = Column(DATE)
    target_segment = Column(Text, default="{}")  # free JSON object, no fixed shape
    strategy_angle = Column(Text)
    # PROPOSED, APPROVED, RUNNING, COMPLETED, PAUSED (Step 17.5) -- PROPOSED->APPROVED only
    # via Phase 18's human review action once that exists; nothing sets it automatically yet.
    status = Column(String, default="PROPOSED")
    # Step 18.1 -- SUPERSEDED by Phase 21's todo_items table (2026-09-05): generate_campaign_todo()
    # no longer writes here, every real to-do is its own addressable TodoItem row instead. Column
    # kept, not deleted (non-destructive precedent, e.g. Step 17.6), for any historical row still
    # holding pre-Phase-21 data.
    daily_todo = Column(Text, default="[]")
    metrics_summary = Column(Text, default="{}")  # JSON cache, Step 17.3 -- never authoritative
    # Step 18.1/17.6 -- the AI's own proposed target lead count for this campaign's discovery
    # batch (e.g. 100). Nullable: no goal set means today's continuous cooldown-paced discovery,
    # not "no discovery." Raisable by a later day's strategist proposal once reached.
    lead_count_goal = Column(Integer)
    # Step 18.1/18.4 -- SUPERSEDED by Phase 21 (2026-09-05): a structural proposal now lives on
    # its own TodoItem.proposal, applied by approve_todo_item() per-item. Column kept, not
    # deleted, for the same non-destructive reason as daily_todo above.
    pending_strategy_proposal = Column(Text)
    # Phase 18 Step 18.2 -- SUPERSEDED by Phase 21 (2026-09-05): there is no more single
    # whole-day approval concept once approval is per-TodoItem (each item has its own
    # resolved_at). Column kept, not deleted, for the same non-destructive reason as
    # daily_todo above.
    last_approved_date = Column(String)
    # Phase 20 Step 20.3 -- Execution Watchdog. NULL means normal (no active alert). Set to
    # a JSON object ({"reason","bounce_count","message","raised_at"}) the moment a real
    # anomaly (3 consecutive real send failures/bounces) is detected for this campaign's own
    # batch -- while set, _run_outreach_tick skips claiming further leads for THIS campaign
    # only (every other campaign is unaffected). Cleared only by a human action
    # (services/campaign_service.py clear_campaign_watchdog_alert()), never by the system
    # re-checking on its own -- this is a real pause requiring real review, not a cooldown.
    watchdog_alert = Column(Text)
    # Kickoff template preview (built 2026-09-05 from Step 18.1b intent): JSON draft
    # (subject/body/sections) shown on the daily review when this campaign has no real
    # leads yet. Uses literal [Business Name]/[Pain Point] placeholders -- never invents
    # a fictional business. Once a real lead is tagged, get_daily_review prefers that lead's
    # sample instead. Cleared when strategy_angle is applied/changed so the next review
    # regenerates against the new angle.
    kickoff_draft = Column(Text)
    # HTML vs plain-text email render (2026-09-05): HTML = Phase 11 designed sections +
    # render_email_html for preview and send; TEXT = prose draft, plain preview, send
    # without designed sections (email_service simple HTML fallback). Default HTML.
    # Set by AI strategist proposal, Daily Review chips, or free-text feedback.
    email_render_mode = Column(String, default="HTML")  # HTML | TEXT
    # Phase 21 -- the lightweight fingerprint _run_signal_driven_todo_tick() diffs against to
    # decide "did anything real change since the last to-do generation for this campaign".
    # JSON: {"sent","opened","replied","hot","has_target"}. Updated every time
    # generate_campaign_todo() actually runs (daily floor OR signal-driven), never otherwise.
    last_todo_signal = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 34. STRATEGY INSIGHTS (Phase 19 Step 19.1-19.3) -- one row per learned strategy rule,
# reusing the EXACT "most recent ACTIVE row wins, superseded rows kept not deleted" pattern
# already proven in ProductStrategy (Phase 7, consumed since Phase 15(A)). Grouped by
# (product_id, domain) -- `domain` is the real business vertical (campaign.target_segment's
# own `industry` value) real campaigns for this product have actually targeted, POOLED
# across however many campaigns tried it, not a single campaign's own result. Simplified
# from the original 4-field spec (winning/losing angle + a separate winning_tone) to just
# winning/losing angle -- this project's Campaign model has no field distinguishing "tone"
# from "angle" (`strategy_angle` is the one free-text axis a campaign has), so a second
# column for the same real data would carry nothing a human couldn't already read in
# `winning_angle` itself.
class StrategyInsight(Base):
    __tablename__ = "strategy_insights"
    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    domain = Column(String, nullable=False)
    winning_angle = Column(Text, nullable=False)
    losing_angle = Column(Text)
    confidence = Column(REAL)
    # Must quote the real aggregated numbers it was computed from -- Step 19.3's own gate,
    # enforced by prompt instruction + real-testing, not a schema constraint.
    rationale = Column(Text, nullable=False)
    status = Column(String, default="ACTIVE")  # ACTIVE, SUPERSEDED
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 35. CAMPAIGN THESES (Phase 20 Step 20.1) -- one row per real IST day Step 18.1's strategist
# runs for a campaign: what it believed going in (`hypothesis`), what today's real numbers
# actually showed (`observation`), and what it's doing differently as a result
# (`pivot_decision`, or an explicit "no change, still testing X"). Deliberately separate from
# `strategy_insights` (Table 34) -- that is a cross-campaign, floor-gated, validated RULE; this
# is one campaign's own evolving, day-by-day narrative, real even when there's nothing yet
# validated enough to write as a rule. One row per (campaign_id, day) -- a same-day feedback
# regeneration updates this day's row rather than creating a second one for the same date.
class CampaignThesis(Base):
    __tablename__ = "campaign_theses"
    __table_args__ = (
        UniqueConstraint("campaign_id", "day", name="uq_campaign_thesis_day"),
    )
    id = Column(String, primary_key=True, default=_uuid)
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    day = Column(String, nullable=False)  # ISO date (YYYY-MM-DD, IST)
    hypothesis = Column(Text, nullable=False)
    observation = Column(Text)
    pivot_decision = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# 36. TODO ITEMS (Phase 21) -- SUPERSEDES Step 18.1's campaign.daily_todo/pending_strategy_
# proposal/last_approved_date. Every real to-do the AI Sales Manager raises is now its own
# addressable row -- individually feedback-able (Step 20.4's pushback mechanism reused) and
# individually approved/dismissed, never bundled into one whole-day bulk action. A new
# generation only ever ADDS rows; an existing PENDING row is never silently overwritten --
# nothing a human hasn't acted on ever disappears on its own.
#
# Two scopes, one table, one review queue:
# - CAMPAIGN: tied to a real, already-existing campaign (follow-up, targeting/angle/render-mode
#   proposal, a knowledge-gap note, a dispatch-readiness nudge -- everything
#   generate_campaign_todo() used to write into daily_todo).
# - GLOBAL: NOT tied to any campaign -- "this product's leads are trending strong in industry X
#   right now, worth a new campaign" (what generate_campaign_suggestion() used to only log as an
#   AgentEvent). Approving a GLOBAL item never creates a campaign by itself -- a campaign is
#   always human-created (the same invariant Phase 17 established) -- it hands the frontend a
#   pre-fill payload for the existing CampaignFormModal instead.
class TodoItem(Base):
    __tablename__ = "todo_items"
    id = Column(String, primary_key=True, default=_uuid)
    scope = Column(String, nullable=False)  # CAMPAIGN | GLOBAL
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="CASCADE"))  # CAMPAIGN only
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"))    # GLOBAL only
    # 2026-09-07: set when this to-do is about ONE specific lead (e.g. no dispatch draft
    # ever cleared QC, a human must write this one by hand) -- lets dedup key on
    # (campaign_id, lead_id, label) instead of one shared label colliding across every
    # other lead in the same campaign.
    lead_id = Column(String, ForeignKey("leads.id", ondelete="CASCADE"))
    label = Column(String)         # free-text, e.g. "Follow-up", "Conflict", "New campaign idea"
    text = Column(Text, nullable=False)  # current state -- what per-item feedback revises
    # Optional JSON structural change: target_segment/lead_count_goal/strategy_angle/
    # email_render_mode (CAMPAIGN, applied by approve_todo_item onto the real Campaign row) or
    # a full campaign-creation prefill (GLOBAL, handed to the frontend, never applied server-side).
    proposal = Column(Text)
    confidence = Column(REAL)      # Step 20.2's honest confidence, carried over per-item
    rationale = Column(Text)
    # 2026-09-07: a real, structural blocker (Discovery off, ready-to-send-but-outreach-off,
    # an OPERATIONAL_READINESS failure) vs an ordinary strategic note/proposal -- computed in
    # Python from a fixed set of known labels, never left to the model to self-classify.
    # Drives the Campaign Calendar's red "needs action" alert (vs the routine gold clock).
    is_blocker = Column(Integer, default=0)
    status = Column(String, default="PENDING")  # PENDING | APPROVED | DISMISSED
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    resolved_at = Column(TIMESTAMP)
