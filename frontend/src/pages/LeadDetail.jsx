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

// Fixed, meaningful order -- Object.entries() on the raw JSON gave alphabetical order
// (Buying Signal, Icp Fit, Pain Match, Reachability), which has no relationship to how a
// rep should actually scan the breakdown. This order matches how scoring_agent.py itself
// reasons about fit: is this the right business, does their pain match what we sell, can
// we reach them, are they showing buying intent.
const SCORE_BREAKDOWN_ORDER = ["icp_fit", "pain_match", "reachability", "buying_signal"];

function barColor(value) {
  if (value >= 0.7) return "bg-emerald-500";
  if (value >= 0.4) return "bg-amber-500";
  return "bg-slate-300";
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
  emerald: { bg: "bg-emerald-100", text: "text-emerald-600" },
  red: { bg: "bg-red-100", text: "text-red-600" },
  amber: { bg: "bg-amber-100", text: "text-amber-600" },
  slate: { bg: "bg-slate-100", text: "text-slate-500" },
};

// Phase 14 Step 14.1 -- a real, honest per-message delivery state (never a guess: "--"
// covers a channel/event this project genuinely has no signal for, matching
// services/outreach/delivery_status.py's own contract). Single check = Sent, double =
// Delivered, blue double = Seen (WhatsApp-style convention users already recognize),
// emerald double = Replied (strongest possible signal), red X = Failed.
function DeliveryTick({ state }) {
  if (state === "Failed") return <XCircle size={12} className="text-red-500" />;
  if (state === "Replied") return <CheckCheck size={12} className="text-emerald-500" />;
  if (state === "Seen") return <CheckCheck size={12} className="text-sky-500" />;
  if (state === "Delivered") return <CheckCheck size={12} className="text-slate-400" />;
  if (state === "Sent") return <Check size={12} className="text-slate-400" />;
  return null;
}

// Server sends raw agent/action_type/outcome/routed_to strings -- this is the one place
// that turns them into an icon + color + human title, so the timeline list itself stays
// simple (CRM_UI_UX_PLAN.md: format decisions live in one place, not scattered in JSX).
function describeEvent(e) {
  if (e.type === "OUTREACH_SENT") {
    const failed = e.delivery_state === "Failed";
    return {
      icon: e.channel === "WHATSAPP" ? MessageCircle : Mail,
      color: failed ? "red" : "emerald",
      title: `${e.channel === "WHATSAPP" ? "WhatsApp" : "Email"} sent${e.subject ? `: ${e.subject}` : ""}`,
      variant: failed ? "DANGER" : "SUCCESS",
      badge: e.delivery_state || e.status,
      body: e.body,
    };
  }
  if (e.type === "REPLY_RECEIVED") {
    const positive = ["INTERESTED", "DEMO_REQUESTED"].includes(e.intent_detected);
    const negative = e.intent_detected === "STOP";
    return {
      icon: e.channel === "WHATSAPP" ? MessageCircle : Mail,
      color: negative ? "red" : positive ? "emerald" : "slate",
      title: `${e.channel === "WHATSAPP" ? "WhatsApp" : "Email"} reply${e.intent_detected ? ` — ${e.intent_detected}` : ""}`,
      variant: negative ? "DANGER" : positive ? "SUCCESS" : "NEUTRAL",
      badge: e.intent_detected || "unclassified",
      body: e.message,
      extra: e.ai_suggested_response ? `AI draft reply: ${e.ai_suggested_response}` : null,
    };
  }
  // AGENT_EVENT
  const escalated = e.routed_to === "HUMAN_ESCALATION";
  const rejected = e.outcome === "REJECTED";
  const good = ["APPROVED", "EXECUTE", "SENT"].includes(e.outcome);
  return {
    icon: escalated ? AlertCircle : rejected ? XCircle : good ? CheckCircle2 : Bot,
    color: escalated ? "amber" : rejected ? "red" : good ? "emerald" : "slate",
    title: `${e.agent} · ${e.action_type.replace(/_/g, " ").toLowerCase()}`,
    variant: escalated ? "WARNING" : rejected ? "DANGER" : good ? "SUCCESS" : "NEUTRAL",
    badge: e.outcome || e.routed_to || "",
    body: e.payload && Object.keys(e.payload).length ? JSON.stringify(e.payload) : null,
    extra: e.confidence != null ? `confidence ${e.confidence.toFixed(2)}` : null,
  };
}

