import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Send, BellOff } from "lucide-react";
import { api } from "../api/client";
import Badge from "./ui/Badge";
import { useConfirm } from "../lib/ConfirmContext";
import { useToast } from "../lib/ToastContext";
import { intentBadgeClass } from "../lib/intentColors";
import { TIER_BG, TIER_BORDER } from "../lib/tierColors";
import { relativeTime } from "../lib/relativeTime";

// Compact pipeline-board row -- deliberately NOT the old tall card (name + region +
// AI-justification paragraph + score/contact chips + full-width button). At real volume
// (hundreds of leads in one column) that height meant only 2-3 leads were visible at
// once, forcing constant scrolling and making the board unusable as an overview (found
// live, user feedback: "data achese visible ho"). This is ~1/4 the height -- name,
// region + score on one compact block, tier + a one-click send icon on the side. The
// full AI justification/contact detail already lives one click away on Lead Detail,
// which is exactly what this row links to -- nothing here is lost, just deferred.
export default function LeadCard({ lead }) {
  const tier = lead.score?.tier;
  // For an already-escalated lead, WHY it's hot (the reply's intent) is more useful
  // than the scoring-time tier badge -- "82 · HOT" told you nothing you didn't already
  // know from the "Hot / Escalated" column it's sitting in (user feedback, real
  // screenshot). Falls back to the tier badge for a HOT_LEAD claimed manually (no reply
  // behind it, so no intent exists).
  const intent = lead.status === "HOT_LEAD" ? lead.latest_reply_intent : null;
  const navigate = useNavigate();
  const confirm = useConfirm();
  const toast = useToast();
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null); // { EMAIL: {...}, WHATSAPP: {...} }
  // OUTREACHING (from the server, via props) backs up local `sending` state -- when a
  // send is in flight the lead's status flips to OUTREACHING almost immediately, which
  // moves its Kanban column and REMOUNTS this card with fresh (sending=false) state, so
  // local state alone can't stop a second click during that window from firing a real
  // duplicate send. See tracker.md Step 4.4 duplicate-outreach bug.
  const sendInFlight = sending || lead.status === "OUTREACHING";
  // A suppressed lead's real send would silently no-op anyway (suppression.py's
  // is_suppressed() check runs immediately before every send, unconditionally) -- not
  // offering the button at all is more honest than a button that looks like it'll work.
  const canSend = lead.score && (lead.primary_email || lead.primary_phone) && !lead.is_suppressed;

  // Carries its Kanban column's status along so the detail page's own Prev/Next walks
  // through that same column, not the whole unfiltered table.
  function openLead() {
    navigate(`/leads/${lead.id}?status=${lead.status}`);
  }

  async function sendOutreach(e) {
    // Send button sits INSIDE the now fully-clickable card -- stopPropagation here is what
    // keeps a send click from also firing the card's own openLead() navigation.
    e?.stopPropagation?.();
    // force: true by default -- see LeadDetail.jsx's sendOutreach for the full reasoning.
    // Still requires a real contact channel, still goes through QC + suppression.
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
    setResult(null);
    try {
      const res = await api.triggerOutreach(lead.id, { force: true });
      setResult(res.results);
    } catch (err) {
      toast.error(err.message.replace(/^\d+\s*/, "").replace(/^\["|"\]$/g, ""), {
        duration: 6000,
      });
    } finally {
      setSending(false);
    }
  }

  return (
    <div
      role="link"
      tabIndex={0}
      onClick={openLead}
      onKeyDown={(e) => { if (e.key === "Enter") openLead(); }}
      className={`min-h-[50px] cursor-pointer rounded-md border border-slate-100 px-2.5 py-2 shadow-sm transition-all hover:-translate-y-px hover:border-slate-300 hover:shadow focus:outline-none focus:ring-2 focus:ring-slate-300 ${
        lead.is_suppressed
          ? "border-l-[3px] bg-slate-100"
          : tier ? `${TIER_BG[tier]} border-l-[3px]` : "bg-white"
      }`}
      style={
        lead.is_suppressed
          ? { borderLeftColor: "#94a3b8" }
          : tier ? { borderLeftColor: TIER_BORDER[tier] } : undefined
      }
    >
      {/* Opted-out overrides everything else -- whatever tier/intent this lead also
         has, "we can never contact them again" is the fact that matters most, and
         before this it had NO visible signal anywhere in the CRM (found live: the only
         way to discover it was opening the conversation and noticing intent='STOP'). */}
      {lead.is_suppressed && (
        <div className="mb-1 flex items-center gap-1 text-[10px] font-semibold text-slate-500">
          <BellOff size={11} /> Opted out -- do not contact
        </div>
      )}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-medium leading-snug text-slate-800">{lead.company_name}</p>
          {/* flex row, not one truncated string -- a single `truncate` on "region · time"
             clips the WHOLE line at the container edge, so a long region silently ate the
             time suffix entirely (found live: "1d ago" never rendered behind a long
             address). Region gets the shrinking flex-1 slot; time is shrink-0 so it always
             stays visible regardless of how long the region text is. Still one line --
             PipelineKanban.jsx's column height is computed from this card's exact fixed
             height (ROW_HEIGHT_PX); a second line here would silently break that math. */}
          <p className="mt-0.5 flex items-baseline gap-1 text-[11px] leading-snug text-slate-500">
            <span className="min-w-0 truncate">{lead.region_location || "No region"}</span>
            {lead.updated_at && <span className="shrink-0">· {relativeTime(lead.updated_at)}</span>}
          </p>
        </div>
        {/* One right-hand cluster, top-aligned with the name -- score, tier, and the
           send action together instead of the tier signal repeating (a badge here AND
           a color strip elsewhere) and score fighting the region for the same line,
           which is what made the row read as cluttered/misaligned before. */}
        <div className="flex shrink-0 items-center gap-1.5">
          {lead.score && (
            <span className="rounded bg-white/80 px-1.5 py-0.5 text-[10px] font-semibold tabular-nums text-slate-600">
              {lead.score.score}
            </span>
          )}
          {intent ? (
            <span
              title={lead.latest_reply_message || undefined}
              className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ring-inset ${intentBadgeClass(intent)}`}
            >
              {intent.replace(/_/g, " ")}
            </span>
          ) : (
            tier && <Badge variant={tier}>{tier}</Badge>
          )}
          {canSend && (
            <button
              onClick={sendOutreach}
              disabled={sendInFlight}
              title={sendInFlight ? "Sending…" : "Send Outreach Now"}
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-slate-500 transition-colors hover:bg-white hover:text-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Send size={13} />
            </button>
          )}
        </div>
      </div>

      {result && (
        <div className="mt-1.5 flex flex-wrap gap-x-3 text-[10px]">
          {Object.entries(result).map(([channel, r]) => (
            <span key={channel} className={r.status === "SENT" ? "text-emerald-600" : "text-amber-600"}>
              {channel}: {r.status === "SENT" ? "Sent ✓" : `Escalated (${r.reason || "needs review"})`}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
