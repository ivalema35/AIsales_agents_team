import { useEffect, useState } from "react";
import LeadCard from "./LeadCard";
import { statusHex } from "../lib/statusColors";

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

const ROWS_PER_PAGE = 10;
// LeadCard's own steady-state height (px-2.5/py-2 padding + its two-line text block) --
// fixing the list area to exactly this many rows means the column is sized FOR a full
// page of 10 up front, not sized to the viewport and then hoping 10 rows happen to fit
// (which is what caused the internal scrollbar even on a full page before). Rows can
// still grow slightly if a send result banner appears (rare, transient), so the overflow
// is kept as a safety fallback, not removed -- it just won't fire in the normal case.
const ROW_HEIGHT_PX = 50;
const ROW_GAP_PX = 6;
const LIST_PADDING_PX = 16; // p-2 top + bottom
const LIST_HEIGHT_PX = ROWS_PER_PAGE * ROW_HEIGHT_PX + (ROWS_PER_PAGE - 1) * ROW_GAP_PX + LIST_PADDING_PX;

function KanbanColumn({ col }) {
  const [page, setPage] = useState(1);
  const totalPages = Math.max(1, Math.ceil(col.leads.length / ROWS_PER_PAGE));

  // Real leads keep arriving (15s poll) and filters can change the underlying set --
  // clamp down (not reset to 1) if the page someone was on no longer exists, so a filter
  // change that shrinks the list doesn't strand them on a blank page.
  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [totalPages, page]);

  const pageLeads = col.leads.slice((page - 1) * ROWS_PER_PAGE, page * ROWS_PER_PAGE);

  return (
    <div className="flex w-80 shrink-0 flex-col rounded-lg bg-white ring-1 ring-slate-200">
      <div className="flex items-center justify-between rounded-t-lg border-b border-slate-100 bg-white px-3 py-2.5">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: statusHex(col.key) }} />
          {col.label}
        </h3>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">
          {col.leads.length}
        </span>
      </div>

      <div className="flex flex-col gap-1.5 overflow-y-auto p-2" style={{ height: `${LIST_HEIGHT_PX}px` }}>
        {col.leads.length === 0 && (
          <p className="px-1 py-4 text-center text-xs text-slate-300">No leads</p>
        )}
        {pageLeads.map((lead) => (
          <LeadCard key={lead.id} lead={lead} />
        ))}
      </div>

      {/* Per-column Prev/Next -- browsing a status's full list stays right here on the
         Dashboard instead of bouncing out to the Leads page, no matter how many leads
         that status ends up holding once real traffic fills the pipeline. */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-slate-100 px-2 py-1.5">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="rounded px-2 py-1 text-xs font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-800 disabled:cursor-not-allowed disabled:opacity-30"
          >
            ‹ Prev
          </button>
          <span className="text-[11px] text-slate-400">Page {page} of {totalPages}</span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="rounded px-2 py-1 text-xs font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-800 disabled:cursor-not-allowed disabled:opacity-30"
          >
            Next ›
          </button>
        </div>
      )}
    </div>
  );
}

export default function PipelineKanban({ leads }) {
  const byStatus = COLUMNS.map((col) => {
    const colLeads = leads
      .filter((l) => l.status === col.key)
      // Newest first -- `updated_at` (not `created_at`) so "recent" means "recently
      // entered THIS stage," not "discovered a while ago." A lead sitting in SCORED for
      // days after a fresh (re)score should still surface above one that's been idle --
      // `created_at` alone would leave it buried under old DISCOVERED-era timestamps.
      // Score only breaks a tie between leads updated at the exact same moment.
      .sort((a, b) => {
        const byDate = b.updated_at.localeCompare(a.updated_at);
        if (byDate !== 0) return byDate;
        return (b.score?.score ?? -1) - (a.score?.score ?? -1);
      });
    return { ...col, leads: colLeads };
  }); // every stage always shows, even at 0 -- the user wants the full pipeline shape
      // visible at a glance, not just the stages that happen to be occupied right now.

  return (
    <div className="flex gap-4 overflow-x-auto rounded-xl border border-slate-200 bg-slate-50 p-3">
      {byStatus.map((col) => (
        <KanbanColumn key={col.key} col={col} />
      ))}
    </div>
  );
}
