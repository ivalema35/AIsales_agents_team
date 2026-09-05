import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { MessageCircle, Mail, CheckCircle2 } from "lucide-react";
import { api } from "../api/client";
import { relativeTime } from "../lib/relativeTime";

function ChannelChip({ channel }) {
  const isWa = channel === "WHATSAPP";
  const Icon = isWa ? MessageCircle : Mail;
  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-medium ${
        isWa ? "bg-good-100 text-good-600" : "bg-parchment-raised-2 text-ink-500"
      }`}
    >
      <Icon size={10} /> {isWa ? "WhatsApp" : "Email"}
    </span>
  );
}

// Phase 21 (2026-09-05) -- the old "Ready to claim" (amber) section was removed: it's
// redundant with the AI Manager Inbox's own "N leads ready to dispatch" to-do signal
// (Step 18.1's READY_TO_DISPATCH_COUNT), and the operator asked for the Inbox to take
// this panel's old top-of-Dashboard spot. This is now a single, urgent, red strip for
// the one signal that's genuinely time-sensitive and unrelated to campaign strategy: a
// real lead just replied showing interest, and nobody has acted on it yet.
//
// needs_response: a lead just replied showing real interest and got auto-escalated to
// HOT_LEAD by Step 4.3's classifier. "Mark as Contacted" moves it to ENGAGED, which is
// what makes it drop off this list -- there's no separate "resolved" flag, the status
// change itself is the signal.
export default function AlertsPanel({ alerts, onContacted }) {
  const navigate = useNavigate();
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState(null);

  const needsResponse = alerts?.needs_response || [];

  function openLead(leadId) {
    navigate(`/leads/${leadId}`);
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
    <div className="rounded-xl border border-alert-600/20 bg-alert-100/60 p-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="h-2 w-2 rounded-full bg-alert-600" />
        <h2 className="font-display text-sm font-semibold text-alert-700">
          Just replied — needs response
        </h2>
        <span className="rounded-full bg-alert-100 px-2 py-0.5 text-xs font-semibold text-alert-700">
          {needsResponse.length}
        </span>
      </div>

      {error && <p className="mb-2 text-xs text-alert-600">{error}</p>}
      {needsResponse.length === 0 ? (
        <p className="text-sm text-alert-700/60">Nothing waiting right now.</p>
      ) : (
        <div className="flex flex-col gap-2">
          {needsResponse.map((a) => (
            <div
              key={a.lead_id}
              role="link"
              tabIndex={0}
              onClick={() => openLead(a.lead_id)}
              onKeyDown={(e) => { if (e.key === "Enter") openLead(a.lead_id); }}
              className="cursor-pointer rounded-lg border-l-[3px] border-alert-600 bg-parchment-raised p-3 shadow-sm ring-1 ring-alert-600/20 transition-shadow hover:shadow focus:outline-none focus:ring-2 focus:ring-alert-600/30"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink-900">{a.company_name}</p>
                  {a.source === "INTEREST_CLICK" ? (
                    <p className="mt-1 flex items-center gap-1 text-xs font-medium text-good-700">
                      <CheckCircle2 size={12} /> Clicked "Yes, tell me more" on the outreach email
                    </p>
                  ) : (
                    <p className="mt-1 line-clamp-2 text-xs italic leading-relaxed text-ink-700">"{a.message}"</p>
                  )}
                  <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-[11px] text-ink-500">
                    {a.source === "INTEREST_CLICK" ? (
                      <span className="rounded bg-good-100 px-1.5 py-0.5 font-medium text-good-600">
                        DECLARED YES
                      </span>
                    ) : (
                      <span className="rounded bg-alert-100 px-1.5 py-0.5 font-medium text-alert-600">
                        {a.intent.replace(/_/g, " ")}
                      </span>
                    )}
                    <ChannelChip channel={a.channel} />
                    <span className="font-mono">{relativeTime(a.replied_at)}</span>
                  </div>
                </div>
                <button
                  onClick={(e) => markContacted(a.lead_id, e)}
                  disabled={busyId === a.lead_id}
                  className="shrink-0 rounded-md bg-alert-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:opacity-90 disabled:opacity-50"
                >
                  {busyId === a.lead_id ? "Marking…" : "Mark as Contacted"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
