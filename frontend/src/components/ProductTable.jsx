import Badge from "./ui/Badge";

// Tier hue-per-slot, reused from the shared status/tier badge system elsewhere in the
// CRM (LeadDetail's ScoreCard, Badge.jsx) so HOT/WARM/COLD read as the same color here
// as everywhere else -- not a table-local palette.
const TIER_BAR_COLORS = { HOT: "#dc2626", WARM: "#d97706", COLD: "#cbd5e1" };
const TIER_ORDER = ["HOT", "WARM", "COLD"];

// A count of zero is not information -- it's the absence of it, and a table where most
// cells read "0" reads as broken more than it reads as empty. A muted dash says "none"
// without competing for attention against the real counts on rows that have activity.
function TierBadge({ variant, count }) {
  if (!count) return <span className="text-slate-300">—</span>;
  return <Badge variant={variant}>{count}</Badge>;
}

// Compact stacked bar under the product name -- at-a-glance tier mix (magnitude +
// composition) so the reader isn't cross-referencing three separate columns to see
// whether a product's leads skew hot or cold. 1px surface gaps between segments per
// the dataviz skill's mark spec (never a border to separate touching marks). Always
// renders the track (even at total=0, as a flat empty groove) -- returning null for
// empty products made those rows visibly SHORTER than the rest, an inconsistent
// rhythm down the table that read as broken rather than just "no data yet".
function TierDistributionBar({ tierCounts, total }) {
  return (
    <div className="mt-1.5 flex h-1.5 w-28 gap-px overflow-hidden rounded-full bg-slate-100">
      {total > 0 &&
        TIER_ORDER.map((t) => {
          const count = tierCounts[t] || 0;
          if (!count) return null;
          return (
            <span
              key={t}
              className="h-full first:rounded-l-full last:rounded-r-full"
              style={{ width: `${(count / total) * 100}%`, backgroundColor: TIER_BAR_COLORS[t] }}
              title={`${t}: ${count}`}
            />
          );
        })}
    </div>
  );
}

// Fixed per-column widths (colgroup + table-fixed) instead of the browser's default
// content-fit auto layout -- auto layout let the narrow numeric columns hug their
// content and dumped ALL the leftover width into a single dead gap between Product and
// Country, which read as a layout bug. Fixed widths spread that space evenly instead.
const PRODUCT_COL_WIDTHS = ["32%", "9%", "9%", "9%", "9%", "9%", "11.5%", "11.5%"];

// Its own file (not inlined in Analytics.jsx) so the Dashboard's pinnable "By product"
// widget renders the exact same table, not a redrawn copy that could drift out of sync.
export default function ProductTable({ rows }) {
  if (!rows) return null;
  return (
    <div className="overflow-x-auto">
      <table className="w-full table-fixed text-left text-xs">
        <colgroup>
          {PRODUCT_COL_WIDTHS.map((w, i) => (
            <col key={i} style={{ width: w }} />
          ))}
        </colgroup>
        <thead>
          <tr className="border-b border-slate-200 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            <th className="py-2.5 pr-3">Product</th>
            <th className="py-2.5 pr-3">Country</th>
            <th className="py-2.5 pr-3 text-right">Leads</th>
            <th className="py-2.5 pr-3 text-right">Hot</th>
            <th className="py-2.5 pr-3 text-right">Warm</th>
            <th className="py-2.5 pr-3 text-right">Cold</th>
            <th className="py-2.5 pr-3 text-right">Outreached</th>
            <th className="py-2.5 text-right">Converted</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((r) => {
            const isEmpty = r.total_leads === 0;
            return (
              <tr key={r.product_id} className={`transition-colors hover:bg-slate-50 ${isEmpty ? "opacity-45" : ""}`}>
                <td className="py-3 pr-3">
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                    <span className="font-medium leading-snug text-slate-800">{r.title}</span>
                    {!r.is_active && <Badge variant="NEUTRAL">Inactive</Badge>}
                  </div>
                  <TierDistributionBar tierCounts={r.tier_counts} total={r.total_leads} />
                </td>
                <td className="py-3 pr-3">
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500">
                    {r.target_country}
                  </span>
                </td>
                <td className="py-3 pr-3 text-right text-sm font-semibold tabular-nums text-slate-900">
                  {r.total_leads}
                </td>
                <td className="py-3 pr-3">
                  <div className="flex justify-end"><TierBadge variant="HOT" count={r.tier_counts.HOT} /></div>
                </td>
                <td className="py-3 pr-3">
                  <div className="flex justify-end"><TierBadge variant="WARM" count={r.tier_counts.WARM} /></div>
                </td>
                <td className="py-3 pr-3">
                  <div className="flex justify-end"><TierBadge variant="COLD" count={r.tier_counts.COLD} /></div>
                </td>
                <td className="py-3 pr-3 text-right tabular-nums text-slate-700">
                  {r.outreached > 0 ? r.outreached : <span className="text-slate-300">—</span>}
                </td>
                <td className="py-3 text-right tabular-nums font-semibold">
                  {r.converted > 0 ? (
                    <span className="text-emerald-600">{r.converted}</span>
                  ) : (
                    <span className="font-normal text-slate-300">—</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
