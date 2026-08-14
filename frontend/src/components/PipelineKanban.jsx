import LeadCard from "./LeadCard";

// Column order matches the pipeline's actual state progression (MASTER PRD leads.status).
// Terminal states (CONVERTED, REJECTED) are intentionally left off the board -- this
// view is about watching leads MOVE through the pipeline, not archiving. HOT_LEAD IS
// shown (unlike the original design) -- it's driven by two separate flows now, a
// score-based claim AND Step 4.3's inbound-reply escalation, so it's a common, active
// state a lead can sit in, not a rare terminal one; hiding it made real escalated leads
// disappear from the board entirely.
const COLUMNS = [
  { key: "DISCOVERED", label: "Discovered" },
  { key: "ENRICHED", label: "Enriched" },
  { key: "REVIEWED", label: "Reviewed" },
  { key: "SCORED", label: "Scored" },
  { key: "OUTREACHING", label: "Outreaching" },
  { key: "OUTREACHED", label: "Outreached" },
  { key: "ENGAGED", label: "Engaged" },
  { key: "HOT_LEAD", label: "Hot / Escalated" },
];

export default function PipelineKanban({ leads }) {
  const byStatus = COLUMNS.map((col) => ({
    ...col,
    leads: leads.filter((l) => l.status === col.key),
  }));

  return (
    <div className="flex gap-4 overflow-x-auto rounded-xl border border-slate-200 bg-slate-50 p-3">
      {byStatus.map((col) => (
        <div key={col.key} className="flex w-72 shrink-0 flex-col rounded-lg bg-white ring-1 ring-slate-200">
          <div className="flex items-center justify-between rounded-t-lg border-b border-slate-100 bg-white px-3 py-2.5">
            <h3 className="text-sm font-semibold text-slate-700">{col.label}</h3>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">
              {col.leads.length}
            </span>
          </div>
          <div className="flex flex-col gap-2 overflow-y-auto p-2" style={{ maxHeight: "calc(100vh - 320px)", minHeight: "120px" }}>
            {col.leads.length === 0 && (
              <p className="px-1 py-4 text-center text-xs text-slate-300">No leads</p>
            )}
            {col.leads.map((lead) => (
              <LeadCard key={lead.id} lead={lead} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
