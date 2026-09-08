import { useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, CheckCircle2, Mail, MessageSquareWarning, Sparkles, X } from "lucide-react";
import { api } from "../api/client";
import { industryLabel, locationLabel } from "../lib/targetSegment";

// Phase 21 -- a todo item whose label is genuinely about a real signal conflict (Step
// 20.2) gets distinct, more urgent styling than an ordinary note, so a human's eye lands
// on it first. Matching by label text, not a fixed enum -- the strategist's labels are
// free-text by design (Step 18.1), "Conflict"/"Tension" are just what it tends to write.
function isConflictLabel(label) {
  const l = (label || "").toLowerCase();
  return l.includes("conflict") || l.includes("tension");
}

function isOutreachEmailDraft(proposal) {
  return proposal && proposal.kind === "outreach_email_draft" && proposal.subject && proposal.body;
}

// Shared by the Dashboard's AI Manager Inbox (every campaign/product, unfiltered) and a
// Campaign Detail page's own queue (filtered to just that campaign) -- one card design,
// never two independently-drifting ones. `onResolved(id)` tells the parent list to drop
// this card once it's approved/dismissed. `onApproveGlobal(prefill, item)` is only relevant
// for a GLOBAL ("new campaign idea") card -- the parent (which owns the shared
// CampaignFormModal) opens it pre-filled; a CAMPAIGN-scope card never calls this.
export default function TodoItemCard({ item: initialItem, showSourceChip = false, onResolved, onApproveGlobal }) {
  const [item, setItem] = useState(initialItem);
  const [showFeedback, setShowFeedback] = useState(false);
  const [instruction, setInstruction] = useState("");
  const [revising, setRevising] = useState(false);
  const [pushback, setPushback] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  // 2026-09-07, user-flagged real gap: approving used to just silently remove the card --
  // no confirmation of WHAT actually changed on the real campaign. Now a CAMPAIGN-scope
  // approval with a real applied proposal shows a persistent "Applied" summary instead of
  // vanishing, until the human explicitly closes it.
  const [appliedResult, setAppliedResult] = useState(null);

  const conflict = isConflictLabel(item.label);
  const proposal = item.proposal;
  const emailDraft = isOutreachEmailDraft(proposal);
  // GLOBAL always has a real action (opens the campaign-creation form); a CAMPAIGN item
  // has one when it carries a structural proposal OR is the standing "Approve campaign"
  // cue (that actually flips campaign status to APPROVED on Approve) OR an email draft
  // waiting for Approve & send.
  const hasAction =
    item.scope === "GLOBAL" || !!proposal || item.label === "Approve campaign";

  async function submitFeedback(e) {
    e.preventDefault();
    if (!instruction.trim()) return;
    setRevising(true);
    setError(null);
    try {
      const result = await api.submitTodoFeedback(item.id, instruction);
      setItem(result.item);
      setPushback(result.pushback || null);
      setInstruction("");
      setShowFeedback(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setRevising(false);
    }
  }

  async function approve() {
    setBusy(true);
    setError(null);
    try {
      const result = await api.approveTodoItem(item.id);
      if (item.scope === "GLOBAL" && result.applied?.campaign_created) {
        // 2026-09-08, real user ask: Approve on a "New campaign idea" now creates the
        // real campaign directly (services/campaign_service.py) -- no more form to fill
        // out separately. Show exactly what got created, same as a CAMPAIGN-scope apply.
        setAppliedResult(result.applied);
        setBusy(false);
      } else if (item.scope === "GLOBAL") {
        // Legacy fallback (shouldn't happen for a real proposal after the above fix, but
        // a GLOBAL item with no usable proposal still resolves cleanly either way).
        if (result.campaign_prefill) {
          onApproveGlobal?.({ ...result.campaign_prefill, suggestion: item.text }, item);
        }
        onResolved?.(item.id);
      } else if (result.applied) {
        // A real structural change landed on the real campaign row -- show exactly what,
        // don't just make the card vanish. Stays until the human closes it.
        setAppliedResult(result.applied);
        setBusy(false);
      } else {
        // A plain note with no proposal attached -- nothing to confirm, just resolve.
        onResolved?.(item.id);
      }
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  async function dismiss() {
    setBusy(true);
    setError(null);
    try {
      await api.dismissTodoItem(item.id);
      onResolved?.(item.id);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  if (appliedResult) {
    return (
      <div className="rounded-lg border border-good-600/40 bg-good-100 p-3">
        <div className="flex items-start justify-between gap-2">
          <span className="flex items-center gap-1.5 font-mono text-[9px] font-semibold uppercase tracking-wide text-good-700">
            <CheckCircle2 size={12} />
            {appliedResult.sent_email
              ? "Email sent"
              : appliedResult.campaign_created
                ? "Campaign created"
                : "Applied to this campaign"}
          </span>
          <button
            onClick={() => onResolved?.(item.id)}
            className="shrink-0 rounded-md p-1 text-good-700 hover:bg-good-100"
            aria-label="Close"
          >
            <X size={13} />
          </button>
        </div>
        <div className="mt-1.5 flex flex-col gap-1 text-xs text-ink-900">
          {appliedResult.sent_email && (
            <>
              <p>
                Sent to <b>{appliedResult.company_name || "this lead"}</b>
                {appliedResult.to ? ` (${appliedResult.to})` : ""}.
              </p>
              {appliedResult.subject && (
                <p className="text-ink-700">
                  <b>Subject:</b> {appliedResult.subject}
                </p>
              )}
            </>
          )}
          {appliedResult.status === "APPROVED" && (
            <p><b>Campaign status:</b> Marked approved</p>
          )}
          {appliedResult.campaign_created && (
            <p>
              <b>{appliedResult.name}</b> is live —{" "}
              <Link to={`/campaigns/${appliedResult.campaign_id}`} className="underline decoration-line underline-offset-2 hover:text-ink-900">
                open it
              </Link>
            </p>
          )}
          {appliedResult.target_segment && (
            <p>
              <b>Target set:</b> {industryLabel(appliedResult.target_segment) || "—"}
              {appliedResult.target_segment.location && ` in ${locationLabel(appliedResult.target_segment)}`}
            </p>
          )}
          {appliedResult.lead_count_goal != null && <p><b>Lead count goal set:</b> {appliedResult.lead_count_goal}</p>}
          {appliedResult.strategy_angle && <p><b>New angle set:</b> {appliedResult.strategy_angle}</p>}
          {appliedResult.email_render_mode && (
            <p><b>Email format set:</b> {appliedResult.email_render_mode === "TEXT" ? "Plain text" : "HTML template"}</p>
          )}
        </div>
      </div>
    );
  }

  const approveLabel = emailDraft
    ? "Approve & send"
    : item.scope === "GLOBAL"
    ? "Create campaign…"
    : "Approve";

  return (
    <div
      className={`rounded-lg border p-3 ${
        conflict ? "border-dashed border-alert-600 bg-alert-100" : "border-line bg-parchment-raised"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex flex-wrap items-center gap-1.5">
          <span
            className={`flex items-center gap-1 rounded-full px-2 py-0.5 font-mono text-[9px] font-semibold uppercase tracking-wide ${
              emailDraft
                ? "bg-ink-900 text-parchment-raised"
                : conflict
                ? "bg-alert-600 text-white"
                : "bg-parchment-raised-2 text-ink-700"
            }`}
          >
            {emailDraft ? <Mail size={9} /> : conflict ? <AlertTriangle size={9} /> : null}
            {item.label || "Note"}
          </span>
          {showSourceChip && (
            <span className="rounded-full bg-gold-100 px-2 py-0.5 font-mono text-[9px] font-semibold text-gold-700">
              {item.scope === "GLOBAL" ? item.product_title || "New campaign idea" : item.campaign_name || "Campaign"}
            </span>
          )}
          {item.confidence != null && !emailDraft && (
            <span
              title="How confident the AI is, based on real data volume/clarity"
              className={`rounded-full px-2 py-0.5 font-mono text-[9px] font-semibold ${
                item.confidence >= 0.7
                  ? "bg-good-100 text-good-700"
                  : item.confidence >= 0.4
                  ? "bg-gold-100 text-gold-700"
                  : "bg-parchment-raised-2 text-ink-500"
              }`}
            >
              {Math.round(item.confidence * 100)}% confidence
            </span>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          {/* 2026-09-07, user-flagged real gap: "Approve" implied it would DO something
              even for a pure observation with no proposal attached (e.g. "Discovery off"
              -- that switch lives in Settings, not on this campaign, so Approve had
              nothing to actually apply). Approve/Dismiss then behaved identically and
              silently, which is worse than confusing -- it looked like acting when it
              wasn't. A to-do with no real lever gets one honest "Got it" instead. */}
          {hasAction ? (
            <>
              <button
                onClick={dismiss}
                disabled={busy}
                className="rounded-md px-2.5 py-1.5 text-[11px] font-medium text-ink-500 hover:bg-parchment-raised-2 hover:text-ink-900 disabled:opacity-50"
              >
                {emailDraft ? "Not now" : "Dismiss"}
              </button>
              <button
                onClick={approve}
                disabled={busy}
                className="rounded-md bg-ink-900 px-3 py-1.5 text-[11px] font-semibold text-parchment-raised hover:opacity-90 disabled:opacity-50"
              >
                {busy ? (emailDraft ? "Sending…" : "Working…") : approveLabel}
              </button>
            </>
          ) : (
            <button
              onClick={dismiss}
              disabled={busy}
              title="Nothing here for the system to apply on its own -- this just clears it from your inbox"
              className="rounded-md bg-parchment-raised-2 px-3 py-1.5 text-[11px] font-semibold text-ink-700 hover:bg-line disabled:opacity-50"
            >
              {busy ? "Working…" : "Got it"}
            </button>
          )}
        </div>
      </div>

      <p className="mt-2 text-xs text-ink-700">{item.text}</p>

      {/* 2026-09-07, user's real catch: "system ne bola review ke liye bheja, kuch aya
          hi nahi todo me, kaise review karu?" -- a lead-scoped to-do now links straight to
          that lead's own page instead of leaving a human to hunt for it manually. */}
      {item.lead_id && (
        <Link
          to={`/leads/${item.lead_id}`}
          className="mt-2 inline-block text-[11px] font-medium text-gold-700 hover:text-gold-600 hover:underline"
        >
          Open {item.lead_company_name || "this lead"}'s page →
        </Link>
      )}

      {/* Option B (2026-09-08): QC-rejected email with a real draft -- show it plainly so
          Approve & send is a real review, not a blind click. */}
      {emailDraft && (
        <div className="mt-2.5 rounded-md border border-line bg-parchment p-3">
          <p className="font-mono text-[9px] font-semibold uppercase tracking-wide text-ink-500">
            Email to review
          </p>
          <p className="mt-1.5 text-sm font-semibold text-ink-900">
            <span className="font-normal text-ink-500">Subject: </span>
            {proposal.subject}
          </p>
          <p className="mt-2 whitespace-pre-wrap text-xs leading-relaxed text-ink-700">
            {proposal.body}
          </p>
          {proposal.qc_note && (
            <p className="mt-2.5 border-t border-line pt-2 text-[11px] leading-relaxed text-ink-500">
              Why AI hesitated: {proposal.qc_note}
            </p>
          )}
        </div>
      )}

      {proposal && !emailDraft && (
        <div className="mt-2 rounded-md border border-dashed border-gold-600 bg-gold-100 p-2.5">
          <span className="flex items-center gap-1.5 font-mono text-[9px] font-semibold uppercase tracking-wide text-gold-700">
            <Sparkles size={11} /> Structural change -- applies on Approve
          </span>
          <div className="mt-1.5 flex flex-col gap-1 text-xs text-ink-900">
            {proposal.target_segment && (
              <p>
                <b>Target:</b>{" "}
                {industryLabel(proposal.target_segment) || "—"}
                {proposal.target_segment.location && ` in ${locationLabel(proposal.target_segment)}`}
              </p>
            )}
            {proposal.lead_count_goal != null && <p><b>Lead count goal:</b> {proposal.lead_count_goal}</p>}
            {proposal.strategy_angle && <p><b>New angle:</b> {proposal.strategy_angle}</p>}
            {proposal.email_render_mode && (
              <p><b>Email format:</b> {proposal.email_render_mode === "TEXT" ? "Plain text" : "HTML template"}</p>
            )}
          </div>
        </div>
      )}

      {pushback && (
        <div className="mt-2 rounded-md border border-dashed border-alert-600 bg-alert-100 p-2.5">
          <span className="flex items-center gap-1.5 font-mono text-[9px] font-semibold uppercase tracking-wide text-alert-600">
            <MessageSquareWarning size={11} /> AI's honest take
          </span>
          <p className="mt-1 text-xs text-ink-900">{pushback}</p>
        </div>
      )}

      {error && <p className="mt-2 text-[11px] text-alert-600">{error}</p>}

      {showFeedback ? (
        <form onSubmit={submitFeedback} className="mt-2.5 flex flex-col gap-1.5">
          <input
            autoFocus
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder={
              emailDraft
                ? "e.g. remove pricing talk, make it shorter"
                : "e.g. isko formal karo, ek ROI line add karo"
            }
            className="rounded-md border border-line bg-parchment-raised px-2.5 py-1.5 text-xs text-ink-900 placeholder:text-ink-500 focus:border-gold-500 focus:outline-none"
          />
          <div className="flex items-center gap-2">
            <button
              type="submit"
              disabled={revising || !instruction.trim()}
              className="rounded-md bg-gold-600 px-3 py-1.5 text-[11px] font-semibold text-white hover:opacity-90 disabled:opacity-50"
            >
              {revising ? "Updating…" : emailDraft ? "Update email" : "Regenerate"}
            </button>
            <button
              type="button"
              onClick={() => setShowFeedback(false)}
              className="text-[11px] font-medium text-ink-500 hover:text-ink-900"
            >
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <button
          onClick={() => setShowFeedback(true)}
          className="mt-2.5 text-[11px] font-medium text-ink-500 hover:text-ink-900"
        >
          {emailDraft ? "Ask for a change" : "Give feedback"}
        </button>
      )}
    </div>
  );
}
