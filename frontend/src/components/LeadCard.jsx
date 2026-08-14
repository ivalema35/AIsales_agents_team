import { useState } from "react";
import { api } from "../api/client";

const TIER_STYLES = {
  HOT: "bg-red-50 text-red-700 ring-1 ring-inset ring-red-200",
  WARM: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200",
  COLD: "bg-slate-100 text-slate-500 ring-1 ring-inset ring-slate-200",
};

export default function LeadCard({ lead }) {
  const tier = lead.score?.tier;
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null); // { EMAIL: {...}, WHATSAPP: {...} } | { error }
  // OUTREACHING (from the server, via props) backs up local `sending` state -- when a
  // send is in flight the lead's status flips to OUTREACHING almost immediately, which
  // moves its Kanban column and REMOUNTS this card with fresh (sending=false) state, so
  // local state alone can't stop a second click during that window from firing a real
  // duplicate send. See tracker.md Step 4.4 duplicate-outreach bug.
  const sendInFlight = sending || lead.status === "OUTREACHING";

  async function sendOutreach(e) {
    e.stopPropagation();
    const ok = window.confirm(
      `Send REAL outreach to ${lead.company_name} now (${lead.primary_email || "no email"} / ` +
      `${lead.primary_phone || "no phone"})? This is a real send, not a simulation.`
    );
    if (!ok) return;

    setSending(true);
    setResult(null);
    try {
      const res = await api.triggerOutreach(lead.id);
      setResult(res.results);
    } catch (err) {
      setResult({ error: err.message });
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium leading-snug text-slate-900 line-clamp-2">{lead.company_name}</p>
        {tier && (
          <span className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold ${TIER_STYLES[tier] || TIER_STYLES.COLD}`}>
            {tier}
          </span>
        )}
      </div>

      {lead.region_location && (
        <p className="mt-1 truncate text-xs text-slate-400">{lead.region_location}</p>
      )}

      {lead.score && (
        <p className="mt-2 text-xs leading-relaxed text-slate-600 line-clamp-3">{lead.score.justification}</p>
      )}

      <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-2 text-[11px] text-slate-400">
        <span>{lead.score ? `Score ${lead.score.score}` : "Not scored"}</span>
        <span className="flex gap-2">
          {lead.primary_email && <span className="rounded bg-slate-50 px-1.5 py-0.5">Email</span>}
          {lead.primary_phone && <span className="rounded bg-slate-50 px-1.5 py-0.5">Phone</span>}
        </span>
      </div>

      {lead.score && (lead.primary_email || lead.primary_phone) && (
        <button
          onClick={sendOutreach}
          disabled={sendInFlight}
          className="mt-2 w-full rounded-md bg-slate-800 py-1.5 text-xs font-medium text-white hover:bg-slate-900 disabled:opacity-50"
        >
          {sendInFlight ? "Sending…" : "Send Outreach Now"}
        </button>
      )}

      {result && !result.error && (
        <div className="mt-2 space-y-0.5 text-[11px]">
          {Object.entries(result).map(([channel, r]) => (
            <p key={channel} className={r.status === "SENT" ? "text-emerald-600" : "text-amber-600"}>
              {channel}: {r.status === "SENT" ? "Sent ✓" : `Escalated (${r.reason || "needs review"})`}
            </p>
          ))}
        </div>
      )}
      {result?.error && <p className="mt-2 text-[11px] text-red-600">{result.error}</p>}
    </div>
  );
}
