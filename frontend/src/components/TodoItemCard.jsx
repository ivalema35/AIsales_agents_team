import { useState } from "react";
import { AlertTriangle, CheckCircle2, MessageSquareWarning, Sparkles, X } from "lucide-react";
import { api } from "../api/client";
import { industryLabel } from "../lib/targetSegment";

// Phase 21 -- a todo item whose label is genuinely about a real signal conflict (Step
// 20.2) gets distinct, more urgent styling than an ordinary note, so a human's eye lands
// on it first. Matching by label text, not a fixed enum -- the strategist's labels are
// free-text by design (Step 18.1), "Conflict"/"Tension" are just what it tends to write.
function isConflictLabel(label) {
  const l = (label || "").toLowerCase();
  return l.includes("conflict") || l.includes("tension");
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
  // GLOBAL always has a real action (opens the campaign-creation form); a CAMPAIGN item
  // only has one when it actually carries a structural proposal to apply -- a plain
  // observation (e.g. "Discovery off", a Copy note) has nothing for Approve to do.
  const hasAction = item.scope === "GLOBAL" || !!proposal;

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
      if (item.scope === "GLOBAL") {
        // Opening the pre-filled campaign form IS the confirmation here -- nothing was
        // applied server-side for a GLOBAL item, so there's nothing else to show inline.
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
            <CheckCircle2 size={12} /> Applied to this campaign
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
          {appliedResult.target_segment && (
            <p>
              <b>Target set:</b> {industryLabel(appliedResult.target_segment) || "—"}
              {appliedResult.target_segment.location && ` in ${appliedResult.target_segment.location}`}
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
              conflict ? "bg-alert-600 text-white" : "bg-parchment-raised-2 text-ink-700"
            }`}
          >
            {conflict && <AlertTriangle size={9} />}
            {item.label || "Note"}
          </span>
          {showSourceChip && (
            <span className="rounded-full bg-gold-100 px-2 py-0.5 font-mono text-[9px] font-semibold text-gold-700">
              {item.scope === "GLOBAL" ? item.product_title || "New campaign idea" : item.campaign_name || "Campaign"}
            </span>
          )}
          {item.confidence != null && (
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
                Dismiss
              </button>
              <button
                onClick={approve}
                disabled={busy}
                className="rounded-md bg-ink-900 px-3 py-1.5 text-[11px] font-semibold text-parchment-raised hover:opacity-90 disabled:opacity-50"
              >
                {busy ? "Working…" : item.scope === "GLOBAL" ? "Create campaign…" : "Approve"}
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

      {proposal && (
        <div className="mt-2 rounded-md border border-dashed border-gold-600 bg-gold-100 p-2.5">
          <span className="flex items-center gap-1.5 font-mono text-[9px] font-semibold uppercase tracking-wide text-gold-700">
            <Sparkles size={11} /> Structural change -- applies on Approve
          </span>
          <div className="mt-1.5 flex flex-col gap-1 text-xs text-ink-900">
            {proposal.target_segment && (
              <p>
                <b>Target:</b>{" "}
                {industryLabel(proposal.target_segment) || "—"}
                {proposal.target_segment.location && ` in ${proposal.target_segment.location}`}
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
            placeholder="e.g. isko formal karo, ek ROI line add karo"
            className="rounded-md border border-line bg-parchment-raised px-2.5 py-1.5 text-xs text-ink-900 placeholder:text-ink-500 focus:border-gold-500 focus:outline-none"
          />
          <div className="flex items-center gap-2">
            <button
              type="submit"
              disabled={revising || !instruction.trim()}
              className="rounded-md bg-gold-600 px-3 py-1.5 text-[11px] font-semibold text-white hover:opacity-90 disabled:opacity-50"
            >
              {revising ? "Revising…" : "Regenerate"}
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
          Give feedback
        </button>
      )}
    </div>
  );
}
