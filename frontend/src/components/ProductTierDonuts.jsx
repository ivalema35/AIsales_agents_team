import { useState } from "react";
import { TIER_BORDER } from "../lib/tierColors";
import Badge from "./ui/Badge";
import ProductTable from "./ProductTable";

// dataviz skill: a donut is only sanctioned for "part-to-whole at a glance, <=6
// segments" -- one big pie of 8 PRODUCT slices would be exactly the anti-pattern it
// warns against ("donut for comparing close values" / "8 categorical hues when the
// story is one number"). This is the opposite shape: small multiples, one compact
// 3-segment donut PER product (HOT/WARM/COLD only -- always <=3 segments), which is
// what the guidance actually allows. Comparing products happens by scanning the grid,
// not by cramming everything into one wheel.
const TIER_ORDER = ["HOT", "WARM", "COLD"];
const DONUT_SIZE = 96;
const STROKE = 13;
const GAP_PX = 3; // mark-spec: a surface gap between touching segments, not a border

function ProductDonut({ tierCounts, total }) {
  const r = (DONUT_SIZE - STROKE) / 2;
  const cx = DONUT_SIZE / 2;
  const cy = DONUT_SIZE / 2;
  const circumference = 2 * Math.PI * r;

  let cursor = -90; // start at 12 o'clock
  const segments = [];
  for (const tier of TIER_ORDER) {
    const count = tierCounts[tier] || 0;
    if (!count || !total) continue;
    const pct = count / total;
    const len = Math.max(0, pct * circumference - GAP_PX);
    segments.push({ tier, count, len, rotate: cursor });
    cursor += pct * 360;
  }

  return (
    <svg width={DONUT_SIZE} height={DONUT_SIZE} viewBox={`0 0 ${DONUT_SIZE} ${DONUT_SIZE}`} role="img" aria-label={`${total} leads by tier`}>
      {/* Always-present track (even at total=0) -- consistent with every other
         zero-state track in this app (TierDistributionBar, PipelineKanban's empty
         columns): a flat ring reads as "no data yet," not a rendering glitch. */}
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#f1f5f9" strokeWidth={STROKE} />
      {segments.map((s) => (
        <circle
          key={s.tier}
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke={TIER_BORDER[s.tier]}
          strokeWidth={STROKE}
          strokeDasharray={`${s.len} ${circumference - s.len}`}
          transform={`rotate(${s.rotate} ${cx} ${cy})`}
        >
          <title>{`${s.tier}: ${s.count} lead${s.count === 1 ? "" : "s"}`}</title>
        </circle>
      ))}
      <text x={cx} y={cy - 3} textAnchor="middle" fontSize="19" fontWeight="700" fill="#0b0b0b">
        {total}
      </text>
      <text x={cx} y={cy + 13} textAnchor="middle" fontSize="8" fill="#898781" letterSpacing="0.5">
        LEADS
      </text>
    </svg>
  );
}

// Small multiples of per-product tier donuts -- one glanceable ring per product, sorted
// biggest first. Color is never the only signal: a legend names every hue up top, each
// segment carries a hover tooltip with its exact count, and "View as table" (the
// existing ProductTable, reused not redrawn) is the accessibility relief the dataviz
// skill's contrast check obligates for the muted COLD gray.
export default function ProductTierDonuts({ rows }) {
  const [showTable, setShowTable] = useState(false);
  if (!rows) return null;

  const sorted = [...rows].sort((a, b) => b.total_leads - a.total_leads);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4 text-xs text-slate-600">
          {TIER_ORDER.map((t) => (
            <span key={t} className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: TIER_BORDER[t] }} />
              {t}
            </span>
          ))}
        </div>
        <button
          onClick={() => setShowTable((v) => !v)}
          className="text-xs font-medium text-slate-500 hover:text-slate-800"
        >
          {showTable ? "View as chart" : "View as table"}
        </button>
      </div>

      {showTable ? (
        <ProductTable rows={rows} />
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {sorted.map((p) => (
            <div
              key={p.product_id}
              className={`flex flex-col items-center gap-2 rounded-lg border border-slate-100 p-3 text-center transition-colors hover:border-slate-200 ${
                p.total_leads === 0 ? "opacity-50" : ""
              }`}
            >
              <ProductDonut tierCounts={p.tier_counts} total={p.total_leads} />
              <div className="min-w-0">
                <p className="line-clamp-2 text-xs font-medium leading-snug text-slate-800">{p.title}</p>
                <div className="mt-1 flex flex-wrap items-center justify-center gap-1">
                  <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                    {p.target_country}
                  </span>
                  {!p.is_active && <Badge variant="NEUTRAL">Inactive</Badge>}
                </div>
              </div>
              {(p.outreached > 0 || p.converted > 0) && (
                <p className="text-[10px] text-slate-400">
                  {p.outreached > 0 && `${p.outreached} outreached`}
                  {p.outreached > 0 && p.converted > 0 && " · "}
                  {p.converted > 0 && <span className="font-medium text-emerald-600">{p.converted} converted</span>}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
