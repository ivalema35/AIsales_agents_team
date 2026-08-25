import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Plus, RefreshCw, Tag, Clock3, CheckCircle2, XCircle, Package, MessageSquareText, Boxes,
  Sparkles, Check, X as XIcon,
} from "lucide-react";
import { api } from "../api/client";
import { useConfirm } from "../lib/ConfirmContext";
import Badge from "../components/ui/Badge";
import ChipInput from "../components/ui/ChipInput";

const CATEGORIES = ["MARKETING", "UTILITY", "AUTHENTICATION"];
const PURPOSES = ["FIRST_TOUCH", "FOLLOW_UP"];
const STATUS_VARIANT = { PENDING: "WARNING", APPROVED: "SUCCESS", REJECTED: "DANGER", ADMIN_REJECTED: "DANGER" };
const DEAD_STATUSES = ["ADMIN_REJECTED", "REJECTED"];

// Phase 13 Step 13.1/13.2 -- the same 3 real follow-up conversations as the email side.
const FOLLOWUP_LEVEL_HINT = {
  1: "Level 1 re-presents the first touch (e.g. a reminder about the demo/pain point).",
  2: "Level 2 is a short, plain open question -- no pitch, just inviting a reply.",
  3: "Level 3 is the last touch: a low-pressure standing offer, never a final push.",
};

const EMPTY_DRAFT = {
  name: "", language: "en", category: "MARKETING", purpose: "FOLLOW_UP", followup_level: 1,
  body_text: "", variable_labels: [], product_id: "", button_url: "", button_label: "",
};

