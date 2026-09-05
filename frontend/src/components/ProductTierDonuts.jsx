import { useState } from "react";
import { TIER_BORDER } from "../lib/tierColors";
import ProductTable from "./ProductTable";

// Chart chrome fills (center labels, empty track) -- parchment/ink tokens as hex for SVG.
// Track uses line-strong so an empty ring stays visible on parchment-raised cards
// (the old near-white track washed out and looked broken).
const CHROME = {
  primary: "#1d2340", // ink-900
  muted: "#6c7093",   // ink-500
  track: "#c7bd9f",   // line-strong
};

// dataviz skill: a donut is only sanctioned for "part-to-whole at a glance, <=6
// segments" -- one big pie of 8 PRODUCT slices would be exactly the anti-pattern it
// warns against ("donut for comparing close values" / "8 categorical hues when the
// story is one number"). This is the opposite shape: small multiples, one compact
// 3-segment donut PER product (HOT/WARM/COLD only -- always <=3 segments), which is
// what the guidance actually allows. Comparing products happens by scanning the grid,
// not by cramming everything into one wheel.
const TIER_ORDER = ["HOT", "WARM", "COLD"];
const DONUT_SIZE = 72;
const STROKE = 11;
const GAP_PX = 2; // mark-spec: a surface gap between touching segments, not a border

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
    <svg
      width={DONUT_SIZE}
      height={DONUT_SIZE}
      viewBox={`0 0 ${DONUT_SIZE} ${DONUT_SIZE}`}
      role="img"
      aria-label={`${total} leads by tier`}
      className="shrink-0"
    >
      {/* Always-present track (even at total=0) -- consistent with every other
         zero-state track in this app (TierDistributionBar, PipelineKanban's empty
         columns): a flat ring reads as "no data yet," not a rendering glitch. */}
      <circle
        cx={cx}
        cy={cy}
        r={r}
        fill="none"
        stroke={CHROME.track}
        strokeWidth={STROKE}
        strokeOpacity={total > 0 ? 0.4 : 0.65}
        strokeDasharray={total > 0 ? undefined : "4 4"}
      />
      {segments.map((s) => (
        <circle
          key={s.tier}
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={TIER_BORDER[s.tier]}
          strokeWidth={STROKE}
          strokeDasharray={`${s.len} ${circumference - s.len}`}
          transform={`rotate(${s.rotate} ${cx} ${cy})`}
        >
          <title>{`${s.tier}: ${s.count} lead${s.count === 1 ? "" : "s"}`}</title>
        </circle>
      ))}
      <text
        x={cx}
        y={cy - 2}
        textAnchor="middle"
        fontSize="15"
        fontWeight="700"
        fontFamily="IBM Plex Mono, ui-monospace, monospace"
        fill={CHROME.primary}
      >
        {total}
      </text>
      <text x={cx} y={cy + 11} textAnchor="middle" fontSize="7" fill={CHROME.muted} letterSpacing="0.4">
        LEADS
      </text>
    </svg>
  );
}

// Small multiples of per-product tier donuts -- one glanceable ring per product, sorted
// biggest first. Horizontal row cards (donut left, copy right) so product titles stay
// readable instead of truncating in a cramped 4-column vertical stack. Color is never
// the only signal: a legend names every hue up top, each segment carries a hover
// tooltip, and "View as table" is the accessibility relief the dataviz skill's contrast
// check obligates for the muted COLD gray.
export default function ProductTierDonuts({ rows }) {
  const [showTable, setShowTable] = useState(false);
  if (!rows) return null;

  const sorted = [...rows].sort((a, b) => b.total_leads - a.total_leads);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 text-[11px] text-ink-700">
          {TIER_ORDER.map((t) => (
            <span key={t} className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: TIER_BORDER[t] }} />
              {t}
            </span>
          ))}
        </div>
        <button
          onClick={() => setShowTable((v) => !v)}
          className="shrink-0 text-xs font-medium text-ink-500 hover:text-ink-900"
        >
          {showTable ? "View as chart" : "View as table"}
        </button>
      </div>

      {showTable ? (
        <ProductTable rows={rows} />
      ) : (
        <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
          {sorted.map((p) => {
            const hot = p.tier_counts?.HOT || 0;
            const warm = p.tier_counts?.WARM || 0;
            const cold = p.tier_counts?.COLD || 0;
            return (
              <div
                key={p.product_id}
                title={p.title}
                className={`flex items-center gap-3 rounded-lg border border-line bg-parchment p-3 transition-colors hover:border-line-strong ${
                  p.total_leads === 0 ? "opacity-55" : ""
                }`}
              >
                <ProductDonut tierCounts={p.tier_counts} total={p.total_leads} />
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-semibold leading-snug text-ink-900 line-clamp-2">
                    {p.title}
                  </p>
                  <div className="mt-1 flex flex-wrap items-center gap-1.5">
                    <span className="rounded bg-parchment-raised-2 px-1.5 py-0.5 font-mono text-[10px] font-medium text-ink-500">
                      {p.target_country}
                    </span>
                    {/* Inactive only -- an "Active" pill on every live product just adds
                       noise; absence of this label already means discovery is on. */}
                    {!p.is_active && (
                      <span className="text-[10px] font-medium text-ink-500">Inactive</span>
                    )}
                  </div>
                  {p.total_leads > 0 && (
                    <p className="mt-1.5 font-mono text-[10px] tabular-nums text-ink-500">
                      <span style={{ color: TIER_BORDER.HOT }}>{hot} hot</span>
                      <span className="mx-1 text-ink-500/40">·</span>
                      <span style={{ color: TIER_BORDER.WARM }}>{warm} warm</span>
                      <span className="mx-1 text-ink-500/40">·</span>
                      <span style={{ color: TIER_BORDER.COLD }}>{cold} cold</span>
                    </p>
                  )}
                  {(p.outreached > 0 || p.converted > 0) && (
                    <p className="mt-0.5 text-[10px] text-ink-500">
                      {p.outreached > 0 && `${p.outreached} outreached`}
                      {p.outreached > 0 && p.converted > 0 && " · "}
                      {p.converted > 0 && (
                        <span className="font-medium text-good-600">{p.converted} converted</span>
                      )}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
