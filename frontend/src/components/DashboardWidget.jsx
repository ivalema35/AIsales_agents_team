import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { api } from "../api/client";
import FunnelChart from "./FunnelChart";
import ChannelChart from "./ChannelChart";
import CandleChart from "./CandleChart";
import ProductTierDonuts from "./ProductTierDonuts";
import OutreachFunnelChart from "./OutreachFunnelChart";
import OutreachPeriodPicker from "./OutreachPeriodPicker";

const TITLES = {
  funnel: "Pipeline funnel",
  channel_performance: "Channel performance",
  trend: "Leads discovered per day",
  by_product: "By product",
  outreach_funnel: "Sent, seen & replied",
};

// Each widget body owns its own fetch -- same one-shot-on-mount pattern Analytics.jsx
// itself uses, just split per-chart so the Dashboard doesn't need to know which API
// calls back which chart.
function FunnelWidget() {
  const [data, setData] = useState(null);
  useEffect(() => { api.getFunnel().then(setData); }, []);
  return <FunnelChart data={data} />;
}

function ChannelWidget() {
  const [data, setData] = useState(null);
  useEffect(() => { api.getChannelPerformance().then(setData); }, []);
  return <ChannelChart data={data} />;
}

function TrendWidget() {
  const [range, setRange] = useState("week");
  const [data, setData] = useState(null);
  useEffect(() => {
    const periods = range === "week" ? 7 : 30;
    api.getTrend("day", periods).then(setData);
  }, [range]);
  return (
    <>
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
      <CandleChart data={data} />
    </>
  );
}

function ProductWidget() {
  const [data, setData] = useState(null);
  useEffect(() => { api.getByProduct().then(setData); }, []);
  return <ProductTierDonuts rows={data} />;
}

function OutreachFunnelWidget() {
  const [data, setData] = useState(null);
  function load(start, end) {
    api.getOutreachFunnel(start, end).then(setData);
  }
  return (
    <>
      <OutreachPeriodPicker onChange={load} />
      <OutreachFunnelChart data={data} />
    </>
  );
}

const BODIES = {
  funnel: FunnelWidget,
  channel_performance: ChannelWidget,
  trend: TrendWidget,
  by_product: ProductWidget,
  outreach_funnel: OutreachFunnelWidget,
};

// Renders one pinned Analytics chart on the Dashboard (see api/dashboard.py for the
// persisted pin list). Unknown/stale ids render nothing rather than crash -- the backend
// already filters these on save, but a leftover id from a renamed widget shouldn't take
// the whole Dashboard down.
export default function DashboardWidget({ id, onRemove }) {
  const Body = BODIES[id];
  if (!Body) return null;
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-800">{TITLES[id]}</h3>
        <button
          onClick={() => onRemove(id)}
          title="Remove from Dashboard"
          className="rounded-md p-1 text-slate-300 transition-colors hover:bg-slate-100 hover:text-slate-600"
        >
          <X size={14} />
        </button>
      </div>
      <Body />
    </div>
  );
}
