import { SERIES } from "../lib/chartColors";

// Grouped bars, 2 categorical series (channel), legend (required for 2+ series). Its own
// file (not inlined in Analytics.jsx) so the Dashboard's pinnable "Channel performance"
// widget renders the exact same chart, not a redrawn copy that could drift out of sync.
export default function ChannelChart({ data }) {
  if (!data) return null;
  const channels = ["EMAIL", "WHATSAPP"];
  const colors = { EMAIL: SERIES.blue, WHATSAPP: SERIES.orange };
  // Funnel order -- Sent, then Seen (real read-receipt/email-open data, see
  // api/inbound.py's WhatsApp status handling and api/webhooks.py's Resend handler),
  // then Replies. Each stage is naturally <= the one before it.
  const metrics = [
    { key: "sent", label: "Sent" },
    { key: "seen", label: "Seen" },
    { key: "replies", label: "Replies" },
  ];
  const max = Math.max(1, ...channels.flatMap((c) => metrics.map((m) => data[c][m.key] || 0)));

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-4 text-xs text-slate-600">
        {channels.map((c) => (
          <span key={c} className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: colors[c] }} />
            {c === "EMAIL" ? "Email" : "WhatsApp"}
          </span>
        ))}
      </div>
      {metrics.map((m) => (
        <div key={m.key} className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-slate-500">{m.label}</span>
          {channels.map((c) => {
            const value = data[c][m.key] || 0;
            const pct = (value / max) * 100;
            const barWidth = value > 0 ? Math.max(pct, 3) : 0;
            return (
              <div key={c} className="flex items-center gap-2">
                <div className="h-4 flex-1 overflow-hidden rounded-md bg-slate-100">
                  <div
                    className="h-full rounded-r-[4px] transition-all duration-300 ease-out"
                    style={{ width: `${barWidth}%`, backgroundColor: colors[c] }}
                    title={`${c === "EMAIL" ? "Email" : "WhatsApp"} ${m.label.toLowerCase()}: ${value}`}
                  />
                </div>
                <span className="w-8 shrink-0 text-right text-xs font-semibold tabular-nums text-slate-700">{value}</span>
              </div>
            );
          })}
        </div>
      ))}
      <div className="mt-1 grid grid-cols-2 gap-3 border-t border-slate-100 pt-3">
        {channels.map((c) => (
          <div key={c} className="flex items-center gap-2.5 rounded-md bg-slate-50 px-3 py-2">
            <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: colors[c] }} />
            <div className="flex flex-1 items-center justify-between gap-2">
              <div>
                <p className="text-[11px] text-slate-500">{c === "EMAIL" ? "Email" : "WhatsApp"} seen rate</p>
                <p className="text-sm font-semibold text-slate-900">
                  {data[c].seen_rate != null ? `${(data[c].seen_rate * 100).toFixed(1)}%` : "—"}
                </p>
              </div>
              <div>
                <p className="text-[11px] text-slate-500">Reply rate</p>
                <p className="text-sm font-semibold text-slate-900">
                  {data[c].reply_rate != null ? `${(data[c].reply_rate * 100).toFixed(1)}%` : "—"}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
