import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams, useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowLeft, ChevronLeft, ChevronRight, Mail, Phone, Globe, MapPin, User as UserIcon, Building2,
  Gauge, AlertTriangle, Clock, Bot, CheckCircle2, XCircle, AlertCircle,
  MessageCircle, MessagesSquare, BellOff, Trophy, ThumbsDown, Share2, Copy, Send, X,
  Check, CheckCheck, Users, Star,
} from "lucide-react";
import { api } from "../api/client";
import Badge from "../components/ui/Badge";
import { statusBadgeClass } from "../lib/statusColors";
import { useConfirm } from "../lib/ConfirmContext";
import { useToast } from "../lib/ToastContext";
import { InstagramIcon, FacebookIcon, LinkedinIcon } from "../lib/socialIcons";

const TIER_VARIANT = { HOT: "HOT", WARM: "WARM", COLD: "COLD" };

// Fixed order matches how scoring reasons about fit. Labels are plain-language for
// non-technical users -- never show raw keys like "icp_fit" in the UI.
const SCORE_FACTORS = [
  {
    key: "icp_fit",
    label: "Right kind of business?",
    hint: "Does this company match who we usually sell to?",
  },
  {
    key: "pain_match",
    label: "Has a problem we solve?",
    hint: "Did we find a clear pain point our product addresses?",
  },
  {
    key: "reachability",
    label: "Can we reach them?",
    hint: "Do we have email, phone, or social to contact them?",
  },
  {
    key: "buying_signal",
    label: "Showing interest to buy?",
    hint: "Any sign they are actively looking or ready to buy?",
  },
];

const TIER_PLAIN = {
  HOT: {
    title: "High priority",
    blurb: "Strong fit — worth contacting soon.",
  },
  WARM: {
    title: "Worth a look",
    blurb: "Decent fit — a good candidate when you have time.",
  },
  COLD: {
    title: "Low priority for now",
    blurb: "Weak fit or little buying signal — skip unless something changes.",
  },
};

// LLM sometimes returns 0–1 floats, sometimes 0–100 points (e.g. 20 + 15 = score 35).
// Never multiply a 0–100 value by 100 again — that produced the broken "2000%" bars.
function normalizeScoreFactor(raw) {
  const n = Number(raw);
  if (!Number.isFinite(n) || n <= 0) return 0;
  if (n <= 1) return n;
  if (n <= 100) return Math.min(1, n / 100);
  return 1;
}

function factorStrength(normalized) {
  if (normalized <= 0) return { label: "None", tone: "text-ink-500 bg-parchment-raised-2" };
  if (normalized < 0.25) return { label: "Weak", tone: "text-ink-600 bg-parchment-raised-2" };
  if (normalized < 0.5) return { label: "Fair", tone: "text-warm-800 bg-warm-100" };
  if (normalized < 0.75) return { label: "Good", tone: "text-good-800 bg-good-100" };
  return { label: "Strong", tone: "text-good-800 bg-good-100" };
}

function confidencePlain(confidence) {
  const c = Math.max(0, Math.min(1, Number(confidence) || 0));
  const pct = Math.round(c * 100);
  if (c >= 0.7) return { label: "Quite sure", detail: `${pct}% sure about this read`, pct };
  if (c >= 0.4) return { label: "Somewhat sure", detail: `${pct}% sure — treat as a guide, not gospel`, pct };
  return { label: "Not very sure", detail: `Only ${pct}% sure — double-check before acting`, pct };
}

function barColor(value) {
  if (value >= 0.7) return "bg-good-600";
  if (value >= 0.4) return "bg-warm-600";
  return "bg-line-strong";
}

function dayLabel(dateStr) {
  const today = new Date().toISOString().slice(0, 10);
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
  if (dateStr === today) return "Today";
  if (dateStr === yesterday) return "Yesterday";
  return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function timeLabel(ts) {
  return new Date(ts.replace(" ", "T") + "Z").toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
}

// Fixed, literal Tailwind classes per color key -- NEVER derive a class name at runtime
// via string manipulation (e.g. "bg-x-500".replace("bg-","text-")). Tailwind's JIT
// compiler only generates CSS for class names it can find literally in the source; a
// runtime-computed string like that produces a real DOM class with no matching CSS rule,
// so the color silently never renders (found and fixed while building this exact file).
const DOT_COLORS = {
  emerald: { bg: "bg-good-100", text: "text-good-700" },
  red: { bg: "bg-alert-100", text: "text-alert-700" },
  amber: { bg: "bg-warm-100", text: "text-warm-700" },
  slate: { bg: "bg-parchment-raised-2", text: "text-ink-500" },
};

// Phase 14 Step 14.1 -- a real, honest per-message delivery state (never a guess: "--"
// covers a channel/event this project genuinely has no signal for, matching
// services/outreach/delivery_status.py's own contract). Single check = Sent, double =
// Delivered, blue double = Seen (WhatsApp-style convention users already recognize),
// emerald double = Replied (strongest possible signal), red X = Failed.
function DeliveryTick({ state }) {
  if (state === "Failed") return <XCircle size={12} className="text-alert-600" />;
  if (state === "Replied") return <CheckCheck size={12} className="text-good-600" />;
  if (state === "Seen") return <CheckCheck size={12} className="text-ink-700" />;
  if (state === "Delivered") return <CheckCheck size={12} className="text-ink-500" />;
  if (state === "Sent") return <Check size={12} className="text-ink-500" />;
  return null;
}

// Server sends raw agent/action_type/outcome/routed_to strings -- this is the one place
// that turns them into plain-language copy a non-tech user can scan (never show
// HUMAN_ESCALATION / ANALYZED / SCORING · Score as-is).
const ACTION_TITLES = {
  SCORE: "Scored this lead",
  ANALYZE_REVIEWS: "Checked public reviews",
  DRAFT_EMAIL: "Drafted an email",
  DRAFT_EMAIL_SECTIONS: "Drafted an email",
  DRAFT_FOLLOWUP_EMAIL: "Drafted a follow-up email",
  DRAFT_SOCIAL: "Drafted a social message",
  DISPATCH_EMAIL: "Tried to send email",
  DISPATCH_WHATSAPP: "Tried to send WhatsApp",
  CLASSIFY_INTENT: "Read their reply",
  REVIEW_DRAFT: "Checked the draft before send",
  REVIEW_SOCIAL_DRAFT: "Checked the social draft",
  REVIEW_TEMPLATE_DRAFT: "Checked a template draft",
  ESCALATE: "Flagged for you",
  KB_GAP_DETECTED: "Found a knowledge gap",
  REDRAFT_REPLY: "Rewrote a reply draft",
  SUGGEST_IMPROVEMENT: "Suggested an improvement",
};

const STATUS_PLAIN = {
  HUMAN_ESCALATION: {
    label: "Needs your review",
    variant: "WARNING",
    blurb: "AI was not sure enough to act alone — take a look before outreach.",
  },
  EXECUTE: { label: "Done", variant: "SUCCESS", blurb: null },
  QC_REVIEW: {
    label: "Needs quality check",
    variant: "WARNING",
    blurb: "Draft or decision should be checked before it goes out.",
  },
  IMMEDIATE_EXECUTE: { label: "Handled right away", variant: "SUCCESS", blurb: null },
  ANALYZED: { label: "Reviews checked", variant: "SUCCESS", blurb: null },
  APPROVED: { label: "Approved", variant: "SUCCESS", blurb: null },
  REJECTED: { label: "Rejected", variant: "DANGER", blurb: "Did not pass the quality check." },
  LLM_FAILED: {
    label: "AI couldn't finish",
    variant: "DANGER",
    blurb: "Something went wrong with the AI call — you may need to retry.",
  },
  NO_INPUT: {
    label: "Nothing to check",
    variant: "NEUTRAL",
    blurb: "No reviews or input were available for this step.",
  },
  DRAFTED: { label: "Draft ready", variant: "SUCCESS", blurb: null },
  EMPTY_DRAFT: { label: "Draft was empty", variant: "WARNING", blurb: null },
  SENT: { label: "Sent", variant: "SUCCESS", blurb: null },
  SKIPPED_NO_TEMPLATE: {
    label: "Skipped — no template",
    variant: "WARNING",
    blurb: "WhatsApp needs an approved template before it can send.",
  },
};

const INTENT_PLAIN = {
  INTERESTED: "Interested",
  DEMO_REQUESTED: "Wants a demo",
  STOP: "Asked to stop",
  OBJECTION: "Has a concern",
  QUESTION: "Asked a question",
  NEUTRAL: "Neutral reply",
  OTHER: "Other",
};

const DELIVERY_PLAIN = {
  Failed: "Failed to send",
  Replied: "They replied",
  Seen: "Seen",
  Delivered: "Delivered",
  Sent: "Sent",
};

function statusPlain(raw) {
  if (!raw) return null;
  if (STATUS_PLAIN[raw]) return STATUS_PLAIN[raw];
  // Unknown backend codes: title-case without SCREAMING_SNAKE
  return {
    label: raw.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()),
    variant: "NEUTRAL",
    blurb: null,
  };
}

