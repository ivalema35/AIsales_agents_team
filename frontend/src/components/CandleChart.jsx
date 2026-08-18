import { useState } from "react";
import { SERIES, INK } from "../lib/chartColors";

// Builds an SVG path for a bar whose top corners are rounded and whose baseline stays
// square -- same mark spec as the funnel/channel bars (4px rounded data-end only), just
// rotated for a vertical bar. A plain <rect rx> would round all four corners, which reads
// as a floating pill instead of a bar rising from the axis.
function topRoundedBarPath(x, top, width, height, radius) {
  if (height <= 0) return "";
  const r = Math.min(radius, width / 2, height);
  const bottom = top + height;
  return `M${x},${bottom} L${x},${top + r} Q${x},${top} ${x + r},${top} L${x + width - r},${top} Q${x + width},${top} ${x + width},${top + r} L${x + width},${bottom} Z`;
}

// Daily "candle" bars for leads discovered -- one value per day, so no open/high/low/close,
// but styled with the same rising-column read as a candlestick (thin baseline-anchored
// columns rather than a line) since that's what reads clearest for a day-by-day count.
// Single series -> no legend needed (title already names it); hover highlights + a native
// <title> tooltip carry the per-day value, with a table view underneath for the dataviz
// skill's "a table view exists" accessibility requirement. Its own file so the
// Dashboard's pinnable "Leads discovered" widget renders the exact same chart Analytics
// does, not a redrawn copy.
export default function CandleChart({ data }) {
  const [hoverIdx, setHoverIdx] = useState(null);
  const [showTable, setShowTable] = useState(false);
  if (!data || data.length === 0) return null;

  // More top air (room for the tallest bar's label to clear the card edge) and more
  // bottom air (date label sits clear of the baseline instead of crowding it) than the
  // line chart needed -- a bar chart's labels live INSIDE the plot, a line's didn't.
  const W = 720, H = 248, PAD = { top: 28, right: 12, bottom: 30, left: 36 };
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;
  const n = data.length;
  const slot = plotW / n;
  const barWidth = Math.max(4, Math.min(24, slot * 0.5));
  const todayIdx = n - 1;

  const maxY = Math.max(1, ...data.map((d) => d.leads_discovered));
  const niceMax = Math.ceil(maxY / 5) * 5 || 5;
  const y = (v) => PAD.top + plotH - (v / niceMax) * plotH;

  const gridSteps = 4;
  const gridValues = Array.from({ length: gridSteps + 1 }, (_, i) => Math.round((niceMax / gridSteps) * i));
  const labelEvery = Math.ceil(n / 8) || 1;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-4">
        <span className="flex items-center gap-1.5 text-xs text-slate-600">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: SERIES.blue }} />
          Leads discovered
        </span>
        <button
          onClick={() => setShowTable((v) => !v)}
          className="text-xs font-medium text-slate-500 hover:text-slate-800"
        >
          {showTable ? "View as chart" : "View as table"}
        </button>
      </div>

      {showTable ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="py-2 pr-3 font-medium">Day</th>
                <th className="py-2 pr-3 text-right font-medium">Leads discovered</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((d) => (
                <tr key={d.period_end}>
                  <td className="py-1.5 pr-3 text-slate-700">{d.period_end}</td>
                  <td className="py-1.5 pr-3 text-right tabular-nums text-slate-700">{d.leads_discovered}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Leads discovered per day">
        <defs>
          {/* Subtle top-to-bottom lift so the bars read as solid columns, not a flat
             color fill -- the one bit of "premium" polish a plain fill can't give. */}
          <linearGradient id="candleBarFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#5b9be0" />
            <stop offset="100%" stopColor={SERIES.blue} />
          </linearGradient>
        </defs>

        {gridValues.map((v) => (
          <g key={v}>
            <line x1={PAD.left} x2={W - PAD.right} y1={y(v)} y2={y(v)} stroke={INK.grid} strokeWidth="1" />
            <text x={PAD.left - 8} y={y(v)} textAnchor="end" dominantBaseline="middle" fontSize="10" fill={INK.muted}>
              {v}
            </text>
          </g>
        ))}

        {data.map((d, i) => {
          const cx = PAD.left + slot * i + slot / 2;
          const value = d.leads_discovered;
          const barH = (value / niceMax) * plotH;
          const isHover = hoverIdx === i;
          const isToday = i === todayIdx;
          return (
            <g
              key={d.period_end}
              onMouseEnter={() => setHoverIdx(i)}
              onMouseLeave={() => setHoverIdx(null)}
            >
              <rect x={cx - slot / 2} y={PAD.top} width={slot} height={plotH} fill="transparent" />
              {/* Today's column gets a faint standing band, so "where are we now" reads
                 at a glance without a legend entry for a single highlighted day. */}
              {isToday && (
                <rect x={cx - slot / 2 + 1} y={PAD.top} width={slot - 2} height={plotH} fill="#f1f5f9" rx="4" />
              )}
              {i % labelEvery === 0 && (
                <text
                  x={cx}
                  y={H - 10}
                  textAnchor="middle"
                  fontSize="9"
                  fontWeight={isToday ? "700" : "400"}
                  fill={isToday ? INK.secondary : INK.muted}
                >
                  {isToday ? "Today" : d.period_end.slice(5)}
                </text>
              )}
              {value > 0 ? (
                <>
                  <path
                    d={topRoundedBarPath(cx - barWidth / 2, y(value), barWidth, barH, 4)}
                    fill="url(#candleBarFill)"
                    stroke={isHover ? SERIES.blue : "none"}
                    strokeWidth={isHover ? 2 : 0}
                    opacity={isHover ? 1 : 0.92}
                    className="transition-opacity duration-150"
                  >
                    <title>{`${d.period_end}: ${value} lead${value === 1 ? "" : "s"} discovered`}</title>
                  </path>
                  {/* Selective direct label -- only non-zero bars get one, so a run of
                     quiet days doesn't drown the numbers that actually say something
                     (dataviz skill: "label the endpoint... never a number on every point"). */}
                  <text
                    x={cx}
                    y={y(value) - 8}
                    textAnchor="middle"
                    fontSize="11"
                    fontWeight={isHover ? "700" : "600"}
                    fill={isHover ? INK.primary : INK.secondary}
                  >
                    {value}
                  </text>
                </>
              ) : (
                // Zero day: a short flat tick on the baseline reads as "no data" without
                // a floating "0" competing for attention against real values.
                <line x1={cx - 5} x2={cx + 5} y1={y(0)} y2={y(0)} stroke={INK.grid} strokeWidth="2" />
              )}
            </g>
          );
        })}
      </svg>
      )}
    </div>
  );
}
