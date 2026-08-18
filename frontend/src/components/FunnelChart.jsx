import { Link } from "react-router-dom";
import { statusHex, statusBadgeClass } from "../lib/statusColors";

// Current pipeline distribution -- how many leads are sitting at each status RIGHT NOW
// (not cumulative). Each stage uses ITS OWN fixed color from statusColors.js (the same
// map every other status badge in the app reads from -- Kanban, LeadCard, LeadDetail),
// not a single sequential ramp, so "SCORED" is the same blue everywhere in the CRM.
// 4px rounded bar-ends, value labeled at the tip. Currently used by Analytics, fed from
// the `/analytics/funnel` API -- pulled into its own component (not inlined in
// Analytics.jsx) so a future second consumer reuses this exact visualization instead of
// a redrawn one that could drift out of sync.
//
// `getHref(stage)` is optional -- when given, each row becomes a link; omit it for a
// non-interactive read.
export default function FunnelChart({ data, getHref }) {
  if (!data) return null;
  const max = Math.max(1, ...data.stages.map((s) => s.count));
  return (
    <div className="flex flex-col gap-2.5">
      {data.stages.map((s) => {
        // A real minimum width for any nonzero count -- SCORED (329) otherwise dwarfs
        // OUTREACHED/HOT_LEAD (1 each) down to an invisible sliver on a linear scale,
        // which reads as indistinguishable from the genuinely-zero stages. The minimum
        // is well above the bar's own height (16px) so a small value still reads as a
        // short BAR, not a round blob -- a 3% minimum on a wide track measured almost
        // as tall as it was wide and looked like a dot (found live). Zero stages are
        // dimmed (not hidden) so the eye lands on stages that actually have leads.
        const pct = (s.count / max) * 100;
        const barWidth = s.count > 0 ? Math.max(pct, 10) : 0;
        const isEmpty = s.count === 0;
        const Row = getHref && s.count > 0 ? Link : "div";
        const rowProps = getHref && s.count > 0 ? { to: getHref(s.stage) } : {};
        return (
          <Row
            key={s.stage}
            {...rowProps}
            className={`group flex items-center gap-3 ${isEmpty ? "opacity-40" : ""} ${
              getHref && s.count > 0 ? "-mx-1 rounded-md px-1 py-0.5 transition-colors hover:bg-slate-50" : ""
            }`}
          >
            <span
              className={`w-28 shrink-0 truncate rounded-full px-2 py-0.5 text-center text-[11px] font-semibold ${statusBadgeClass(s.stage)}`}
            >
              {s.stage.replace(/_/g, " ")}
            </span>
            <div className="h-4 flex-1 overflow-hidden rounded-md bg-slate-100">
              {/* Mark spec: bar grows from a square baseline, only the data-end (right)
                 gets a 4px round -- rounding BOTH ends turned a short/small-value bar
                 into a blob/circle instead of a recognizably short bar (found live). */}
              <div
                className="h-full rounded-r-[4px] transition-all duration-300 ease-out"
                style={{ width: `${barWidth}%`, backgroundColor: statusHex(s.stage) }}
                title={`${s.stage.replace(/_/g, " ")}: ${s.count} lead${s.count === 1 ? "" : "s"}`}
              />
            </div>
            <span className="w-12 shrink-0 text-right text-xs font-semibold tabular-nums text-slate-700">{s.count}</span>
          </Row>
        );
      })}
      {data.rejected > 0 && (
        <p className="mt-1 text-xs text-slate-400">
          + {data.rejected} rejected (dropped out, not part of the ordered funnel above)
        </p>
      )}
    </div>
  );
}