function formatAgentPayload(actionType, payload) {
  if (!payload || typeof payload !== "object") return null;
  const parts = [];
  if (actionType === "SCORE") {
    if (payload.tier != null || payload.score != null) {
      parts.push(
        `Marked ${payload.tier || "—"} · ${payload.score != null ? `${payload.score}/100` : "no score"}`
      );
    }
  }
  if (actionType === "ANALYZE_REVIEWS") {
    if (payload.snippet_count != null) parts.push(`Looked at ${payload.snippet_count} review snippet${payload.snippet_count === 1 ? "" : "s"}`);
    if (payload.pain_point_count != null) {
      parts.push(
        payload.pain_point_count === 0
          ? "No clear pain points found"
          : `Found ${payload.pain_point_count} pain point${payload.pain_point_count === 1 ? "" : "s"}`
      );
    }
  }
  if (payload.error) parts.push(`Error: ${String(payload.error).slice(0, 120)}`);
  if (parts.length) return parts.join(" · ");
  // Last resort: skip raw JSON dump for empty or opaque payloads
  const keys = Object.keys(payload);
  if (!keys.length) return null;
  return null;
}

function describeEvent(e) {
  if (e.type === "OUTREACH_SENT") {
    const failed = e.delivery_state === "Failed";
    const channel = e.channel === "WHATSAPP" ? "WhatsApp" : "Email";
    const delivery = DELIVERY_PLAIN[e.delivery_state] || e.delivery_state || e.status;
    return {
      icon: e.channel === "WHATSAPP" ? MessageCircle : Mail,
      color: failed ? "red" : "emerald",
      title: failed ? `${channel} did not send` : `${channel} sent`,
      summary: e.subject || null,
      variant: failed ? "DANGER" : "SUCCESS",
      badge: delivery,
      blurb: null,
      body: e.body,
      extra: null,
    };
  }
  if (e.type === "REPLY_RECEIVED") {
    const positive = ["INTERESTED", "DEMO_REQUESTED"].includes(e.intent_detected);
    const negative = e.intent_detected === "STOP";
    const channel = e.channel === "WHATSAPP" ? "WhatsApp" : "Email";
    const intentLabel = INTENT_PLAIN[e.intent_detected] || (e.intent_detected
      ? e.intent_detected.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())
      : null);
    return {
      icon: e.channel === "WHATSAPP" ? MessageCircle : Mail,
      color: negative ? "red" : positive ? "emerald" : "slate",
      title: `${channel} reply received`,
      summary: intentLabel ? `They seem: ${intentLabel}` : "Reply received — intent not classified yet",
      variant: negative ? "DANGER" : positive ? "SUCCESS" : "NEUTRAL",
      badge: intentLabel || "Unclassified",
      blurb: null,
      body: e.message,
      extra: e.ai_suggested_response ? `Suggested reply: ${e.ai_suggested_response}` : null,
    };
  }

  // AGENT_EVENT
  const statusKey = e.outcome || e.routed_to || "";
  const status = statusPlain(statusKey);
  const escalated = e.routed_to === "HUMAN_ESCALATION" || e.outcome === "HUMAN_ESCALATION";
  const rejected = e.outcome === "REJECTED" || statusKey === "REJECTED";
  const failed = statusKey === "LLM_FAILED";
  const good = ["APPROVED", "EXECUTE", "SENT", "ANALYZED", "DRAFTED", "IMMEDIATE_EXECUTE"].includes(statusKey);

  const title =
    ACTION_TITLES[e.action_type] ||
    (e.action_type
      ? e.action_type.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())
      : "System update");

  const payloadSummary = formatAgentPayload(e.action_type, e.payload);
  let confLine = null;
  if (e.confidence != null && Number.isFinite(Number(e.confidence))) {
    const conf = confidencePlain(e.confidence);
    confLine = `How sure: ${conf.label} (${conf.pct}%)`;
  }

  return {
    icon: escalated ? AlertCircle : rejected || failed ? XCircle : good ? CheckCircle2 : Bot,
    color: escalated ? "amber" : rejected || failed ? "red" : good ? "emerald" : "slate",
    title,
    summary: payloadSummary || status?.blurb || null,
    variant: status?.variant || (escalated ? "WARNING" : rejected || failed ? "DANGER" : good ? "SUCCESS" : "NEUTRAL"),
    badge: status?.label || null,
    blurb: payloadSummary ? status?.blurb : null,
    body: null,
    extra: [confLine, e.payload && Object.keys(e.payload).length && !payloadSummary
      ? null // intentionally hide opaque JSON from non-tech users
      : null].filter(Boolean).join(" · ") || (confLine || null),
  };
}