function TimelineEntry({ event }) {
  const [expanded, setExpanded] = useState(false);
  const d = describeEvent(event);
  const Icon = d.icon;
  const colors = DOT_COLORS[d.color] || DOT_COLORS.slate;
  const hasDetail = d.body || d.extra;

  return (
    <div className="flex gap-3 border-b border-slate-100 px-4 py-3 last:border-0 hover:bg-slate-50">
      <div className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full ${colors.bg}`}>
        <Icon size={13} className={colors.text} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-medium capitalize text-slate-900">{d.title}</p>
          {d.badge && <Badge variant={d.variant}>{d.badge}</Badge>}
        </div>
        <p className="mt-0.5 text-[11px] text-slate-400">{timeLabel(event.timestamp)}</p>
        {hasDetail && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="mt-1 text-xs font-medium text-slate-400 hover:text-slate-700"
          >
            {expanded ? "Hide detail" : "Show detail"}
          </button>
        )}
        {expanded && (
          <div className="mt-2 rounded-md bg-slate-50 p-2.5 text-xs text-slate-600">
            {d.body && <p className="whitespace-pre-wrap break-words">{d.body}</p>}
            {d.extra && <p className="mt-1 italic text-slate-500">{d.extra}</p>}
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
          <div className="sticky top-0 z-10 border-b border-slate-100 bg-slate-50/95 px-4 py-1.5 text-xs font-semibold text-slate-500 backdrop-blur">
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
          outbound ? "bg-slate-800 text-white" : "bg-white text-slate-800 ring-1 ring-slate-200"
        }`}
      >
        <div className="mb-1 flex items-center gap-2">
          <span className={`text-[11px] font-semibold ${outbound ? "text-slate-300" : "text-slate-400"}`}>
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
          <p className={`mb-1 text-xs font-semibold ${outbound ? "text-slate-200" : "text-slate-500"}`}>
            {event.subject}
          </p>
        )}
        <p className="whitespace-pre-wrap break-words leading-relaxed">{outbound ? event.body : event.message}</p>
        <p className={`mt-1.5 flex items-center gap-1 text-[10px] ${outbound ? "text-slate-400" : "text-slate-400"}`}>
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
    <span className="text-[11px] font-medium text-slate-400">
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
      <div className="mb-3 flex items-center justify-between border-b border-slate-100">
        <div className="flex gap-1">
          {CONVERSATION_CHANNELS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-medium transition-colors ${
                tab === key
                  ? "border-slate-800 text-slate-900"
                  : "border-transparent text-slate-400 hover:text-slate-700"
              }`}
            >
              <Icon size={13} /> {label} <span className="text-slate-400">({byChannel[key].length})</span>
            </button>
          ))}
        </div>
        <SequenceStageBadge seq={activeSeq} />
      </div>

      {messages.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-8 text-center">
          <MessagesSquare className="text-slate-300" size={28} />
          <p className="text-xs text-slate-400">No {tab === "EMAIL" ? "email" : "WhatsApp"} messages yet.</p>
        </div>
      ) : (
        <div ref={scrollRef} className="flex max-h-[480px] flex-col gap-3 overflow-y-auto rounded-md bg-slate-50 p-3">
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
        <Gauge className="text-slate-300" size={28} />
        <p className="text-xs text-slate-400">Not scored yet.</p>
      </div>
    );
  }
  const breakdown = score.scoring_breakdown || {};
  const orderedKeys = [...SCORE_BREAKDOWN_ORDER.filter((k) => k in breakdown),
    ...Object.keys(breakdown).filter((k) => !SCORE_BREAKDOWN_ORDER.includes(k))];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Badge variant={TIER_VARIANT[score.tier] || "NEUTRAL"}>{score.tier}</Badge>
        <span className="text-lg font-semibold text-slate-900">{score.score}<span className="text-xs font-normal text-slate-400">/100</span></span>
        <span className="text-xs text-slate-400">confidence {(score.confidence ?? 0).toFixed(2)}</span>
      </div>
      <p className="text-sm leading-relaxed text-slate-600">{score.justification}</p>
      <div className="flex flex-col gap-2">
        {orderedKeys.map((key) => {
          const value = breakdown[key] || 0;
          return (
            <div key={key} className="flex items-center gap-2 text-xs">
              <span className="w-24 shrink-0 capitalize text-slate-500">{key.replace(/_/g, " ")}</span>
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
                <div className={`h-full rounded-full transition-all ${barColor(value)}`} style={{ width: `${Math.round(value * 100)}%` }} />
              </div>
              <span className="w-8 text-right font-medium text-slate-500">{Math.round(value * 100)}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const EDITABLE_FIELDS = [
  ["company_name", "Company name", Building2],
  ["contact_person_name", "Contact person", UserIcon],
  ["contact_person_role", "Role", UserIcon],
  ["primary_email", "Email", Mail],
  ["primary_phone", "Phone", Phone],
  ["whatsapp_number", "WhatsApp number", MessageCircle],
  ["website_url", "Website", Globe],
  ["instagram_url", "Instagram", InstagramIcon],
  ["facebook_url", "Facebook", FacebookIcon],
  ["linkedin_url", "LinkedIn", LinkedinIcon],
  ["region_location", "Region", MapPin],
];

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
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {EDITABLE_FIELDS.map(([key, label, Icon]) => (
        <label key={key} className="flex flex-col gap-1">
          <span className="flex items-center gap-1 text-xs font-medium text-slate-500">
            <Icon size={12} className="text-slate-400" /> {label}
          </span>
          <input
            value={form[key]}
            placeholder="Not set"
            onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
            className="rounded-md border border-slate-200 px-2.5 py-1.5 text-sm text-slate-900 placeholder:text-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
        </label>
      ))}
      <div className="col-span-1 flex items-center gap-2 pt-1 sm:col-span-2">
        <button
          onClick={save}
          disabled={!dirty || saving}
          className="rounded-md bg-slate-800 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {saving ? "Saving…" : "Save changes"}
        </button>
        <button
          onClick={onCancel}
          className="rounded-md px-3 py-1.5 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-100"
        >
          Cancel
        </button>
        {error && <span className="text-xs text-red-600">{error}</span>}
      </div>
    </div>
  );
}

// Read-only by default (clean, scannable, matches how a CRM should display data at rest)
// -- the always-open input form this replaced looked "formy" even when nobody was
// editing anything. "Edit details" switches to ContactInfoForm above.
function ContactInfoDisplay({ lead, onEdit }) {
  return (
    <div className="flex flex-col gap-2.5">
      {EDITABLE_FIELDS.map(([key, label, Icon]) => (
        <div key={key} className="flex items-center gap-2.5 text-sm">
          <Icon size={13} className="shrink-0 text-slate-400" />
          <span className="w-28 shrink-0 text-xs text-slate-500">{label}</span>
          <span className={lead[key] ? "truncate text-slate-800" : "text-slate-300"}>
            {lead[key] || "Not set"}
          </span>
        </div>
      ))}
      <button
        onClick={onEdit}
        className="mt-2 w-fit rounded-md border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50"
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
    <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-800">
          <Icon size={15} className="text-slate-400" /> {title}
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
    <div className="rounded-md border border-slate-200 p-3">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-800">
          <Icon size={14} className="text-slate-400" /> {platform.label}
        </div>
        <a href={profileUrl} target="_blank" rel="noopener noreferrer"
           className="text-xs text-slate-400 hover:text-slate-700 hover:underline">
          Open profile
        </a>
      </div>

      {!queueItem && (
        <button
          onClick={requestDraft}
          disabled={drafting}
          className="mt-2 rounded-md border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {drafting ? "Drafting…" : `Draft ${platform.label} message`}
        </button>
      )}

      {queueItem && queueItem.status === "QUEUED" && (
        <div className="mt-2 flex flex-col gap-2">
          <p className="whitespace-pre-wrap rounded-md bg-slate-50 p-2.5 text-xs text-slate-700">
            {queueItem.message_text}
          </p>
          {queueItem.reasoning && (
            <p className="text-[11px] italic text-slate-400">Why: {queueItem.reasoning}</p>
          )}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={copyText}
              className="flex items-center gap-1 rounded-md border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50"
            >
              <Copy size={12} /> {copied ? "Copied" : "Copy text"}
            </button>
            <button
              onClick={markSent}
              disabled={acting}
              title="Confirm you sent this manually from your own account"
              className="flex items-center gap-1 rounded-md bg-slate-800 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Send size={12} /> Mark as Sent
            </button>
            <button
              onClick={dismissDraft}
              disabled={acting}
              className="flex items-center gap-1 rounded-md px-2.5 py-1.5 text-xs font-medium text-slate-400 transition-colors hover:bg-slate-50 hover:text-slate-600 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <X size={12} /> Dismiss
            </button>
          </div>
        </div>
      )}

      {queueItem && queueItem.status === "SENT" && (
        <div className="mt-2 flex items-center justify-between gap-2">
          <span className="text-xs text-emerald-600">Sent {relativeTime(queueItem.sent_at)}</span>
          <button
            onClick={requestDraft}
            disabled={drafting}
            className="text-xs font-medium text-slate-500 hover:text-slate-800 disabled:opacity-40"
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
            className="text-xs font-medium text-slate-500 hover:text-slate-800 disabled:opacity-40"
          >
            {drafting ? "Drafting…" : "Draft another"}
          </button>
        </div>
      )}

      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </div>
  );
}

function SocialOutreachCard({ lead, queue, onRefresh }) {
  const platforms = SOCIAL_PLATFORMS.filter((p) => lead[p.urlField]);
  if (platforms.length === 0) {
    return (
      <p className="text-xs text-slate-400">
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
    <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">
      <span className="text-[11px] text-slate-400">Copy this lead's real outreach content for:</span>
      {CROSS_CHANNEL_PLATFORMS.map(({ key, label, icon: Icon }) => (
        <button
          key={key}
          onClick={() => copyFor(key)}
          disabled={copying === key}
          title={`Copy for ${label}`}
          className="flex items-center gap-1.5 rounded-md border border-slate-200 px-2 py-1 text-[11px] font-medium text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
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
        strong ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
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
      <p className="text-xs text-slate-400">
        No individual contacts found yet at this company (needs the company's own LinkedIn
        page resolved first).
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      {contacts.map((c) => (
        <div key={c.id} className="flex items-start justify-between gap-3 rounded-md bg-slate-50 p-3 text-xs">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="font-semibold text-slate-800">{c.full_name || "Name not confirmed"}</span>
              {c.is_decision_maker ? (
                <span className="flex items-center gap-0.5 text-amber-500" title="Flagged as a decision maker">
                  <Star size={10} />
                </span>
              ) : null}
              <ConfidenceBadge confidence={c.confidence} />
            </div>
            <p className="mt-0.5 text-slate-500">{c.role}</p>
            <p className="mt-0.5 text-[10px] text-slate-400">via {c.source}</p>
          </div>
          {c.linkedin_url && (
            <a
              href={c.linkedin_url}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 text-slate-400 hover:text-slate-700"
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

  if (error) return <div className="mx-auto max-w-7xl px-6 py-6 text-sm text-red-600">{error}</div>;
  if (!lead) return <div className="mx-auto max-w-7xl px-6 py-10 text-center text-sm text-slate-400">Loading…</div>;

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-5 px-6 py-6">
      <div className="flex items-center justify-between gap-3">
        <Link to="/" className="flex w-fit items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-800">
          <ArrowLeft size={13} /> Back to dashboard
        </Link>

        {adjacent && (
          <div className="flex items-center gap-2">
            {adjacent.total > 0 && (
              <span className="text-xs text-slate-400">Lead {adjacent.position} of {adjacent.total}</span>
            )}
            <button
              onClick={() => goTo(adjacent.prev.id)}
              disabled={!adjacent.prev}
              title={adjacent.prev ? adjacent.prev.company_name : undefined}
              className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ChevronLeft size={13} /> Previous
            </button>
            <button
              onClick={() => goTo(adjacent.next.id)}
              disabled={!adjacent.next}
              title={adjacent.next ? adjacent.next.company_name : undefined}
              className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Next <ChevronRight size={13} />
            </button>
          </div>
        )}
      </div>

      <div className="flex items-start justify-between gap-3 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-slate-100 text-sm font-semibold text-slate-600">
            {lead.company_name.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold text-slate-900">{lead.company_name}</h1>
              {lead.reference_code && (
                <span
                  title="Reference code -- quote this in alerts/conversation to identify this lead"
                  className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[11px] text-slate-500"
                >
                  {lead.reference_code}
                </span>
              )}
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
              {lead.region_location && (
                <span className="flex items-center gap-1"><MapPin size={12} /> {lead.region_location}</span>
              )}
              {lead.primary_email && (
                <a href={`mailto:${lead.primary_email}`} className="flex items-center gap-1 hover:text-slate-800 hover:underline">
                  <Mail size={12} /> {lead.primary_email}
                </a>
              )}
              {lead.primary_phone && (
                <a href={`tel:${lead.primary_phone}`} className="flex items-center gap-1 hover:text-slate-800 hover:underline">
                  <Phone size={12} /> {lead.primary_phone}
                </a>
              )}
              {lead.instagram_url && (
                <a href={lead.instagram_url} target="_blank" rel="noopener noreferrer"
                   title="Instagram" className="flex items-center text-slate-400 hover:text-slate-800">
                  <InstagramIcon size={13} />
                </a>
              )}
              {lead.facebook_url && (
                <a href={lead.facebook_url} target="_blank" rel="noopener noreferrer"
                   title="Facebook" className="flex items-center text-slate-400 hover:text-slate-800">
                  <FacebookIcon size={13} />
                </a>
              )}
              {lead.linkedin_url && (
                <a href={lead.linkedin_url} target="_blank" rel="noopener noreferrer"
                   title="LinkedIn" className="flex items-center text-slate-400 hover:text-slate-800">
                  <LinkedinIcon size={13} />
                </a>
              )}
              <span className="text-slate-300">·</span>
              <span>Added {relativeTime(lead.created_at)}</span>
            </div>
          </div>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-2">
          <div className="flex items-center gap-2">
            {lead.interest_state === "YES" && (
              <span
                title={`Clicked "Yes, tell me more" on a real outreach send${lead.interest_state_at ? ` (${relativeTime(lead.interest_state_at)})` : ""}`}
                className="inline-flex shrink-0 items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 ring-1 ring-inset ring-emerald-200"
              >
                <CheckCircle2 size={11} /> Said Yes
              </span>
            )}
            {lead.interest_state === "NO" && (
              <span
                title={`Clicked "Not right now" -- declined this pitch, still contactable (NOT unsubscribed)${lead.interest_state_at ? ` (${relativeTime(lead.interest_state_at)})` : ""}`}
                className="inline-flex shrink-0 items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-semibold text-blue-700 ring-1 ring-inset ring-blue-200"
              >
                <XCircle size={11} /> Said No
              </span>
            )}
            {lead.is_suppressed && (
              <span
                title="This lead's email/phone is in the suppression list -- no future outreach will be sent"
                className="inline-flex shrink-0 items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-500 ring-1 ring-inset ring-slate-200"
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
              className="rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {markingContacted ? "Marking…" : "Mark as Contacted"}
            </button>
          )}
          {lead.score && (lead.primary_email || lead.primary_phone) && !lead.is_suppressed && (
            <button
              onClick={() => sendOutreach()}
              disabled={sendInFlight}
              className="rounded-md bg-slate-800 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40"
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
                className="flex items-center gap-1 rounded-md bg-emerald-50 px-2.5 py-1.5 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-200 transition-colors hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Trophy size={12} /> Mark Converted
              </button>
              <button
                onClick={() => closeDeal("REJECTED")}
                disabled={closingStatus}
                title="Mark as a lost deal"
                className="flex items-center gap-1 rounded-md bg-white px-2.5 py-1.5 text-xs font-medium text-slate-500 ring-1 ring-inset ring-slate-200 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
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
        <div className="-mt-3 flex flex-wrap gap-3 rounded-lg border border-slate-200 bg-white px-4 py-2 text-xs shadow-sm">
          {Object.entries(sendResult).map(([channel, r]) => (
            <span key={channel} className={r.status === "SENT" ? "text-emerald-600" : "text-amber-600"}>
              {channel}: {r.status === "SENT" ? "Sent ✓" : `Escalated (${r.reason || "needs review"})`}
            </span>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <SectionCard title="Contact & profile" icon={UserIcon}>
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
        <SectionCard title="Score" icon={Gauge}>
          <ScoreCard score={lead.score} />
        </SectionCard>
      </div>

      {lead.pain_points.length > 0 && (
        <SectionCard title="Verified pain points" icon={AlertTriangle}>
          <div className="flex flex-col gap-2">
            {lead.pain_points.map((p, i) => (
              <div key={i} className="flex items-start gap-3 rounded-md bg-slate-50 p-3 text-xs">
                <div className={`mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full ${barColor(p.severity_0_1 || 0)}`} />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-800">{p.code.replace(/_/g, " ")}</span>
                    <span className="text-slate-400">severity {Math.round((p.severity_0_1 || 0) * 100)}%</span>
                  </div>
                  <p className="mt-1 italic text-slate-600">&ldquo;{p.evidence_quote}&rdquo;</p>
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
          {!timeline && <p className="text-xs text-slate-400">Loading…</p>}
          {timeline && (
            <div className="flex flex-col gap-3">
              <ConversationPanel events={timeline} sequences={lead?.followup_sequences} />
              <CrossChannelCopyBar leadId={id} />
            </div>
          )}
        </SectionCard>

        <SectionCard
          title="Timeline"
          icon={Clock}
          headerExtra={<span className="text-xs text-slate-400">{timeline ? `${timeline.length} events` : ""}</span>}
        >
          {!timeline && <p className="text-xs text-slate-400">Loading…</p>}
          {timeline && timeline.length === 0 && (
            <div className="flex flex-col items-center gap-2 py-6 text-center">
              <Clock className="text-slate-300" size={28} />
              <p className="text-xs text-slate-400">No activity yet.</p>
            </div>
          )}
          {timeline && timeline.length > 0 && (
            <div className="-mx-4 -mb-4 rounded-b-lg border-t border-slate-100">
              <Timeline events={timeline} />
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}
