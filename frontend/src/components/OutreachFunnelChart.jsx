import { useState } from "react";
import { SERIES, INK } from "../lib/chartColors";

// Bucket colors validated together (dataviz skill validator, light mode): CVD separation
// worst-adjacent ΔE 9.2, normal-vision floor 27.6 -- both clear. The gray FAILs the
// categorical lightness-band/chroma-floor checks on purpose: it's a neutral "nothing
// happened yet" background state, same accepted reasoning as the COLD-tier gray
// elsewhere in this app (ProductTierDonuts) -- not a real category competing for
// attention. Reused hues, not invented: aqua already means "replies" (get_trend's
// palette), orange already means "seen" (the old ChannelChart rows) -- so the meaning
// carries over instead of introducing a 4th color family for the same concepts.
const BUCKETS = [
  { key: "replied", label: "Replied", color: SERIES.aqua },
  { key: "seen_no_reply", label: "Seen, no reply", color: SERIES.orange },
  { key: "not_seen", label: "Not seen", color: "#cbd5e1" },
];

const CHANNEL_META = {
  EMAIL: { label: "Email", dot: SERIES.blue },
  WHATSAPP: { label: "WhatsApp", dot: "#eb6834" },
};

const SIZE = 168;
const STROKE = 22;
const GAP_PX = 3; // mark-spec: a surface gap between touching segments, not a border

// One donut per channel: this IS genuine part-to-whole (unlike a raw Sent/Seen/Replied
// pie, where Seen and Replied are subsets of Sent, not additive slices -- summing them
// would double count and the "total" would mean nothing). Here each SENT message lands
// in exactly one of three mutually-exclusive buckets (see get_outreach_funnel's
// classification), so the ring's segments always sum to the channel's real total sent --
// same "small multiples, <=6 segments" shape the dataviz skill sanctions for
// ProductTierDonuts, reapplied here with this chart's own bucket semantics.
function ChannelDonut({ channel, data }) {
  const total = data.sent;
  const r = (SIZE - STROKE) / 2;
  const cx = SIZE / 2;
  const cy = SIZE / 2;
  const circumference = 2 * Math.PI * r;

  let cursor = -90; // 12 o'clock start
  const segments = [];
  for (const b of BUCKETS) {
    const count = data.buckets[b.key] || 0;
    if (!count || !total) continue;
    const pct = count / total;
    const len = Math.max(0, pct * circumference - GAP_PX);
    segments.push({ ...b, count, len, rotate: cursor, pct });
    cursor += pct * 360;
  }

  const meta = CHANNEL_META[channel];

  return (
    <div className="flex flex-col items-center gap-3">
      <span className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
        <span className="h-2 w-2 rounded-full" style={{ backgroundColor: meta.dot }} />
        {meta.label}
      </span>
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`} role="img" aria-label={`${meta.label}: ${total} sent`}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#f1f5f9" strokeWidth={STROKE} />
        {segments.map((s) => (
          <circle
            key={s.key}
            cx={cx} cy={cy} r={r}
            fill="none"
            stroke={s.color}
            strokeWidth={STROKE}
            strokeDasharray={`${s.len} ${circumference - s.len}`}
            transform={`rotate(${s.rotate} ${cx} ${cy})`}
          >
            <title>{`${meta.label} — ${s.label}: ${s.count} (${Math.round(s.pct * 100)}% of sent)`}</title>
          </circle>
        ))}
        <text x={cx} y={cy - 6} textAnchor="middle" fontSize="26" fontWeight="700" fill={INK.primary}>
          {total}
        </text>
        <text x={cx} y={cy + 14} textAnchor="middle" fontSize="10" fill={INK.muted} letterSpacing="0.5">
          SENT
        </text>
      </svg>
      {total > 0 ? (
        <div className="flex flex-col gap-1 self-stretch">
          {BUCKETS.map((b) => {
            const count = data.buckets[b.key] || 0;
            const pct = total > 0 ? Math.round((count / total) * 100) : 0;
            return (
              <div key={b.key} className="flex items-center justify-between gap-2 text-xs">
                <span className="flex items-center gap-1.5 text-slate-600">
                  <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: b.color }} />
                  {b.label}
                </span>
                <span className="font-semibold tabular-nums text-slate-800">
                  {count} <span className="font-normal text-slate-400">({pct}%)</span>
                </span>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="text-xs text-slate-400">Nothing sent</p>
      )}
    </div>
  );
}

function OutreachFunnelTable({ data }) {
  const { channels } = data;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="border-b border-slate-200 text-slate-500">
            <th className="py-2 pr-3 font-medium">Channel</th>
            <th className="py-2 pr-3 text-right font-medium">Sent</th>
            <th className="py-2 pr-3 text-right font-medium">Replied</th>
            <th className="py-2 pr-3 text-right font-medium">Seen, no reply</th>
            <th className="py-2 pr-3 text-right font-medium">Not seen</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {Object.entries(channels).map(([channel, d]) => (
            <tr key={channel}>
              <td className="py-1.5 pr-3 font-medium text-slate-700">{CHANNEL_META[channel].label}</td>
              <td className="py-1.5 pr-3 text-right tabular-nums text-slate-700">{d.sent}</td>
              <td className="py-1.5 pr-3 text-right tabular-nums text-slate-700">{d.buckets.replied}</td>
              <td className="py-1.5 pr-3 text-right tabular-nums text-slate-700">{d.buckets.seen_no_reply}</td>
              <td className="py-1.5 pr-3 text-right tabular-nums text-slate-700">{d.buckets.not_seen}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function OutreachFunnelChart({ data }) {
  const [showTable, setShowTable] = useState(false);
  if (!data) return null;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4 text-xs text-slate-600">
          {BUCKETS.map((b) => (
            <span key={b.key} className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: b.color }} />
              {b.label}
            </span>
          ))}
        </div>
        <button
          onClick={() => setShowTable((v) => !v)}
          className="shrink-0 text-xs font-medium text-slate-500 hover:text-slate-800"
        >
          {showTable ? "View as chart" : "View as table"}
        </button>
      </div>

      {showTable ? (
        <OutreachFunnelTable data={data} />
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          {Object.entries(data.channels).map(([channel, d]) => (
            <ChannelDonut key={channel} channel={channel} data={d} />
          ))}
        </div>
      )}
    </div>
  );
}