function TimelineEntry({ event }) {
  const [expanded, setExpanded] = useState(false);
  const d = describeEvent(event);
  const Icon = d.icon;
  const colors = DOT_COLORS[d.color] || DOT_COLORS.slate;
  const hasDetail = d.body || d.extra || d.blurb;

  return (
    <div className="flex gap-3 border-b border-line px-4 py-3.5 last:border-0 hover:bg-parchment/60">
      <div className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${colors.bg}`}>
        <Icon size={14} className={colors.text} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-medium text-ink-900">{d.title}</p>
          {d.badge && <Badge variant={d.variant}>{d.badge}</Badge>}
        </div>
        {d.summary && (
          <p className="mt-1 text-sm leading-snug text-ink-600">{d.summary}</p>
        )}
        <p className="mt-1 text-[11px] text-ink-500">{timeLabel(event.timestamp)}</p>
        {hasDetail && (
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="mt-1.5 text-xs font-medium text-ink-500 underline decoration-line underline-offset-2 hover:text-ink-900"
          >
            {expanded ? "Hide more" : "More about this"}
          </button>
        )}
        {expanded && (
          <div className="mt-2 rounded-md border border-line bg-parchment p-2.5 text-xs leading-relaxed text-ink-700">
            {d.blurb && <p className="mb-1.5 text-ink-600">{d.blurb}</p>}
            {d.body && <p className="whitespace-pre-wrap break-words">{d.body}</p>}
            {d.extra && <p className={`${d.body || d.blurb ? "mt-1.5" : ""} text-ink-500`}>{d.extra}</p>}
          </div>
        )}
      </div>
    </div>
  );
}

function Timeline({ events }) {
  // Newest first, grouped by calendar day -- 289 real events on one lead is normal for
  // this app after a few days of live testing; a flat oldest-first list would put the
  // most relevant (most recent) activity at the bottom, off-screen.
  const groups = useMemo(() => {
    const sorted = [...events].sort((a, b) => b.timestamp.localeCompare(a.timestamp));
    const byDay = [];
    let current = null;
    for (const e of sorted) {
      const day = e.timestamp.slice(0, 10);
      if (!current || current.day !== day) {
        current = { day, events: [] };
        byDay.push(current);
      }
      current.events.push(e);
    }
    return byDay;
  }, [events]);

  return (
    <div className="max-h-[560px] overflow-y-auto">
      {groups.map((g) => (
        <div key={g.day}>
          <div className="sticky top-0 z-10 border-b border-line bg-parchment-raised-2/95 px-4 py-1.5 text-xs font-semibold text-ink-500 backdrop-blur">
            {dayLabel(g.day)}
          </div>
          {g.events.map((e, i) => (
            <TimelineEntry key={`${g.day}-${i}`} event={e} />
          ))}
        </div>
      ))}
    </div>
  );
}

function intentVariant(intent) {
  if (intent === "STOP") return "DANGER";
  if (["INTERESTED", "DEMO_REQUESTED"].includes(intent)) return "SUCCESS";
  return "NEUTRAL";
}

function MessageBubble({ event }) {
  const outbound = event.type === "OUTREACH_SENT";
  return (
    <div className={`flex ${outbound ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[78%] rounded-lg px-3 py-2 text-sm shadow-sm ${
          outbound ? "bg-ink-900 text-parchment-raised" : "bg-parchment-raised text-ink-700 ring-1 ring-line"
        }`}
      >
        <div className="mb-1 flex items-center gap-2">
          <span className={`text-[11px] font-semibold ${outbound ? "text-parchment-raised/70" : "text-ink-500"}`}>
            {outbound ? "AI-BOS" : "Lead"}
          </span>
          {!outbound && event.intent_detected && (
            <Badge variant={intentVariant(event.intent_detected)}>{event.intent_detected}</Badge>
          )}
          {outbound && event.delivery_state === "Failed" && (
            <Badge variant="DANGER">Failed</Badge>
          )}
        </div>
        {outbound && event.subject && (
          <p className={`mb-1 text-xs font-semibold ${outbound ? "text-parchment-raised/80" : "text-ink-500"}`}>
            {event.subject}
          </p>
        )}
        <p className="whitespace-pre-wrap break-words leading-relaxed">{outbound ? event.body : event.message}</p>
        <p className={`mt-1.5 flex items-center gap-1 font-mono text-[10px] ${outbound ? "text-parchment-raised/50" : "text-ink-500"}`}>
          {dayLabel(event.timestamp.slice(0, 10))} · {timeLabel(event.timestamp)}
          {outbound && <DeliveryTick state={event.delivery_state} />}
        </p>
      </div>
    </div>
  );
}

const CONVERSATION_CHANNELS = [
  { key: "EMAIL", label: "Email", icon: Mail },
  { key: "WHATSAPP", label: "WhatsApp", icon: MessageCircle },
];

// Phase 14 Step 14.3 -- a human label for one channel's follow-up sequence stage.
// terminal_reason values come straight from services/sequence_service.py /
// interest_service.py -- kept in sync with that real, closed set, not guessed.
const TERMINAL_REASON_LABELS = {
  REPLIED: "lead replied",
  SUPPRESSED: "suppressed",
  MAX_STEPS_REACHED: "sequence complete",
  ESCALATED: "escalated to hot lead",
  DECLINED: "declined (said No)",
};

function sequenceStageLabel(seq) {
  if (!seq) return null;
  if (seq.status === "ACTIVE") {
    return seq.followup_level
      ? `Follow-up ${seq.followup_level} of ${seq.max_followup_level} sent`
      : "Follow-ups pending";
  }
  const reason = TERMINAL_REASON_LABELS[seq.terminal_reason] || seq.terminal_reason || seq.status;
  return `Follow-ups stopped — ${reason}`;
}

function SequenceStageBadge({ seq }) {
  const label = sequenceStageLabel(seq);
  if (!label) return null;
  return (
    <span className="text-[11px] font-medium text-ink-500">
      {label}
    </span>
  );
}

function ConversationPanel({ events, sequences }) {
  const byChannel = useMemo(() => {
    const grouped = { EMAIL: [], WHATSAPP: [] };
    for (const e of events) {
      if ((e.type === "OUTREACH_SENT" || e.type === "REPLY_RECEIVED") && grouped[e.channel]) {
        grouped[e.channel].push(e);
      }
    }
    for (const key of Object.keys(grouped)) {
      grouped[key].sort((a, b) => a.timestamp.localeCompare(b.timestamp));
    }
    return grouped;
  }, [events]);

  const [tab, setTab] = useState(byChannel.EMAIL.length > 0 ? "EMAIL" : "WHATSAPP");
  const messages = byChannel[tab];
  const scrollRef = useRef(null);
  const activeSeq = (sequences || []).find((s) => s.channel === tab);

  // Open scrolled to the MOST RECENT message, like every real chat app does -- the list
  // is oldest-first (a conversation reads top-to-bottom as a story), but a long real
  // history can start with several outbound-only messages before the first reply ever
  // came in (real example: this exact lead's early history has back-to-back AI-BOS sends
  // from the Step 4.4 duplicate-send bug, before any reply existed yet) -- opening at the
  // top made it look like only one side was talking. Re-run on every tab/message-count
  // change, not just mount.
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [tab, messages.length]);

  return (
    <div>
      <div className="mb-3 flex items-center justify-between border-b border-line">
        <div className="flex gap-1">
          {CONVERSATION_CHANNELS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-medium transition-colors ${
                tab === key
                  ? "border-ink-900 text-ink-900"
                  : "border-transparent text-ink-500 hover:text-ink-700"
              }`}
            >
              <Icon size={13} /> {label} <span className="text-ink-500">({byChannel[key].length})</span>
            </button>
          ))}
        </div>
        <SequenceStageBadge seq={activeSeq} />
      </div>

      {messages.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-8 text-center">
          <MessagesSquare className="text-ink-500" size={28} />
          <p className="text-xs text-ink-500">No {tab === "EMAIL" ? "email" : "WhatsApp"} messages yet.</p>
        </div>
      ) : (
        <div ref={scrollRef} className="flex max-h-[480px] flex-col gap-3 overflow-y-auto rounded-md bg-parchment p-3">
          {messages.map((m, i) => (
            <MessageBubble key={i} event={m} />
          ))}
        </div>
      )}
    </div>
  );
}