function StatTile({ icon: Icon, label, value, tone = "slate" }) {
  const toneClass = {
    slate: "bg-slate-100 text-slate-600",
    emerald: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
    red: "bg-red-50 text-red-600",
    violet: "bg-violet-50 text-violet-600",
  }[tone];
  return (
    <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-3.5 shadow-sm">
      <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-md ${toneClass}`}>
        <Icon size={16} />
      </div>
      <div className="min-w-0">
        <p className="text-lg font-semibold leading-none text-slate-900">{value}</p>
        <p className="mt-1 truncate text-[11px] text-slate-500">{label}</p>
      </div>
    </div>
  );
}

function BuiltinCard({ t }) {
  return (
    <div className="rounded-md border border-dashed border-slate-300 bg-slate-50/70 p-3">
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="text-xs font-semibold text-slate-800">{t.name}</span>
        <Badge variant="SUCCESS">{t.status}</Badge>
        <Badge variant="NEUTRAL">Built-in</Badge>
      </div>
      {t.body_text ? (
        <p className="mt-1.5 whitespace-pre-wrap text-[11px] leading-relaxed text-slate-600">
          "{t.body_text}"
        </p>
      ) : (
        <p className="mt-1.5 text-[11px] italic leading-relaxed text-slate-400">
          Couldn't fetch the real wording from Meta just now -- try reloading the page.
        </p>
      )}
      {t.variable_labels.length > 0 && (
        <p className="mt-1.5 flex items-center gap-1 text-[10px] text-slate-400">
          <Tag size={10} /> {t.variable_labels.join(", ")}
        </p>
      )}
      <p className="mt-1.5 text-[10px] leading-relaxed text-slate-400">
        Managed in code, not from this dashboard -- not editable here.
      </p>
    </div>
  );
}

function ProposedCard({ t, onApprove, onReject, busyId }) {
  const busy = busyId === t.id;
  return (
    <div className="rounded-md border border-violet-200 bg-violet-50/40 p-3">
      <div className="flex flex-wrap items-center gap-1.5">
        <Sparkles size={12} className="text-violet-500" />
        <span className="text-xs font-semibold text-slate-800">{t.name}</span>
        <Badge variant="NEUTRAL">{t.purpose}{t.followup_level ? ` L${t.followup_level}` : ""}</Badge>
        {t.button_url && (
          <span title={t.button_url} className="rounded bg-violet-50 px-1.5 py-0.5 text-[10px] font-medium text-violet-600">
            Button: {t.button_label || "View"}
          </span>
        )}
        <Badge variant="NEUTRAL">{t.category}</Badge>
        <span className="flex items-center gap-1 text-[10px] font-medium text-slate-400">
          <Boxes size={10} /> {t.product_title || "Shared -- all products"}
        </span>
      </div>
      <p className="mt-1.5 whitespace-pre-wrap text-[11px] leading-relaxed text-slate-700">
        "{t.body_text}"
      </p>
      {t.variable_labels.length > 0 && (
        <p className="mt-1 flex items-center gap-1 text-[10px] text-slate-400">
          <Tag size={10} /> {t.variable_labels.join(", ")}
        </p>
      )}
      {t.reasoning && (
        <p className="mt-1.5 rounded bg-white/70 px-2 py-1.5 text-[11px] italic leading-relaxed text-slate-500">
          AI's reasoning: {t.reasoning}
        </p>
      )}
      <div className="mt-2.5 flex items-center gap-2">
        <button
          onClick={() => onApprove(t)}
          disabled={busy}
          className="flex items-center gap-1 rounded-md bg-slate-800 px-2.5 py-1.5 text-[11px] font-medium text-white hover:bg-slate-900 disabled:opacity-50"
        >
          <Check size={11} /> Approve & Submit to Meta
        </button>
        <button
          onClick={() => onReject(t)}
          disabled={busy}
          className="flex items-center gap-1 rounded-md px-2.5 py-1.5 text-[11px] font-medium text-red-500 hover:bg-red-50 disabled:opacity-50"
        >
          <XIcon size={11} /> Reject
        </button>
      </div>
    </div>
  );
}

// Phase 9 Step 9.5 -- admin submits a real WhatsApp template (real Meta Create Template
// API call) and tracks its real approval state, without ever needing a code edit once
// approved. A FOLLOW_UP-purpose template that reaches APPROVED is automatically
// preferred by jobs/outreach_wa_handler.py over resending touch 1's own template.
export default function WhatsappTemplates() {
  const [builtin, setBuiltin] = useState(null);
  const [templates, setTemplates] = useState(null);
  const [proposed, setProposed] = useState(null);
  const [products, setProducts] = useState([]);
  const [searchParams] = useSearchParams();
  const [purposeFilter, setPurposeFilter] = useState("");
  const [productFilter, setProductFilter] = useState(searchParams.get("product_id") || "");
  const [activeTab, setActiveTab] = useState(searchParams.get("product_id") ? "submitted" : "builtin");
  const [showAddForm, setShowAddForm] = useState(false);
  const [draft, setDraft] = useState(EMPTY_DRAFT);
  const [saving, setSaving] = useState(false);
  const [refreshingId, setRefreshingId] = useState(null);
  const [togglingId, setTogglingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [proposedBusyId, setProposedBusyId] = useState(null);
  const [asking, setAsking] = useState(null);
  const [askResult, setAskResult] = useState(null);
  const [error, setError] = useState(null);
  const confirm = useConfirm();

  useEffect(() => {
    api.listBuiltinWhatsappTemplates().then(setBuiltin).catch((err) => setError(err.message));
    api.listProducts().then(setProducts).catch((err) => setError(err.message));
  }, []);

  function refresh() {
    const params = {};
    if (purposeFilter) params.purpose = purposeFilter;
    if (productFilter) params.product_id = productFilter;
    api.listWhatsappTemplates(params).then(setTemplates).catch((err) => setError(err.message));
  }

  useEffect(refresh, [purposeFilter, productFilter]);

  function refreshProposed() {
    api.listWhatsappTemplates({ status: "DRAFT" }).then(setProposed).catch((err) => setError(err.message));
  }

  useEffect(refreshProposed, []);

  const submittedTemplates = useMemo(
    () => (templates || []).filter((t) => t.status !== "DRAFT"),
    [templates],
  );

  async function askAi(purpose, followupLevel) {
    const askingKey = followupLevel ? `${purpose}_${followupLevel}` : purpose;
    setAsking(askingKey);
    setAskResult(null);
    setError(null);
    try {
      const res = await api.proposeWhatsappTemplate(purpose, followupLevel);
      setAskResult(res);
      if (res.proposed) refreshProposed();
    } catch (err) {
      setError(err.message);
    } finally {
      setAsking(null);
    }
  }

  async function approveProposed(t) {
    const ok = await confirm({
      title: "Approve and submit this AI-drafted template to Meta?",
      message:
        "This sends a real Create Template request to your WhatsApp Business Account. " +
        "It cannot be edited once submitted, and repeated bad submissions can affect your " +
        "account's standing with Meta. Review the wording above carefully before approving.",
      confirmLabel: "Approve & Submit to Meta",
    });
    if (!ok) return;

    setProposedBusyId(t.id);
    try {
      await api.approveWhatsappTemplate(t.id);
      refreshProposed();
      refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setProposedBusyId(null);
    }
  }

  async function rejectProposed(t) {
    const ok = await confirm({
      title: "Reject this AI-drafted template?",
      message: "It will never be sent to Meta and this can't be undone. The AI can always propose another.",
      confirmLabel: "Reject",
    });
    if (!ok) return;

    setProposedBusyId(t.id);
    try {
      await api.rejectWhatsappTemplate(t.id);
      refreshProposed();
    } catch (err) {
      setError(err.message);
    } finally {
      setProposedBusyId(null);
    }
  }

  const stats = useMemo(() => {
    const all = templates || [];
    return {
      pending: all.filter((t) => t.status === "PENDING").length,
      approved: all.filter((t) => t.status === "APPROVED").length,
      rejected: all.filter((t) => t.status === "REJECTED").length,
    };
  }, [templates]);

  const placeholderCount = (draft.body_text.match(/\{\{\d+\}\}/g) || []).length;
  const countMismatch = placeholderCount !== draft.variable_labels.length;

  async function submit(e) {
    e.preventDefault();
    if (!draft.name.trim() || !draft.body_text.trim() || countMismatch) return;

    const ok = await confirm({
      title: "Submit this template to Meta?",
      message:
        "This sends a real Create Template request to your WhatsApp Business Account. " +
        "It cannot be edited once submitted, and repeated bad submissions can affect your " +
        "account's standing with Meta. Are you sure the wording is final?",
      confirmLabel: "Submit to Meta",
    });
    if (!ok) return;

    setSaving(true);
    setError(null);
    try {
      await api.createWhatsappTemplate({ ...draft, product_id: draft.product_id || null });
      setDraft(EMPTY_DRAFT);
      setShowAddForm(false);
      refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function refreshOne(id) {
    setRefreshingId(id);
    try {
      await api.refreshWhatsappTemplate(id);
      refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setRefreshingId(null);
    }
  }

  async function toggleActive(t) {
    setTogglingId(t.id);
    try {
      await api.updateWhatsappTemplate(t.id, { is_active: !t.is_active });
      refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setTogglingId(null);
    }
  }

  async function deleteTemplate(t) {
    const ok = await confirm({
      title: "Delete this rejected template?",
      message: "It never sent to real businesses and can't be used going forward -- this just clears it from the list. Can't be undone.",
      confirmLabel: "Delete",
    });
    if (!ok) return;

    setDeletingId(t.id);
    try {
      await api.deleteWhatsappTemplate(t.id);
      refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <h1 className="text-lg font-semibold text-slate-900">WhatsApp Templates</h1>
      <p className="mb-5 mt-1 max-w-2xl text-xs leading-relaxed text-slate-500">
        Cold WhatsApp only ever goes out via a template Meta has already approved -- this is where new
        ones get submitted and their real approval status tracked. A FOLLOW_UP template that gets
        APPROVED is automatically used for follow-up sends instead of repeating the first-touch message.
      </p>

      {error && (
        <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-xs text-red-600">{error}</p>
      )}

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-5">
        <StatTile icon={Package} label="Built-in templates" value={builtin ? builtin.length : "…"} tone="slate" />
        <StatTile icon={Sparkles} label="AI proposed" value={proposed ? proposed.length : "…"} tone="violet" />
        <StatTile icon={Clock3} label="Pending approval" value={templates ? stats.pending : "…"} tone="amber" />
        <StatTile icon={CheckCircle2} label="Approved" value={templates ? stats.approved : "…"} tone="emerald" />
        <StatTile icon={XCircle} label="Rejected" value={templates ? stats.rejected : "…"} tone="red" />
      </div>

      <div className="mb-4 flex items-center gap-1 border-b border-slate-200">
        <button
          onClick={() => setActiveTab("builtin")}
          className={`px-3 py-2 text-xs font-semibold uppercase tracking-wide transition-colors ${
            activeTab === "builtin" ? "border-b-2 border-slate-800 text-slate-800" : "text-slate-400 hover:text-slate-600"
          }`}
        >
          Built-in {builtin ? `(${builtin.length})` : ""}
        </button>
        <button
          onClick={() => setActiveTab("proposed")}
          className={`flex items-center gap-1 px-3 py-2 text-xs font-semibold uppercase tracking-wide transition-colors ${
            activeTab === "proposed" ? "border-b-2 border-violet-500 text-violet-600" : "text-slate-400 hover:text-slate-600"
          }`}
        >
          <Sparkles size={12} /> AI Proposed {proposed ? `(${proposed.length})` : ""}
        </button>
        <button
          onClick={() => setActiveTab("submitted")}
          className={`px-3 py-2 text-xs font-semibold uppercase tracking-wide transition-colors ${
            activeTab === "submitted" ? "border-b-2 border-slate-800 text-slate-800" : "text-slate-400 hover:text-slate-600"
          }`}
        >
          Submitted {templates ? `(${submittedTemplates.length})` : ""}
        </button>
      </div>

      {activeTab === "builtin" && (
        <div className="mb-6">
          <p className="mb-3 text-[11px] text-slate-400">
            Already live for real first-touch sends today, submitted by hand before this dashboard
            existed. Wording is fetched live from Meta -- read-only, not editable here.
          </p>
          {builtin && builtin.length > 0 ? (
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {builtin.map((t) => <BuiltinCard key={t.key} t={t} />)}
            </div>
          ) : (
            <p className="text-xs text-slate-500">Loading…</p>
          )}
        </div>
      )}

      {activeTab === "proposed" && (
        <div className="mb-6">
          <div className="mb-3 flex items-start justify-between gap-3 rounded-md bg-slate-50 p-3">
            <p className="text-xs leading-relaxed text-slate-500">
              Ask the AI to look at real send/reply data and template coverage, and propose a new
              template ONLY if a real gap or underperformer actually exists for the purpose you pick --
              it never invents a need. Nothing reaches Meta until you approve a specific draft below.
            </p>
            <div className="flex shrink-0 flex-col items-stretch gap-1.5">
              <button
                onClick={() => askAi("FIRST_TOUCH")}
                disabled={!!asking}
                className="flex items-center justify-center gap-1.5 rounded-md bg-violet-600 px-3 py-1.5 text-[11px] font-medium text-white hover:bg-violet-700 disabled:opacity-50"
              >
                <Sparkles size={12} /> {asking === "FIRST_TOUCH" ? "Thinking…" : "Ask for a First Touch template"}
              </button>
              {/* Phase 13 Step 13.2 -- each follow-up level is its own independent
                 coverage gap now (get_approved_followup_template matches strictly per
                 level), so "Ask AI" needs to know WHICH level, not just "a follow-up". */}
              {[1, 2, 3].map((level) => (
                <button
                  key={level}
                  onClick={() => askAi("FOLLOW_UP", level)}
                  disabled={!!asking}
                  className="flex items-center justify-center gap-1.5 rounded-md bg-violet-600 px-3 py-1.5 text-[11px] font-medium text-white hover:bg-violet-700 disabled:opacity-50"
                >
                  <Sparkles size={12} />
                  {asking === `FOLLOW_UP_${level}` ? "Thinking…" : `Ask for a Level ${level} follow-up template`}
                </button>
              ))}
            </div>
          </div>

          {askResult && (
            <p className={`mb-3 rounded-md px-3 py-2 text-xs ${
              askResult.proposed ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"
            }`}>
              {askResult.proposed
                ? "A new draft was created below -- review it before approving."
                : askResult.message}
            </p>
          )}

          {proposed && proposed.length > 0 ? (
            <div className="flex flex-col gap-2">
              {proposed.map((t) => (
                <ProposedCard key={t.id} t={t} onApprove={approveProposed} onReject={rejectProposed} busyId={proposedBusyId} />
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 rounded-md border border-dashed border-slate-200 py-8 text-center">
              <Sparkles size={22} className="text-slate-300" />
              <p className="text-xs text-slate-500">No AI-proposed drafts waiting for review.</p>
            </div>
          )}
        </div>
      )}

      {activeTab === "submitted" && (
      <>
      <div className="mb-3 flex flex-wrap items-center gap-1.5">
        {["", ...PURPOSES].map((p) => (
          <button
            key={p || "ALL"}
            onClick={() => setPurposeFilter(p)}
            className={`rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors ${
              purposeFilter === p ? "bg-slate-800 text-white" : "bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-50"
            }`}
          >
            {p || "All purposes"}
          </button>
        ))}
        <span className="mx-0.5 text-slate-200">|</span>
        <select
          value={productFilter}
          onChange={(e) => setProductFilter(e.target.value)}
          className="rounded-md border border-slate-200 bg-white px-2 py-1 text-[11px] font-medium text-slate-600 focus:border-slate-400 focus:outline-none"
        >
          <option value="">All products</option>
          {products.map((p) => <option key={p.id} value={p.id}>{p.title}</option>)}
        </select>
      </div>

      {templates && submittedTemplates.length > 0 && (
        <div className="mb-4 flex flex-col gap-2">
          {submittedTemplates.map((t) => (
            <div
              key={t.id}
              className={`rounded-md border border-slate-200 bg-white p-3 shadow-sm ${!t.is_active ? "opacity-60" : ""}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="text-xs font-semibold text-slate-800">{t.name}</span>
                    <Badge variant={STATUS_VARIANT[t.status] || "NEUTRAL"}>{t.status}</Badge>
                    {!t.is_active && <Badge variant="NEUTRAL">Disabled</Badge>}
                    <Badge variant="NEUTRAL">{t.purpose}{t.followup_level ? ` L${t.followup_level}` : ""}</Badge>
        {t.button_url && (
          <span title={t.button_url} className="rounded bg-violet-50 px-1.5 py-0.5 text-[10px] font-medium text-violet-600">
            Button: {t.button_label || "View"}
          </span>
        )}
                    <Badge variant="NEUTRAL">{t.category}</Badge>
                    {t.origin === "AI" && (
                      <span className="flex items-center gap-0.5 text-[10px] font-medium text-violet-500">
                        <Sparkles size={10} /> AI-drafted
                      </span>
                    )}
                    <span className="flex items-center gap-1 text-[10px] font-medium text-slate-400">
                      <Boxes size={10} /> {t.product_title || "Shared -- all products"}
                    </span>
                  </div>
                  <p className="mt-1.5 whitespace-pre-wrap text-[11px] leading-relaxed text-slate-600">
                    {t.body_text}
                  </p>
                  {t.variable_labels.length > 0 && (
                    <p className="mt-1 flex items-center gap-1 text-[10px] text-slate-400">
                      <Tag size={10} /> {t.variable_labels.join(", ")}
                    </p>
                  )}
                  {t.status === "REJECTED" && t.rejection_reason && (
                    <p className="mt-1 text-[11px] text-red-600">Rejected: {t.rejection_reason}</p>
                  )}
                  {DEAD_STATUSES.includes(t.status) && (
                    <p className="mt-1 text-[11px] text-slate-400">
                      {t.status === "ADMIN_REJECTED"
                        ? "Rejected before it ever reached Meta -- permanently unusable, safe to delete."
                        : "Meta declined this submission -- permanently unusable, safe to delete."}
                    </p>
                  )}
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  {t.status === "PENDING" && (
                    <button
                      onClick={() => refreshOne(t.id)}
                      disabled={refreshingId === t.id}
                      title="Check real status now"
                      className="flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium text-slate-500 hover:bg-slate-100 disabled:opacity-50"
                    >
                      <RefreshCw size={11} className={refreshingId === t.id ? "animate-spin" : ""} />
                      Check status
                    </button>
                  )}
                  {DEAD_STATUSES.includes(t.status) ? (
                    <button
                      onClick={() => deleteTemplate(t)}
                      disabled={deletingId === t.id}
                      title="Delete this permanently-unusable template"
                      className="rounded-md px-2 py-1 text-[11px] font-medium text-red-500 hover:bg-red-50 disabled:opacity-50"
                    >
                      Delete
                    </button>
                  ) : (
                    <button
                      onClick={() => toggleActive(t)}
                      disabled={togglingId === t.id}
                      title={t.is_active ? "Stop using this template" : "Allow this template to be used again"}
                      className={`rounded-md px-2 py-1 text-[11px] font-medium hover:bg-slate-100 disabled:opacity-50 ${
                        t.is_active ? "text-slate-500" : "text-emerald-600"
                      }`}
                    >
                      {t.is_active ? "Disable" : "Enable"}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {templates && submittedTemplates.length === 0 && !showAddForm && (
        <div className="mb-4 flex flex-col items-center gap-2 rounded-md border border-dashed border-slate-200 py-8 text-center">
          <MessageSquareText size={22} className="text-slate-300" />
          <p className="text-xs text-slate-500">
            {purposeFilter ? `No ${purposeFilter.replace("_", " ").toLowerCase()} templates submitted yet.` : "No templates submitted yet."}
          </p>
        </div>
      )}

      {!showAddForm && (
        <button
          onClick={() => { setDraft((d) => ({ ...d, product_id: productFilter })); setShowAddForm(true); }}
          className="flex w-fit items-center gap-1 rounded-md bg-slate-800 px-3 py-1.5 text-[11px] font-medium text-white hover:bg-slate-900"
        >
          <Plus size={12} /> New template
        </button>
      )}

      {showAddForm && (
        <form onSubmit={submit} className="flex flex-col gap-3.5 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-xs font-semibold text-slate-700">New template</h3>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <label className="flex flex-col gap-1 sm:col-span-2">
              <span className="text-[11px] font-medium text-slate-600">Template name</span>
              <input
                required
                value={draft.name}
                onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))}
                placeholder="e.g. gamezone_followup_nudge"
                className="rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-800 placeholder:text-slate-300 focus:border-slate-400 focus:outline-none"
              />
              <span className="text-[10px] text-slate-400">Lowercase letters, digits, underscores only (Meta's own rule).</span>
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-[11px] font-medium text-slate-600">Language</span>
              <input
                value={draft.language}
                onChange={(e) => setDraft((d) => ({ ...d, language: e.target.value }))}
                placeholder="en"
                className="rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-800 placeholder:text-slate-300 focus:border-slate-400 focus:outline-none"
              />
            </label>
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-[11px] font-medium text-slate-600">Category</span>
            <div className="flex flex-wrap gap-1.5">
              {CATEGORIES.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setDraft((d) => ({ ...d, category: c }))}
                  className={`rounded-md px-2 py-1 text-[11px] font-medium transition-colors ${
                    draft.category === c ? "bg-slate-800 text-white" : "bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-[11px] font-medium text-slate-600">Purpose</span>
            <div className="flex flex-wrap gap-1.5">
              {PURPOSES.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setDraft((d) => ({ ...d, purpose: p }))}
                  className={`rounded-md px-2 py-1 text-[11px] font-medium transition-colors ${
                    draft.purpose === p ? "bg-slate-800 text-white" : "bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {p === "FOLLOW_UP" ? "Follow-up nudge" : "First touch"}
                </button>
              ))}
            </div>
            {draft.purpose === "FOLLOW_UP" && (
              <>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {[1, 2, 3].map((level) => (
                    <button
                      key={level}
                      type="button"
                      onClick={() => setDraft((d) => ({ ...d, followup_level: level }))}
                      className={`rounded-md px-2 py-1 text-[11px] font-medium transition-colors ${
                        draft.followup_level === level
                          ? "bg-slate-800 text-white"
                          : "bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-50"
                      }`}
                    >
                      Level {level}
                    </button>
                  ))}
                </div>
                <span className="text-[10px] text-slate-400">
                  {FOLLOWUP_LEVEL_HINT[draft.followup_level]} Once approved, this is used ONLY for this
                  exact level -- if this level has no approved template, that touch sends nothing on
                  WhatsApp rather than reusing a different level's text.
                </span>
              </>
            )}
          </div>

          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-medium text-slate-600">Product</span>
            <select
              value={draft.product_id}
              onChange={(e) => setDraft((d) => ({ ...d, product_id: e.target.value }))}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-800 focus:border-slate-400 focus:outline-none"
            >
              <option value="">Shared -- usable by every product (default)</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.title}</option>)}
            </select>
            <span className="text-[10px] text-slate-400">
              A product-specific template needs its own separate Meta approval -- leave this as Shared
              unless this product's pitch genuinely needs different wording.
            </span>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-medium text-slate-600">Message body</span>
            <textarea
              required
              rows={3}
              value={draft.body_text}
              onChange={(e) => setDraft((d) => ({ ...d, body_text: e.target.value }))}
              placeholder={"Hi {{1}}, still worth a look for {{2}}?"}
              className="w-full resize-none rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-800 placeholder:text-slate-300 focus:border-slate-400 focus:outline-none"
            />
          </label>

          <ChipInput
            icon={Tag}
            label="Variables (in {{1}}, {{2}}… order)"
            hint="Use contact_name, company_name, or pain_point_phrase -- these are the only values the system knows how to fill in automatically."
            values={draft.variable_labels}
            onChange={(variable_labels) => setDraft((d) => ({ ...d, variable_labels }))}
            placeholder="contact_name, company_name…"
          />
          {draft.body_text && countMismatch && (
            <p className="rounded-md bg-amber-50 px-2.5 py-1.5 text-[11px] text-amber-700">
              Body has {placeholderCount} {"{{n}}"} placeholder(s) but {draft.variable_labels.length} variable(s) listed -- these must match before submitting.
            </p>
          )}

          {/* Real feature -- WhatsApp templates can carry a static call-to-action button,
             same as the email side's CTA/demo button. Static on purpose: content assets
             here are scoped per product, not per lead, so every real send of this
             template already points at the same real, approved link -- no per-lead
             {{n}} substitution needed. */}
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-medium text-slate-600">Button URL (optional)</span>
            <input
              type="url"
              value={draft.button_url}
              onChange={(e) => setDraft((d) => ({ ...d, button_url: e.target.value }))}
              placeholder="https://ivinfotech.com/demo"
              className="rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-800 placeholder:text-slate-300 focus:border-slate-400 focus:outline-none"
            />
            <span className="text-[10px] text-slate-400">
              A real, static demo/website link -- adds a clickable button below the message. Same
              link for every real send of this template (no per-lead personalization on WhatsApp).
            </span>
          </label>
          {draft.button_url && (
            <label className="flex flex-col gap-1">
              <span className="text-[11px] font-medium text-slate-600">Button label (max 25 chars)</span>
              <input
                type="text"
                maxLength={25}
                value={draft.button_label}
                onChange={(e) => setDraft((d) => ({ ...d, button_label: e.target.value }))}
                placeholder="View Demo"
                className="rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-800 placeholder:text-slate-300 focus:border-slate-400 focus:outline-none"
              />
            </label>
          )}

          <div className="flex items-center gap-2 border-t border-slate-100 pt-3.5">
            <button
              type="submit"
              disabled={saving || countMismatch}
              className="rounded-md bg-slate-800 px-3.5 py-1.5 text-xs font-medium text-white hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {saving ? "Submitting…" : "Submit to Meta"}
            </button>
            <button
              type="button"
              onClick={() => { setShowAddForm(false); setDraft(EMPTY_DRAFT); }}
              className="rounded-md px-3.5 py-1.5 text-xs font-medium text-slate-500 hover:bg-slate-100"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
      </>
      )}
    </div>
  );
}
