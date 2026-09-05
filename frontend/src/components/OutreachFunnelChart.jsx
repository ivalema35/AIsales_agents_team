import { useState } from "react";
import { Mail, MessageCircle } from "lucide-react";
import { SERIES } from "../lib/chartColors";

// Chart chrome fills (center labels, empty track) -- parchment/ink tokens as hex for SVG.
// Track deliberately sits on line-strong rather than parchment-raised-2: against a raised
// card surface the old near-white track disappeared (looked like a broken/missing ring).
const CHROME = {
  primary: "#1d2340", // ink-900
  muted: "#6c7093",   // ink-500
  track: "#c7bd9f",   // line-strong -- readable empty ring on parchment-raised
};

// Bucket colors validated together (dataviz skill validator, light mode): CVD separation
// worst-adjacent ΔE 9.2, normal-vision floor 27.6 -- both clear. The gray FAILs the
// categorical lightness-band/chroma-floor checks on purpose: it's a neutral "nothing
// happened yet" background state, same accepted reasoning as the COLD-tier gray
// elsewhere in this app (ProductTierDonuts) -- not a real category competing for
// attention. Reused hues, not invented: aqua already means "replies" (get_trend's
// palette), orange already means "seen" (the old ChannelChart rows) -- so the meaning
// carries over instead of introducing a 4th color family for the same concepts.
// not_seen uses line-strong (parchment-compatible slate/gray neutral replacement).
const BUCKETS = [
  { key: "replied", label: "Replied", color: SERIES.aqua },
  { key: "seen_no_reply", label: "Seen, no reply", color: SERIES.orange },
  { key: "not_seen", label: "Not seen", color: "#c7bd9f" },
];

const CHANNEL_META = {
  EMAIL: { label: "Email", dot: SERIES.blue, Icon: Mail },
  WHATSAPP: { label: "WhatsApp", dot: "#eb6834", Icon: MessageCircle },
};

const SIZE = 132;
const STROKE = 18;
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
  const Icon = meta.Icon;

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-line bg-parchment p-4">
      <span className="flex items-center gap-1.5 text-xs font-semibold text-ink-900">
        <span className="flex h-5 w-5 items-center justify-center rounded-md" style={{ backgroundColor: `${meta.dot}18` }}>
          <Icon size={12} style={{ color: meta.dot }} />
        </span>
        {meta.label}
      </span>

      <div className="flex items-center gap-4">
        <svg
          width={SIZE}
          height={SIZE}
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          role="img"
          aria-label={`${meta.label}: ${total} sent`}
          className="shrink-0"
        >
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke={CHROME.track}
            strokeWidth={STROKE}
            strokeOpacity={total > 0 ? 0.45 : 0.7}
            strokeDasharray={total > 0 ? undefined : "6 5"}
          />
          {segments.map((s) => (
            <circle
              key={s.key}
              cx={cx}
              cy={cy}
              r={r}
              fill="none"
              stroke={s.color}
              strokeWidth={STROKE}
              strokeLinecap="butt"
              strokeDasharray={`${s.len} ${circumference - s.len}`}
              transform={`rotate(${s.rotate} ${cx} ${cy})`}
            >
              <title>{`${meta.label} — ${s.label}: ${s.count} (${Math.round(s.pct * 100)}% of sent)`}</title>
            </circle>
          ))}
          <text
            x={cx}
            y={cy - 4}
            textAnchor="middle"
            fontSize="22"
            fontWeight="700"
            fontFamily="IBM Plex Mono, ui-monospace, monospace"
            fill={CHROME.primary}
          >
            {total}
          </text>
          <text x={cx} y={cy + 12} textAnchor="middle" fontSize="9" fill={CHROME.muted} letterSpacing="0.6">
            SENT
          </text>
        </svg>

        {total > 0 ? (
          <div className="flex min-w-0 flex-1 flex-col gap-1.5">
            {BUCKETS.map((b) => {
              const count = data.buckets[b.key] || 0;
              const pct = Math.round((count / total) * 100);
              return (
                <div key={b.key} className="flex flex-col gap-0.5">
                  <div className="flex items-center justify-between gap-2 text-[11px]">
                    <span className="flex items-center gap-1.5 text-ink-700">
                      <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ backgroundColor: b.color }} />
                      {b.label}
                    </span>
                    <span className="font-mono tabular-nums text-ink-900">
                      {count}
                      <span className="ml-1 font-sans text-ink-500">({pct}%)</span>
                    </span>
                  </div>
                  <div className="h-1 overflow-hidden rounded-full bg-parchment-raised-2">
                    <div
                      className="h-full rounded-full transition-[width]"
                      style={{ width: `${pct}%`, backgroundColor: b.color }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs leading-relaxed text-ink-500">
            No {meta.label.toLowerCase()} sent in this period.
          </p>
        )}
      </div>
    </div>
  );
}

function EmptyOutreachState() {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-line bg-parchment px-4 py-10 text-center">
      <div className="flex items-center gap-3 text-ink-500">
        <Mail size={18} />
        <span className="text-ink-500/40">·</span>
        <MessageCircle size={18} />
      </div>
      <p className="text-sm font-medium text-ink-700">Nothing sent yet</p>
      <p className="max-w-xs text-xs text-ink-500">
        Once outreach goes out, each channel shows how many were replied, seen, or still unseen.
      </p>
    </div>
  );
}

function OutreachFunnelTable({ data }) {
  const { channels } = data;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="border-b border-line text-ink-500">
            <th className="py-2 pr-3 font-medium">Channel</th>
            <th className="py-2 pr-3 text-right font-medium">Sent</th>
            <th className="py-2 pr-3 text-right font-medium">Replied</th>
            <th className="py-2 pr-3 text-right font-medium">Seen, no reply</th>
            <th className="py-2 pr-3 text-right font-medium">Not seen</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {Object.entries(channels).map(([channel, d]) => (
            <tr key={channel}>
              <td className="py-1.5 pr-3 font-medium text-ink-700">{CHANNEL_META[channel].label}</td>
              <td className="py-1.5 pr-3 text-right font-mono tabular-nums text-ink-700">{d.sent}</td>
              <td className="py-1.5 pr-3 text-right font-mono tabular-nums text-ink-700">{d.buckets.replied}</td>
              <td className="py-1.5 pr-3 text-right font-mono tabular-nums text-ink-700">{d.buckets.seen_no_reply}</td>
              <td className="py-1.5 pr-3 text-right font-mono tabular-nums text-ink-700">{d.buckets.not_seen}</td>
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

  const totalSent = Object.values(data.channels).reduce((sum, d) => sum + (d.sent || 0), 0);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-ink-700">
          {BUCKETS.map((b) => (
            <span key={b.key} className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: b.color }} />
              {b.label}
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
        <OutreachFunnelTable data={data} />
      ) : totalSent === 0 ? (
        <EmptyOutreachState />
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {Object.entries(data.channels).map(([channel, d]) => (
            <ChannelDonut key={channel} channel={channel} data={d} />
          ))}
        </div>
      )}
    </div>
  );
}