function ScoreCard({ score }) {
  if (!score) {
    return (
      <div className="flex flex-col items-center gap-2 py-6 text-center">
        <Gauge className="text-ink-500" size={28} />
        <p className="text-sm font-medium text-ink-700">Not scored yet</p>
        <p className="max-w-xs text-xs leading-relaxed text-ink-500">
          Once scoring runs, you will see how strong this lead looks and why — in plain language.
        </p>
      </div>
    );
  }

  const tierKey = score.tier in TIER_PLAIN ? score.tier : "COLD";
  const tierCopy = TIER_PLAIN[tierKey];
  const conf = confidencePlain(score.confidence);
  const points = Math.max(0, Math.min(100, Number(score.score) || 0));
  const breakdown = score.scoring_breakdown || {};

  const knownKeys = new Set(SCORE_FACTORS.map((f) => f.key));
  const extraKeys = Object.keys(breakdown).filter((k) => !knownKeys.has(k));
  const factors = [
    ...SCORE_FACTORS.map((meta) => ({
      ...meta,
      raw: breakdown[meta.key],
      present: meta.key in breakdown,
    })),
    ...extraKeys.map((key) => ({
      key,
      label: key.replace(/_/g, " "),
      hint: null,
      raw: breakdown[key],
      present: true,
    })),
  ].filter((f) => f.present);

  return (
    <div className="flex flex-col gap-5">
      {/* Overall read — what a non-tech user should grasp first */}
      <div className="rounded-md border border-line bg-parchment p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={TIER_VARIANT[score.tier] || "NEUTRAL"}>{score.tier}</Badge>
              <span className="font-display text-base font-semibold text-ink-900">{tierCopy.title}</span>
            </div>
            <p className="mt-1.5 text-sm leading-relaxed text-ink-600">{tierCopy.blurb}</p>
          </div>
          <div className="shrink-0 text-right">
            <p className="font-display text-3xl font-semibold tabular-nums leading-none text-ink-900">
              {points}
              <span className="ml-1 text-sm font-normal text-ink-500">/ 100</span>
            </p>
            <p className="mt-1 text-[11px] uppercase tracking-wide text-ink-500">Overall score</p>
          </div>
        </div>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-parchment-raised-2">
          <div
            className={`h-full rounded-full transition-all ${barColor(points / 100)}`}
            style={{ width: `${points}%` }}
          />
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
          <span className={`rounded-md px-2 py-0.5 font-medium ${
            conf.pct >= 70 ? "bg-good-100 text-good-800"
              : conf.pct >= 40 ? "bg-warm-100 text-warm-800"
                : "bg-parchment-raised-2 text-ink-600"
          }`}>
            How sure: {conf.label}
          </span>
          <span className="text-ink-500">{conf.detail}</span>
        </div>
      </div>

      {score.justification && (
        <div>
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-ink-500">
            Why this score
          </p>
          <p className="text-sm leading-relaxed text-ink-700">{score.justification}</p>
        </div>
      )}

      {factors.length > 0 && (
        <div>
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-ink-500">
            What we checked
          </p>
          <div className="flex flex-col gap-3">
            {factors.map((f) => {
              const normalized = normalizeScoreFactor(f.raw);
              const pct = Math.round(normalized * 100);
              const strength = factorStrength(normalized);
              return (
                <div key={f.key} className="flex flex-col gap-1.5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-ink-800">{f.label}</p>
                      {f.hint && (
                        <p className="text-[11px] leading-snug text-ink-500">{f.hint}</p>
                      )}
                    </div>
                    <span className={`shrink-0 rounded-md px-2 py-0.5 text-[11px] font-semibold ${strength.tone}`}>
                      {strength.label}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-parchment-raised-2">
                      <div
                        className={`h-full rounded-full transition-all ${barColor(normalized)}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="w-9 shrink-0 text-right text-[11px] tabular-nums text-ink-500">
                      {pct}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// Grouped for non-tech scanning: who → how to reach → online → where.
// Flat "Not set" lists hide what matters (can we contact them?) under empty social rows.
const CONTACT_FIELD_GROUPS = [
  {
    id: "who",
    title: "Who they are",
    fields: [
      ["company_name", "Company", Building2, "Business or shop name"],
      ["contact_person_name", "Contact person", UserIcon, "Person you would talk to"],
      ["contact_person_role", "Their role", UserIcon, "Owner, manager, etc."],
    ],
  },
  {
    id: "reach",
    title: "How to reach them",
    fields: [
      ["primary_email", "Email", Mail, "name@company.com"],
      ["primary_phone", "Phone", Phone, "+91 …"],
      ["whatsapp_number", "WhatsApp", MessageCircle, "Leave blank to use phone"],
    ],
  },
  {
    id: "online",
    title: "Online presence",
    fields: [
      ["website_url", "Website", Globe, "https://…"],
      ["instagram_url", "Instagram", InstagramIcon, "Profile link"],
      ["facebook_url", "Facebook", FacebookIcon, "Page link"],
      ["linkedin_url", "LinkedIn", LinkedinIcon, "Profile or company page"],
    ],
  },
  {
    id: "where",
    title: "Location",
    fields: [
      ["region_location", "Address / area", MapPin, "City, area, or full address"],
    ],
  },
];

const EDITABLE_FIELDS = CONTACT_FIELD_GROUPS.flatMap((g) =>
  g.fields.map(([key, label, Icon, placeholder]) => [key, label, Icon, placeholder])
);

function shortUrlLabel(url) {
  try {
    const u = new URL(url.startsWith("http") ? url : `https://${url}`);
    const path = u.pathname === "/" ? "" : u.pathname.replace(/\/$/, "");
    const host = u.hostname.replace(/^www\./, "");
    const full = `${host}${path}`;
    return full.length > 42 ? `${full.slice(0, 40)}…` : full;
  } catch {
    return url.length > 42 ? `${url.slice(0, 40)}…` : url;
  }
}

function contactHref(key, value) {
  if (!value) return null;
  if (key === "primary_email") return `mailto:${value}`;
  if (key === "primary_phone") {
    const digits = value.replace(/[^\d+]/g, "");
    return digits ? `tel:${digits}` : null;
  }
  if (key === "whatsapp_number") {
    const digits = value.replace(/\D/g, "");
    return digits ? `https://wa.me/${digits}` : null;
  }
  if (key === "website_url" || key === "instagram_url" || key === "facebook_url" || key === "linkedin_url") {
    return value.startsWith("http") ? value : `https://${value}`;
  }
  return null;
}

function ContactValue({ fieldKey, value, emptyHint }) {
  if (!value) {
    return <span className="text-sm text-ink-500">{emptyHint || "Not added yet"}</span>;
  }
  const href = contactHref(fieldKey, value);
  const isLink = Boolean(href);
  const label =
    fieldKey.endsWith("_url") || fieldKey === "website_url" ? shortUrlLabel(value) : value;

  if (!isLink) {
    return <span className="text-sm break-words text-ink-800">{label}</span>;
  }
  return (
    <a
      href={href}
      target={href.startsWith("http") ? "_blank" : undefined}
      rel={href.startsWith("http") ? "noopener noreferrer" : undefined}
      className="text-sm break-all font-medium text-ink-800 underline decoration-line underline-offset-2 hover:text-ink-900"
    >
      {label}
    </a>
  );
}

function ContactInfoForm({ lead, onSaved, onCancel }) {
  const [form, setForm] = useState(() =>
    Object.fromEntries(EDITABLE_FIELDS.map(([key]) => [key, lead[key] || ""]))
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const dirty = EDITABLE_FIELDS.some(([key]) => (form[key] || "") !== (lead[key] || ""));

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateLead(lead.id, form);
      onSaved(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      {CONTACT_FIELD_GROUPS.map((group) => (
        <div key={group.id}>
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-ink-500">
            {group.title}
          </p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {group.fields.map(([key, label, Icon, placeholder]) => (
              <label
                key={key}
                className={`flex flex-col gap-1 ${group.id === "where" ? "sm:col-span-2" : ""}`}
              >
                <span className="flex items-center gap-1 text-xs font-medium text-ink-600">
                  <Icon size={12} className="text-ink-500" /> {label}
                </span>
                <input
                  value={form[key]}
                  placeholder={placeholder}
                  onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                  className="rounded-md border border-line bg-parchment-raised px-2.5 py-1.5 text-sm text-ink-900 placeholder:text-ink-500 focus:border-gold-500 focus:outline-none"
                />
              </label>
            ))}
          </div>
        </div>
      ))}
      <div className="flex flex-wrap items-center gap-2 border-t border-line pt-3">
        <button
          onClick={save}
          disabled={!dirty || saving}
          className="rounded-md bg-ink-900 px-3 py-1.5 text-xs font-medium text-parchment-raised transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {saving ? "Saving…" : "Save changes"}
        </button>
        <button
          onClick={onCancel}
          className="rounded-md px-3 py-1.5 text-xs font-medium text-ink-500 transition-colors hover:bg-parchment-raised-2"
        >
          Cancel
        </button>
        {error && <span className="text-xs text-alert-600">{error}</span>}
      </div>
    </div>
  );
}

function ContactInfoDisplay({ lead, onEdit }) {
  const filledCount = EDITABLE_FIELDS.filter(([key]) => Boolean(lead[key])).length;
  const totalCount = EDITABLE_FIELDS.length;
  const hasEmail = Boolean(lead.primary_email);
  const hasPhone = Boolean(lead.primary_phone);
  const hasWhatsApp = Boolean(lead.whatsapp_number || lead.primary_phone);
  const hasPerson = Boolean(lead.contact_person_name);
  const reachReady = hasEmail || hasPhone;

  const onlineFields = CONTACT_FIELD_GROUPS.find((g) => g.id === "online").fields;
  const onlineFilled = onlineFields.filter(([key]) => Boolean(lead[key]));
  const onlineMissing = onlineFields.filter(([key]) => !lead[key]).map(([, label]) => label);

  return (
    <div className="flex flex-col gap-4">
      {/* Snapshot — what a non-tech user should grasp first */}
      <div className="rounded-md border border-line bg-parchment p-4">
        <p className="font-display text-base font-semibold text-ink-900">
          {lead.company_name || "Unnamed company"}
        </p>
        <p className="mt-1 text-sm text-ink-600">
          {hasPerson
            ? `${lead.contact_person_name}${lead.contact_person_role ? ` · ${lead.contact_person_role}` : ""}`
            : "No contact person named yet — add a name so outreach feels personal."}
        </p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${
            reachReady ? "bg-good-100 text-good-800" : "bg-alert-100 text-alert-700"
          }`}>
            {reachReady ? "Can contact" : "No way to contact yet"}
          </span>
          {hasEmail && (
            <span className="rounded-md bg-parchment-raised-2 px-2 py-0.5 text-[11px] font-medium text-ink-600">
              Email ready
            </span>
          )}
          {hasPhone && (
            <span className="rounded-md bg-parchment-raised-2 px-2 py-0.5 text-[11px] font-medium text-ink-600">
              Phone ready
            </span>
          )}
          {hasWhatsApp && (
            <span className="rounded-md bg-parchment-raised-2 px-2 py-0.5 text-[11px] font-medium text-ink-600">
              WhatsApp possible
            </span>
          )}
          {!hasPerson && (
            <span className="rounded-md bg-warm-100 px-2 py-0.5 text-[11px] font-medium text-warm-800">
              Missing name
            </span>
          )}
        </div>
        <p className="mt-2 text-[11px] text-ink-500">
          {filledCount} of {totalCount} details filled
        </p>
      </div>

      {/* Who */}
      <div>
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-ink-500">
          Who they are
        </p>
        <div className="flex flex-col gap-2.5">
          {CONTACT_FIELD_GROUPS.find((g) => g.id === "who").fields.map(([key, label, Icon]) => (
            <div key={key} className="flex items-start gap-2.5">
              <Icon size={14} className="mt-0.5 shrink-0 text-ink-500" />
              <div className="min-w-0 flex-1">
                <p className="text-[11px] text-ink-500">{label}</p>
                <ContactValue
                  fieldKey={key}
                  value={lead[key]}
                  emptyHint={key === "contact_person_name" ? "Add a name" : "Not added yet"}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Reach — always show all three; empty ones are the actionable gaps */}
      <div>
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-ink-500">
          How to reach them
        </p>
        <div className="flex flex-col gap-2.5">
          {CONTACT_FIELD_GROUPS.find((g) => g.id === "reach").fields.map(([key, label, Icon]) => {
            const value = lead[key];
            const waFallback = key === "whatsapp_number" && !value && lead.primary_phone;
            return (
              <div key={key} className="flex items-start gap-2.5">
                <Icon size={14} className="mt-0.5 shrink-0 text-ink-500" />
                <div className="min-w-0 flex-1">
                  <p className="text-[11px] text-ink-500">{label}</p>
                  {waFallback ? (
                    <p className="text-sm text-ink-600">
                      Uses phone ({lead.primary_phone}) unless you set a separate number
                    </p>
                  ) : (
                    <ContactValue
                      fieldKey={key}
                      value={value}
                      emptyHint={key === "primary_email" ? "Add an email" : key === "primary_phone" ? "Add a phone" : "Not added yet"}
                    />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Online — filled links first; missing collapsed into one line (no 4× "Not set") */}
      <div>
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-ink-500">
          Online presence
        </p>
        {onlineFilled.length === 0 ? (
          <p className="text-sm text-ink-500">
            No website or social links yet. Add them if you find a page while researching.
          </p>
        ) : (
          <div className="flex flex-col gap-2.5">
            {onlineFilled.map(([key, label, Icon]) => (
              <div key={key} className="flex items-start gap-2.5">
                <Icon size={14} className="mt-0.5 shrink-0 text-ink-500" />
                <div className="min-w-0 flex-1">
                  <p className="text-[11px] text-ink-500">{label}</p>
                  <ContactValue fieldKey={key} value={lead[key]} />
                </div>
              </div>
            ))}
            {onlineMissing.length > 0 && (
              <p className="text-[11px] text-ink-500">
                Not added: {onlineMissing.join(", ")}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Location */}
      <div>
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-ink-500">
          Location
        </p>
        <div className="flex items-start gap-2.5">
          <MapPin size={14} className="mt-0.5 shrink-0 text-ink-500" />
          <div className="min-w-0 flex-1">
            <p className="text-[11px] text-ink-500">Address / area</p>
            <ContactValue
              fieldKey="region_location"
              value={lead.region_location}
              emptyHint="No address or area on file"
            />
          </div>
        </div>
      </div>

      <button
        onClick={onEdit}
        className="w-fit rounded-md border border-line px-3 py-1.5 text-xs font-medium text-ink-700 transition-colors hover:bg-parchment"
      >
        Edit details
      </button>
    </div>
  );
}

function ContactSection({ lead, onSaved }) {
  const [editing, setEditing] = useState(false);
  if (!editing) {
    return <ContactInfoDisplay lead={lead} onEdit={() => setEditing(true)} />;
  }
  return (
    <ContactInfoForm
      lead={lead}
      onSaved={(updated) => { onSaved(updated); setEditing(false); }}
      onCancel={() => setEditing(false)}
    />
  );
}

function SectionCard({ title, icon: Icon, children, headerExtra }) {
  return (
    <div className="rounded-lg border border-line bg-parchment-raised shadow-sm">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <h2 className="flex items-center gap-2 font-display text-sm font-semibold text-ink-700">
          <Icon size={15} className="text-ink-500" /> {title}
        </h2>
        {headerExtra}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

// Phase 10 Step 10.3 -- AI drafts, a human sends manually from their own real account
// and marks it sent here. Deliberately no "send" action anywhere in this codebase --
// LinkedIn has no official cold-messaging API, and Instagram/Facebook's official APIs
// only permit messaging someone who has already messaged us first.
const SOCIAL_PLATFORMS = [
  { key: "LINKEDIN", urlField: "linkedin_url", label: "LinkedIn", Icon: LinkedinIcon },
  { key: "INSTAGRAM", urlField: "instagram_url", label: "Instagram", Icon: InstagramIcon },
  { key: "FACEBOOK", urlField: "facebook_url", label: "Facebook", Icon: FacebookIcon },
];

function SocialPlatformRow({ platform, profileUrl, leadId, queueItem, onRefresh }) {
  const [drafting, setDrafting] = useState(false);
  const [acting, setActing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);

  async function requestDraft() {
    setDrafting(true);
    setError(null);
    try {
      await api.draftSocialMessage(leadId, platform.key);
      onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setDrafting(false);
    }
  }

  async function copyText() {
    try {
      await navigator.clipboard.writeText(queueItem.message_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard permission denied -- the text is still visible to select manually */
    }
  }

  async function markSent() {
    setActing(true);
    try {
      await api.markSocialSent(queueItem.id);
      onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setActing(false);
    }
  }

  async function dismissDraft() {
    setActing(true);
    try {
      await api.dismissSocialDraft(queueItem.id);
      onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setActing(false);
    }
  }

  const Icon = platform.Icon;

  return (
    <div className="rounded-md border border-line p-3">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-medium text-ink-700">
          <Icon size={14} className="text-ink-500" /> {platform.label}
        </div>
        <a href={profileUrl} target="_blank" rel="noopener noreferrer"
           className="text-xs text-ink-500 hover:text-gold-700 hover:underline">
          Open profile
        </a>
      </div>

      {!queueItem && (
        <button
          onClick={requestDraft}
          disabled={drafting}
          className="mt-2 rounded-md border border-line px-2.5 py-1.5 text-xs font-medium text-ink-700 transition-colors hover:bg-parchment disabled:cursor-not-allowed disabled:opacity-40"
        >
          {drafting ? "Drafting…" : `Draft ${platform.label} message`}
        </button>
      )}

      {queueItem && queueItem.status === "QUEUED" && (
        <div className="mt-2 flex flex-col gap-2">
          <p className="whitespace-pre-wrap rounded-md bg-parchment p-2.5 text-xs text-ink-700">
            {queueItem.message_text}
          </p>
          {queueItem.reasoning && (
            <p className="text-[11px] italic text-ink-500">Why: {queueItem.reasoning}</p>
          )}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={copyText}
              className="flex items-center gap-1 rounded-md border border-line px-2.5 py-1.5 text-xs font-medium text-ink-700 transition-colors hover:bg-parchment"
            >
              <Copy size={12} /> {copied ? "Copied" : "Copy text"}
            </button>
            <button
              onClick={markSent}
              disabled={acting}
              title="Confirm you sent this manually from your own account"
              className="flex items-center gap-1 rounded-md bg-ink-900 px-2.5 py-1.5 text-xs font-medium text-parchment-raised transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Send size={12} /> Mark as Sent
            </button>
            <button
              onClick={dismissDraft}
              disabled={acting}
              className="flex items-center gap-1 rounded-md px-2.5 py-1.5 text-xs font-medium text-ink-500 transition-colors hover:bg-parchment hover:text-ink-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <X size={12} /> Dismiss
            </button>
          </div>
        </div>
      )}

      {queueItem && queueItem.status === "SENT" && (
        <div className="mt-2 flex items-center justify-between gap-2">
          <span className="font-mono text-xs text-good-600">Sent {relativeTime(queueItem.sent_at)}</span>
          <button
            onClick={requestDraft}
            disabled={drafting}
            className="text-xs font-medium text-ink-500 hover:text-ink-900 disabled:opacity-40"
          >
            {drafting ? "Drafting…" : "Draft another"}
          </button>
        </div>
      )}

      {queueItem && queueItem.status === "DISMISSED" && (
        <div className="mt-2">
          <button
            onClick={requestDraft}
            disabled={drafting}
            className="text-xs font-medium text-ink-500 hover:text-ink-900 disabled:opacity-40"
          >
            {drafting ? "Drafting…" : "Draft another"}
          </button>
        </div>
      )}

      {error && <p className="mt-2 text-xs text-alert-600">{error}</p>}
    </div>
  );
}

function SocialOutreachCard({ lead, queue, onRefresh }) {
  const platforms = SOCIAL_PLATFORMS.filter((p) => lead[p.urlField]);
  if (platforms.length === 0) {
    return (
      <p className="text-xs text-ink-500">
        No LinkedIn, Instagram, or Facebook profile on file for this lead -- add one under
        "Contact & profile" to enable drafting.
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-2.5">
      {platforms.map((p) => {
        const latest = queue
          .filter((q) => q.platform === p.key)
          .sort((a, b) => b.created_at.localeCompare(a.created_at))[0];
        return (
          <SocialPlatformRow
            key={p.key}
            platform={p}
            profileUrl={lead[p.urlField]}
            leadId={lead.id}
            queueItem={latest}
            onRefresh={onRefresh}
          />
        );
      })}
    </div>
  );
}

// Phase 14 Step 14.4 -- deliberately separate from SocialPlatformRow/SocialOutreachCard
// above: that Step 10.3(a) feature drafts a NEW, bespoke message per platform via a real
// LLM call. This copies the SAME content the lead's real email already sent -- no
// generation, just a re-render of one canonical stored object -- so it stays visually and
// functionally distinct rather than merged into that queue UI.
const CROSS_CHANNEL_PLATFORMS = [
  { key: "EMAIL", label: "Email", icon: Mail },
  { key: "WHATSAPP", label: "WhatsApp", icon: MessageCircle },
  { key: "INSTAGRAM", label: "Instagram", icon: InstagramIcon },
  { key: "FACEBOOK", label: "Facebook", icon: FacebookIcon },
  { key: "LINKEDIN", label: "LinkedIn", icon: LinkedinIcon },
];

function CrossChannelCopyBar({ leadId }) {
  const toast = useToast();
  const [copying, setCopying] = useState(null);

  async function copyFor(platform) {
    setCopying(platform);
    try {
      const res = await api.getCrossChannelCopy(leadId, platform);
      if (res.format === "html") {
        // A real rich-HTML copy (pastes formatted into Gmail/Outlook compose etc.), with
        // a plain-text fallback in the SAME clipboard write -- some targets only read the
        // text/plain entry, and this must still be readable there.
        try {
          await navigator.clipboard.write([
            new ClipboardItem({
              "text/html": new Blob([res.content], { type: "text/html" }),
              "text/plain": new Blob([res.content.replace(/<[^>]+>/g, " ")], { type: "text/plain" }),
            }),
          ]);
        } catch {
          await navigator.clipboard.writeText(res.content); // e.g. Safari/older browsers
        }
      } else {
        await navigator.clipboard.writeText(res.content);
      }
      toast.success(`${platform === "EMAIL" ? "Email" : platform} content copied`);
    } catch (err) {
      if (err.message.startsWith("404")) {
        toast.error("No synced outreach content for this lead yet — send an email first.");
      } else {
        toast.error(err.message.replace(/^\d+\s*/, "").replace(/^\["|"\]$/g, ""));
      }
    } finally {
      setCopying(null);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2 border-t border-line pt-3">
      <span className="text-[11px] text-ink-500">Copy this lead's real outreach content for:</span>
      {CROSS_CHANNEL_PLATFORMS.map(({ key, label, icon: Icon }) => (
        <button
          key={key}
          onClick={() => copyFor(key)}
          disabled={copying === key}
          title={`Copy for ${label}`}
          className="flex items-center gap-1.5 rounded-md border border-line px-2 py-1 text-[11px] font-medium text-ink-700 transition-colors hover:bg-parchment disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Icon size={12} /> {label}
        </button>
      ))}
    </div>
  );
}

// Phase 15 Step 15(A).2 -- a real, non-negotiable rule: a low-confidence guess must
// NEVER render like a verified contact. Two visually distinct tiers, both always
// showing the real number, never a bare "verified" badge with no way to tell the two
// apart at a glance.
function ConfidenceBadge({ confidence }) {
  if (confidence == null) return null;
  const pct = Math.round(confidence * 100);
  const strong = confidence >= 0.7;
  return (
    <span
      title={strong ? "A cleanly matched LinkedIn result" : "A weaker match -- verify before relying on this"}
      className={`inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium ${
        strong ? "bg-good-100 text-good-700" : "bg-warm-100 text-warm-700"
      }`}
    >
      {strong ? <CheckCircle2 size={10} /> : <AlertCircle size={10} />}
      {pct}% {strong ? "likely" : "unverified"}
    </span>
  );
}

function PeopleCard({ contacts }) {
  if (!contacts || contacts.length === 0) {
    return (
      <p className="text-xs text-ink-500">
        No individual contacts found yet at this company (needs the company's own LinkedIn
        page resolved first).
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      {contacts.map((c) => (
        <div key={c.id} className="flex items-start justify-between gap-3 rounded-md bg-parchment p-3 text-xs">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="font-semibold text-ink-700">{c.full_name || "Name not confirmed"}</span>
              {c.is_decision_maker ? (
                <span className="flex items-center gap-0.5 text-warm-600" title="Flagged as a decision maker">
                  <Star size={10} />
                </span>
              ) : null}
              <ConfidenceBadge confidence={c.confidence} />
            </div>
            <p className="mt-0.5 text-ink-500">{c.role}</p>
            <p className="mt-0.5 font-mono text-[10px] text-ink-500">via {c.source}</p>
          </div>
          {c.linkedin_url && (
            <a
              href={c.linkedin_url}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 text-ink-500 hover:text-gold-700"
              title="Open LinkedIn profile"
            >
              <LinkedinIcon size={14} />
            </a>
          )}
        </div>
      ))}
    </div>
  );
}

function relativeTime(dateStr) {
  const then = new Date(dateStr.replace(" ", "T") + "Z").getTime();
  const days = Math.floor((Date.now() - then) / 86400000);
  if (days <= 0) return "today";
  if (days === 1) return "1 day ago";
  return `${days} days ago`;
}

export default function LeadDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const confirm = useConfirm();
  const toast = useToast();
  const [searchParams] = useSearchParams();
  const [lead, setLead] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [adjacent, setAdjacent] = useState(null); // {position, total, prev, next}
  const [socialQueue, setSocialQueue] = useState([]);
  const [error, setError] = useState(null);
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState(null);

  // Whatever list this lead was opened from (Leads page filters, or a Kanban column's
  // status) rides along in the URL's own query string -- carrying it forward lets
  // Prev/Next keep walking through that SAME list instead of resetting to "everything"
  // on every click.
  const filterQs = searchParams.toString();

  function refresh() {
    api.getLead(id).then(setLead).catch((err) => setError(err.message));
    api.getLeadTimeline(id).then(setTimeline).catch((err) => setError(err.message));
    api.getAdjacentLead(id, Object.fromEntries(searchParams)).then(setAdjacent).catch(() => setAdjacent(null));
    api.listSocialQueue({ lead_id: id }).then(setSocialQueue).catch(() => setSocialQueue([]));
  }

  useEffect(refresh, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  function goTo(neighborId) {
    navigate(`/leads/${neighborId}${filterQs ? `?${filterQs}` : ""}`);
  }

  const sendInFlight = sending || lead?.status === "OUTREACHING";
  const [markingContacted, setMarkingContacted] = useState(false);

  // The only way a HOT_LEAD (auto-escalated because the lead replied showing real
  // interest) stops showing as "needs response" on the Dashboard's alerts panel -- there
  // is no separate resolved flag, moving off HOT_LEAD status IS the signal.
  async function markContacted() {
    setMarkingContacted(true);
    try {
      await api.patchLeadStatus(lead.id, "ENGAGED");
      refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setMarkingContacted(false);
    }
  }

  const [closingStatus, setClosingStatus] = useState(false);

  // CRM had no way at all to close the loop on a lead after it went HOT/ENGAGED --
  // CONVERTED and REJECTED are both valid statuses the backend already accepted, there
  // was just no button anywhere that ever set them (found live, user asked directly:
  // "interested aane ke baad crm me aage kya??"). Real business outcomes, so confirm
  // first like every other real/hard-to-undo action in this app.
  async function closeDeal(status) {
    const ok = await confirm({
      title: status === "CONVERTED" ? "Mark as converted?" : "Mark as lost?",
      message: status === "CONVERTED"
        ? `Mark ${lead.company_name} as a won deal? This is a real business outcome, not a simulation.`
        : `Mark ${lead.company_name} as lost? This closes the lead out of the active pipeline.`,
      confirmLabel: status === "CONVERTED" ? "Mark converted" : "Mark lost",
      danger: status !== "CONVERTED",
    });
    if (!ok) return;
    setClosingStatus(true);
    try {
      await api.patchLeadStatus(lead.id, status);
      refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setClosingStatus(false);
    }
  }

  async function sendOutreach() {
    // force: true by default -- a human already deliberately clicking "send" on this one
    // specific lead's own page IS the judgment call; making them click again past a
    // rejection to override the AI's tier/confidence read was friction with no real safety
    // value here (unlike the autonomous scheduler tick, which force never reaches). What
    // still applies unconditionally, force or not: a real contact channel must exist, and
    // QC + suppression still run exactly as for any other send -- see lead_service.py.
    const ok = await confirm({
      title: "Send real outreach?",
      message: `Send REAL outreach to ${lead.company_name} now (${lead.primary_email || "no email"} / ` +
        `${lead.primary_phone || "no phone"})? This is a real send, not a simulation -- sent ` +
        `regardless of the AI's own tier/confidence read, though QC review and suppression checks ` +
        `still apply.`,
      confirmLabel: "Send now",
    });
    if (!ok) return;
    setSending(true);
    setSendResult(null);
    try {
      const res = await api.triggerOutreach(lead.id, { force: true });
      setSendResult(res.results);
      refresh();
    } catch (err) {
      toast.error(err.message.replace(/^\d+\s*/, "").replace(/^\["|"\]$/g, ""), { duration: 6000 });
    } finally {
      setSending(false);
    }
  }

  if (error) return <div className="mx-auto max-w-7xl px-6 py-6 text-sm text-alert-600">{error}</div>;
  if (!lead) return <div className="mx-auto max-w-7xl px-6 py-10 text-center text-sm text-ink-500">Loading…</div>;

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-5 px-6 py-6">
      <div className="flex items-center justify-between gap-3">
        <Link to="/" className="flex w-fit items-center gap-1 text-xs font-medium text-ink-500 hover:text-ink-900">
          <ArrowLeft size={13} /> Back to dashboard
        </Link>

        {adjacent && (
          <div className="flex items-center gap-2">
            {adjacent.total > 0 && (
              <span className="font-mono text-xs text-ink-500">Lead {adjacent.position} of {adjacent.total}</span>
            )}
            <button
              onClick={() => goTo(adjacent.prev.id)}
              disabled={!adjacent.prev}
              title={adjacent.prev ? adjacent.prev.company_name : undefined}
              className="flex items-center gap-1 rounded-md border border-line bg-parchment-raised px-2.5 py-1.5 text-xs font-medium text-ink-700 hover:bg-parchment disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ChevronLeft size={13} /> Previous
            </button>
            <button
              onClick={() => goTo(adjacent.next.id)}
              disabled={!adjacent.next}
              title={adjacent.next ? adjacent.next.company_name : undefined}
              className="flex items-center gap-1 rounded-md border border-line bg-parchment-raised px-2.5 py-1.5 text-xs font-medium text-ink-700 hover:bg-parchment disabled:cursor-not-allowed disabled:opacity-40"
            >
              Next <ChevronRight size={13} />
            </button>
          </div>
        )}
      </div>

      <div className="flex items-start justify-between gap-3 rounded-lg border border-line bg-parchment-raised p-5 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-parchment-raised-2 text-sm font-semibold text-ink-700">
            {lead.company_name.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-display text-lg font-semibold text-ink-900">{lead.company_name}</h1>
              {lead.reference_code && (
                <span
                  title="Reference code -- quote this in alerts/conversation to identify this lead"
                  className="rounded bg-parchment-raised-2 px-1.5 py-0.5 font-mono text-[11px] text-ink-500"
                >
                  {lead.reference_code}
                </span>
              )}
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-500">
              {lead.region_location && (
                <span className="flex items-center gap-1"><MapPin size={12} /> {lead.region_location}</span>
              )}
              {lead.primary_email && (
                <a href={`mailto:${lead.primary_email}`} className="flex items-center gap-1 hover:text-gold-700 hover:underline">
                  <Mail size={12} /> {lead.primary_email}
                </a>
              )}
              {lead.primary_phone && (
                <a href={`tel:${lead.primary_phone}`} className="flex items-center gap-1 hover:text-gold-700 hover:underline">
                  <Phone size={12} /> {lead.primary_phone}
                </a>
              )}
              {lead.instagram_url && (
                <a href={lead.instagram_url} target="_blank" rel="noopener noreferrer"
                   title="Instagram" className="flex items-center text-ink-500 hover:text-gold-700">
                  <InstagramIcon size={13} />
                </a>
              )}
              {lead.facebook_url && (
                <a href={lead.facebook_url} target="_blank" rel="noopener noreferrer"
                   title="Facebook" className="flex items-center text-ink-500 hover:text-gold-700">
                  <FacebookIcon size={13} />
                </a>
              )}
              {lead.linkedin_url && (
                <a href={lead.linkedin_url} target="_blank" rel="noopener noreferrer"
                   title="LinkedIn" className="flex items-center text-ink-500 hover:text-gold-700">
                  <LinkedinIcon size={13} />
                </a>
              )}
              <span className="text-ink-500">·</span>
              <span className="font-mono">Added {relativeTime(lead.created_at)}</span>
            </div>
          </div>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-2">
          <div className="flex items-center gap-2">
            {lead.interest_state === "YES" && (
              <span
                title={`Clicked "Yes, tell me more" on a real outreach send${lead.interest_state_at ? ` (${relativeTime(lead.interest_state_at)})` : ""}`}
                className="inline-flex shrink-0 items-center gap-1 rounded-full bg-good-100 px-2 py-0.5 text-[11px] font-semibold text-good-700 ring-1 ring-inset ring-good-600/30"
              >
                <CheckCircle2 size={11} /> Said Yes
              </span>
            )}
            {lead.interest_state === "NO" && (
              <span
                title={`Clicked "Not right now" -- declined this pitch, still contactable (NOT unsubscribed)${lead.interest_state_at ? ` (${relativeTime(lead.interest_state_at)})` : ""}`}
                className="inline-flex shrink-0 items-center gap-1 rounded-full bg-gold-100 px-2 py-0.5 text-[11px] font-semibold text-gold-700 ring-1 ring-inset ring-gold-600/30"
              >
                <XCircle size={11} /> Said No
              </span>
            )}
            {lead.is_suppressed && (
              <span
                title="This lead's email/phone is in the suppression list -- no future outreach will be sent"
                className="inline-flex shrink-0 items-center gap-1 rounded-full bg-parchment-raised-2 px-2 py-0.5 text-[11px] font-semibold text-ink-500 ring-1 ring-inset ring-line"
              >
                <BellOff size={11} /> Opted out
              </span>
            )}
            {lead.score && <Badge variant={TIER_VARIANT[lead.score.tier] || "NEUTRAL"}>{lead.score.tier}</Badge>}
            <span className={`inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-[11px] font-semibold ${statusBadgeClass(lead.status)}`}>
              {lead.status.replace(/_/g, " ")}
            </span>
          </div>
          {lead.status === "HOT_LEAD" && (
            <button
              onClick={markContacted}
              disabled={markingContacted}
              title="Moves this lead to Engaged and clears it off the Dashboard's alerts"
              className="rounded-md bg-alert-600 px-3 py-1.5 text-xs font-medium text-parchment-raised transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {markingContacted ? "Marking…" : "Mark as Contacted"}
            </button>
          )}
          {lead.score && (lead.primary_email || lead.primary_phone) && !lead.is_suppressed && (
            <button
              onClick={() => sendOutreach()}
              disabled={sendInFlight}
              className="rounded-md bg-ink-900 px-3 py-1.5 text-xs font-medium text-parchment-raised transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {sendInFlight ? "Sending…" : "Send Outreach Now"}
            </button>
          )}
          {/* Closing the loop -- CRM had no way at all to record a real business
             outcome (deal won/lost) before this; both statuses already existed on the
             backend, just no button anywhere ever set them. */}
          {!["CONVERTED", "REJECTED"].includes(lead.status) && (
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => closeDeal("CONVERTED")}
                disabled={closingStatus}
                title="Mark as a won deal"
                className="flex items-center gap-1 rounded-md bg-good-100 px-2.5 py-1.5 text-xs font-medium text-good-700 ring-1 ring-inset ring-good-600/30 transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Trophy size={12} /> Mark Converted
              </button>
              <button
                onClick={() => closeDeal("REJECTED")}
                disabled={closingStatus}
                title="Mark as a lost deal"
                className="flex items-center gap-1 rounded-md bg-parchment-raised px-2.5 py-1.5 text-xs font-medium text-ink-500 ring-1 ring-inset ring-line transition-colors hover:bg-parchment disabled:cursor-not-allowed disabled:opacity-40"
              >
                <ThumbsDown size={12} /> Mark Lost
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Failure now goes to a toast (see sendOutreach's catch block) -- a permanent inline
         banner here used to sit on the page forever with no way to act on it; the toast
         version can also offer a real next step (Force send anyway). */}
      {sendResult && (
        <div className="-mt-3 flex flex-wrap gap-3 rounded-lg border border-line bg-parchment-raised px-4 py-2 text-xs shadow-sm">
          {Object.entries(sendResult).map(([channel, r]) => (
            <span key={channel} className={r.status === "SENT" ? "text-good-600" : "text-warm-600"}>
              {channel}: {r.status === "SENT" ? "Sent ✓" : `Escalated (${r.reason || "needs review"})`}
            </span>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <SectionCard title="Who & how to reach" icon={UserIcon}>
          {/* Real bug, found live: PATCH /leads/<id> only ever returns the bare
             contact/profile fields it actually changed -- never pain_points/
             review_insight/firmographics/score.scoring_breakdown, which only the
             initial GET enriches the response with. Replacing `lead` wholesale with
             that partial response wiped those out and crashed the next render
             (`lead.pain_points.length` on `undefined`). Merge onto the existing lead
             instead -- PATCH's editable fields never overlap with the enrichment-only
             ones anyway, so a merge is strictly correct, not just a workaround. */}
          <ContactSection lead={lead} onSaved={(updated) => setLead((prev) => ({ ...prev, ...updated }))} />
        </SectionCard>
        <SectionCard title="Lead strength" icon={Gauge}>
          <ScoreCard score={lead.score} />
        </SectionCard>
      </div>

      {lead.pain_points.length > 0 && (
        <SectionCard title="Verified pain points" icon={AlertTriangle}>
          <div className="flex flex-col gap-2">
            {lead.pain_points.map((p, i) => (
              <div key={i} className="flex items-start gap-3 rounded-md bg-parchment p-3 text-xs">
                <div className={`mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full ${barColor(p.severity_0_1 || 0)}`} />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-ink-700">{p.code.replace(/_/g, " ")}</span>
                    <span className="font-mono text-ink-500">severity {Math.round((p.severity_0_1 || 0) * 100)}%</span>
                  </div>
                  <p className="mt-1 italic text-ink-700">&ldquo;{p.evidence_quote}&rdquo;</p>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      <SectionCard title="People at this company" icon={Users}>
        <PeopleCard contacts={lead.contacts} />
      </SectionCard>

      <SectionCard title="Social outreach (draft-and-queue)" icon={Share2}>
        <SocialOutreachCard lead={lead} queue={socialQueue} onRefresh={refresh} />
      </SectionCard>

      {/* Side by side on a real desktop width (xl: 1280px+, matches the responsiveness
         floor in CRM_UI_UX_PLAN.md), stacked below that -- both panels are independently
         scrollable, so this is a pure layout choice, not a data dependency between them. */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <SectionCard title="Conversation" icon={MessagesSquare}>
          {!timeline && <p className="text-xs text-ink-500">Loading…</p>}
          {timeline && (
            <div className="flex flex-col gap-3">
              <ConversationPanel events={timeline} sequences={lead?.followup_sequences} />
              <CrossChannelCopyBar leadId={id} />
            </div>
          )}
        </SectionCard>

        <SectionCard
          title="What happened"
          icon={Clock}
          headerExtra={
            <span className="text-xs text-ink-500">
              {timeline
                ? `${timeline.length} update${timeline.length === 1 ? "" : "s"}`
                : ""}
            </span>
          }
        >
          {!timeline && <p className="text-xs text-ink-500">Loading…</p>}
          {timeline && timeline.length === 0 && (
            <div className="flex flex-col items-center gap-2 py-6 text-center">
              <Clock className="text-ink-500" size={28} />
              <p className="text-sm font-medium text-ink-700">No activity yet</p>
              <p className="max-w-xs text-xs leading-relaxed text-ink-500">
                Scoring, review checks, sends, and replies will show up here in plain language.
              </p>
            </div>
          )}
          {timeline && timeline.length > 0 && (
            <div className="-mx-4 -mb-4 rounded-b-lg border-t border-line">
              <Timeline events={timeline} />
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}
