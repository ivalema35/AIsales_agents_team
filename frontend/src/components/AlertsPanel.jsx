import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { MessageCircle, Mail } from "lucide-react";
import { api } from "../api/client";
import { relativeTime } from "../lib/relativeTime";

// Ready-to-claim can genuinely run to dozens once discovery scales -- same "capped +
// link to the full, searchable Leads page" pattern used everywhere else in the CRM
// (PipelineKanban's per-column pagination, ReadyToSend before it), so this panel stays a
// fixed, glanceable size instead of growing into its own nested-scrolling list.
const CLAIM_PREVIEW_CAP = 5;

function ChannelChip({ channel }) {
  const isWa = channel === "WHATSAPP";
  const Icon = isWa ? MessageCircle : Mail;
  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-medium ${
        isWa ? "bg-emerald-50 text-emerald-600" : "bg-slate-100 text-slate-500"
      }`}
    >
      <Icon size={10} /> {isWa ? "WhatsApp" : "Email"}
    </span>
  );
}

// Polls /api/v1/alerts (MASTER PRD §5 Step 4.4). Two sections, not one merged list, and
// deliberately two DIFFERENT accent colors (red vs amber) -- the original single-red
// treatment made a 13-deep "ready to claim" list read with the same fire-alarm urgency
// as the one lead that's actually sitting there waiting on a reply, which buries the
// real priority (found live, user feedback on a real screenshot).
//
// - needs_response (red): a lead just replied showing real interest and got
//   auto-escalated to HOT_LEAD by Step 4.3's classifier -- nobody has acted on it yet.
//   "Mark as Contacted" moves it to ENGAGED, which is what makes it drop off this list --
//   there's no separate "resolved" flag, the status change itself is the signal.
// - ready_to_claim (amber): scored HOT by the scoring agent, not yet picked up by anyone.
//   Worth knowing about, not on fire. "Claim" moves it to HOT_LEAD (the original v1
//   behavior).
export default function AlertsPanel({ alerts, onClaimed, onContacted }) {
  const navigate = useNavigate();
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState(null);

  const needsResponse = alerts?.needs_response || [];
  const readyToClaim = alerts?.ready_to_claim || [];
  const total = needsResponse.length + readyToClaim.length;

  function openLead(leadId) {
    navigate(`/leads/${leadId}`);
  }

  async function claim(leadId, e) {
    // Card itself is now clickable (opens the lead) -- stopPropagation is what keeps a
    // Claim click from also firing the card's own navigation.
    e.stopPropagation();
    setBusyId(leadId);
    setError(null);
    try {
      await api.patchLeadStatus(leadId, "HOT_LEAD");
      onClaimed?.(leadId);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  async function markContacted(leadId, e) {
    e.stopPropagation();
    setBusyId(leadId);
    setError(null);
    try {
      await api.patchLeadStatus(leadId, "ENGAGED");
      onContacted?.(leadId);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="rounded-xl border border-red-100 bg-red-50/60 p-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="h-2 w-2 rounded-full bg-red-500" />
        <h2 className="text-sm font-semibold text-red-900">Needs your attention</h2>
        <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700">{total}</span>
      </div>

      {error && <p className="mb-2 text-xs text-red-600">{error}</p>}
      {total === 0 && <p className="text-sm text-red-700/60">Nothing waiting right now.</p>}

      {needsResponse.length > 0 && (
        <div className={readyToClaim.length > 0 ? "mb-4" : ""}>
          <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-red-700">
            Just replied — needs response <span className="text-red-400">({needsResponse.length})</span>
          </p>
          <div className="flex flex-col gap-2">
            {needsResponse.map((a) => (
              <div
                key={a.lead_id}
                role="link"
                tabIndex={0}
                onClick={() => openLead(a.lead_id)}
                onKeyDown={(e) => { if (e.key === "Enter") openLead(a.lead_id); }}
                className="cursor-pointer rounded-lg border-l-[3px] border-red-500 bg-white p-3 shadow-sm ring-1 ring-red-100 transition-shadow hover:shadow focus:outline-none focus:ring-2 focus:ring-red-300"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-900">{a.company_name}</p>
                    <p className="mt-1 line-clamp-2 text-xs italic leading-relaxed text-slate-600">"{a.message}"</p>
                    <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-[11px] text-slate-400">
                      <span className="rounded bg-red-50 px-1.5 py-0.5 font-medium text-red-600">
                        {a.intent.replace(/_/g, " ")}
                      </span>
                      <ChannelChip channel={a.channel} />
                      <span>{relativeTime(a.replied_at)}</span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => markContacted(a.lead_id, e)}
                    disabled={busyId === a.lead_id}
                    className="shrink-0 rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-red-700 disabled:opacity-50"
                  >
                    {busyId === a.lead_id ? "Marking…" : "Mark as Contacted"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {readyToClaim.length > 0 && (
        <div>
          <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-amber-700">
            Ready to claim <span className="text-amber-500">({readyToClaim.length})</span>
          </p>
          <div className="flex flex-col gap-2">
            {readyToClaim.slice(0, CLAIM_PREVIEW_CAP).map((a) => (
              <div
                key={a.lead_id}
                role="link"
                tabIndex={0}
                onClick={() => openLead(a.lead_id)}
                onKeyDown={(e) => { if (e.key === "Enter") openLead(a.lead_id); }}
                className="flex cursor-pointer items-center justify-between gap-3 rounded-lg border-l-[3px] border-amber-400 bg-white p-3 shadow-sm ring-1 ring-amber-100 transition-shadow hover:shadow focus:outline-none focus:ring-2 focus:ring-amber-300"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-900">{a.company_name}</p>
                  <p className="mt-0.5 truncate text-xs text-slate-500">{a.justification}</p>
                  <div className="mt-1.5 flex items-center gap-2 text-[11px] text-slate-400">
                    <span className="rounded bg-amber-50 px-1.5 py-0.5 font-semibold text-amber-700">Score {a.score}</span>
                    {a.primary_email && <span className="truncate">{a.primary_email}</span>}
                    {a.primary_phone && <span>{a.primary_phone}</span>}
                  </div>
                </div>
                <button
                  onClick={(e) => claim(a.lead_id, e)}
                  disabled={busyId === a.lead_id}
                  className="shrink-0 rounded-md bg-amber-500 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-amber-600 disabled:opacity-50"
                >
                  {busyId === a.lead_id ? "Claiming…" : "Claim"}
                </button>
              </div>
            ))}
          </div>
          {readyToClaim.length > CLAIM_PREVIEW_CAP && (
            <Link
              to="/leads?tier=HOT"
              className="mt-2 block rounded-md border border-dashed border-amber-200 py-2 text-center text-xs font-medium text-amber-700 transition-colors hover:border-amber-300 hover:bg-amber-50"
            >
              View all {readyToClaim.length} in Leads →
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
