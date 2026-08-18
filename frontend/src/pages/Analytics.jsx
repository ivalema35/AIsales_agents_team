import { useEffect, useState } from "react";
import { Check, Plus } from "lucide-react";
import { api } from "../api/client";
import FunnelChart from "../components/FunnelChart";
import ChannelChart from "../components/ChannelChart";
import CandleChart from "../components/CandleChart";
import ProductTierDonuts from "../components/ProductTierDonuts";
import OutreachFunnelChart from "../components/OutreachFunnelChart";
import OutreachPeriodPicker from "../components/OutreachPeriodPicker";

function StatTile({ label, value, sub }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-slate-400">{sub}</p>}
    </div>
  );
}

// `widgetId` is optional -- when given, an "Add to Home" toggle appears in the header so
// this exact chart can be pinned onto the Dashboard (server-persisted; see
// api/dashboard.py). Charts with no widgetId (none currently) just render without it.
function Card({ title, widgetId, pinned, onTogglePin, children }) {
  const isPinned = widgetId && pinned.includes(widgetId);
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
        {widgetId && (
          <button
            onClick={() => onTogglePin(widgetId)}
            className={`flex shrink-0 items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium transition-colors ${
              isPinned
                ? "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200 hover:bg-emerald-100"
                : "text-slate-400 ring-1 ring-inset ring-slate-200 hover:bg-slate-50 hover:text-slate-700"
            }`}
          >
            {isPinned ? <Check size={11} /> : <Plus size={11} />}
            {isPinned ? "On Dashboard" : "Add to Home"}
          </button>
        )}
      </div>
      {children}
    </div>
  );
}

export default function Analytics() {
  const [funnel, setFunnel] = useState(null);
  const [channels, setChannels] = useState(null);
  const [trend, setTrend] = useState(null);
  const [range, setRange] = useState("week");
  const [products, setProducts] = useState(null);
  const [outreachFunnel, setOutreachFunnel] = useState(null);
  const [pinned, setPinned] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.getFunnel(), api.getChannelPerformance(), api.getByProduct()])
      .then(([f, c, p]) => { setFunnel(f); setChannels(c); setProducts(p); })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    // Both tabs bucket by day (one candle per day) -- only the RANGE of days shown
    // changes: a week's worth vs a month's worth.
    const periods = range === "week" ? 7 : 30;
    api.getTrend("day", periods).then(setTrend).catch((err) => setError(err.message));
  }, [range]);

  function loadOutreachFunnel(start, end) {
    api.getOutreachFunnel(start, end).then(setOutreachFunnel).catch((err) => setError(err.message));
  }

  useEffect(() => {
    api.getDashboardWidgets().then((r) => setPinned(r.widgets)).catch(() => {});
  }, []);

  async function togglePin(widgetId) {
    const next = pinned.includes(widgetId) ? pinned.filter((w) => w !== widgetId) : [...pinned, widgetId];
    setPinned(next); // optimistic -- a failed save just means the toggle looks live for
                      // a moment before the next Dashboard visit shows the real state.
    try {
      await api.saveDashboardWidgets(next);
    } catch (err) {
      setError(err.message);
    }
  }

  if (error) return <div className="mx-auto max-w-7xl px-6 py-6 text-sm text-red-600">{error}</div>;

  const totalReplies = channels ? channels.EMAIL.replies + channels.WHATSAPP.replies : null;
  const totalSent = channels ? channels.EMAIL.sent + channels.WHATSAPP.sent : null;

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">Analytics</h1>
        <p className="mt-0.5 text-sm text-slate-500">
          Real numbers, computed fresh on every load -- nothing cached or estimated. Pin any chart to
          the Dashboard with "Add to Home".
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatTile label="Total leads" value={funnel ? funnel.total_leads : "…"} />
        <StatTile label="Outreach sent" value={totalSent ?? "…"} sub="Email + WhatsApp" />
        <StatTile label="Replies received" value={totalReplies ?? "…"} />
        <StatTile label="Converted" value={products ? products.reduce((sum, p) => sum + p.converted, 0) : "…"} />
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <Card title="Pipeline funnel" widgetId="funnel" pinned={pinned} onTogglePin={togglePin}>
          <FunnelChart data={funnel} />
        </Card>
        <Card title="Channel performance" widgetId="channel_performance" pinned={pinned} onTogglePin={togglePin}>
          <ChannelChart data={channels} />
        </Card>
      </div>

      <Card title="Leads discovered per day" widgetId="trend" pinned={pinned} onTogglePin={togglePin}>
        <div className="mb-3 flex gap-1">
          {["week", "month"].map((g) => (
            <button
              key={g}
              onClick={() => setRange(g)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                range === g ? "bg-slate-800 text-white" : "text-slate-500 hover:bg-slate-100"
              }`}
            >
              {g === "week" ? "Weekly" : "Monthly"}
            </button>
          ))}
        </div>
        <CandleChart data={trend} />
      </Card>

      <Card title="Sent, seen &amp; replied" widgetId="outreach_funnel" pinned={pinned} onTogglePin={togglePin}>
        <p className="mb-3 -mt-1 text-xs text-slate-400">
          Of the messages sent in the selected period: how many were later seen, and how many got a reply.
        </p>
        <OutreachPeriodPicker onChange={loadOutreachFunnel} />
        <OutreachFunnelChart data={outreachFunnel} />
      </Card>

      <Card title="By product" widgetId="by_product" pinned={pinned} onTogglePin={togglePin}>
        <ProductTierDonuts rows={products} />
      </Card>
    </div>
  );
}
