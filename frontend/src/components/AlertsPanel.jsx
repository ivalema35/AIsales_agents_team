import { useState } from "react";
import { api } from "../api/client";

// Polls /api/v1/alerts (MASTER PRD §5 Step 4.4). "Claiming" a HOT lead just moves its
// status to HOT_LEAD via the existing PATCH endpoint -- once claimed, the backend's own
// _EXCLUDED_STATUSES filter drops it from this list on the next poll.
export default function AlertsPanel({ alerts, onClaimed }) {
  const [claimingId, setClaimingId] = useState(null);
  const [error, setError] = useState(null);

  async function claim(leadId) {
    setClaimingId(leadId);
    setError(null);
    try {
      await api.patchLeadStatus(leadId, "HOT_LEAD");
      onClaimed?.(leadId);
    } catch (err) {
      setError(err.message);
    } finally {
      setClaimingId(null);
    }
  }

  return (
    <div className="rounded-xl border border-red-100 bg-red-50/60 p-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="h-2 w-2 rounded-full bg-red-500" />
        <h2 className="text-sm font-semibold text-red-900">HOT leads needing attention</h2>
        <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700">
          {alerts.length}
        </span>
      </div>

      {error && <p className="mb-2 text-xs text-red-600">{error}</p>}
      {alerts.length === 0 && (
        <p className="text-sm text-red-700/60">No HOT leads waiting right now.</p>
      )}

      <div className="flex max-h-96 flex-col gap-2 overflow-y-auto">
        {alerts.map((a) => (
          <div
            key={a.lead_id}
            className="flex items-center justify-between gap-3 rounded-lg bg-white p-3 shadow-sm ring-1 ring-slate-100"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-slate-900">{a.company_name}</p>
              <p className="mt-0.5 truncate text-xs text-slate-500">{a.justification}</p>
              <div className="mt-1.5 flex items-center gap-2 text-[11px] text-slate-400">
                <span className="rounded bg-slate-50 px-1.5 py-0.5 font-medium">Score {a.score}</span>
                {a.primary_email && <span className="truncate">{a.primary_email}</span>}
                {a.primary_phone && <span>{a.primary_phone}</span>}
              </div>
            </div>
            <button
              onClick={() => claim(a.lead_id)}
              disabled={claimingId === a.lead_id}
              className="shrink-0 rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              {claimingId === a.lead_id ? "Claiming…" : "Claim"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
