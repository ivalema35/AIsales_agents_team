import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import PipelineKanban from "../components/PipelineKanban";
import AlertsPanel from "../components/AlertsPanel";
import DashboardWidget from "../components/DashboardWidget";
import RecentReplies from "../components/RecentReplies";

const POLL_MS = 15000;
const TIERS = ["HOT", "WARM", "COLD"];
// Same filled/pill treatment as the Leads page's tier filter -- one look for "tier
// filter" across the app, not a redrawn variant per page.
const TIER_PILL_ACTIVE = {
  HOT: "bg-red-600 text-white ring-1 ring-inset ring-red-600",
  WARM: "bg-amber-500 text-white ring-1 ring-inset ring-amber-500",
  COLD: "bg-slate-600 text-white ring-1 ring-inset ring-slate-600",
};
const TIER_PILL_INACTIVE = "bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-50";

const DATE_PRESETS = [
  { value: "", label: "All time" },
  { value: "today", label: "Today" },
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
];

// created_at has no timezone marker in the raw string (SQLite CURRENT_TIMESTAMP, UTC) --
// append one before parsing so the comparison is against a real instant, not whatever
// timezone the browser would otherwise assume for a bare "YYYY-MM-DD HH:MM:SS" string.
function parseUtc(dateStr) {
  return new Date(dateStr.replace(" ", "T") + "Z");
}

function dateCutoff(preset) {
  if (!preset) return null;
  const now = new Date();
  if (preset === "today") return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  const days = preset === "7d" ? 7 : 30;
  return new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
}

export default function Dashboard() {
  const [leads, setLeads] = useState([]);
  const [alerts, setAlerts] = useState({ needs_response: [], ready_to_claim: [] });
  const [products, setProducts] = useState([]);
  const [productFilter, setProductFilter] = useState("");
  const [tierFilter, setTierFilter] = useState("");
  const [dateFilter, setDateFilter] = useState("");
  const [widgetIds, setWidgetIds] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [leadsRes, alertsRes] = await Promise.all([api.listLeads(), api.listAlerts()]);
      setLeads(leadsRes.leads);
      setAlerts(alertsRes);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  useEffect(() => {
    api.listProducts().then(setProducts).catch(() => {});
  }, []);

  useEffect(() => {
    api.getDashboardWidgets().then((r) => setWidgetIds(r.widgets)).catch(() => {});
  }, []);

  async function removeWidget(widgetId) {
    const next = widgetIds.filter((w) => w !== widgetId);
    setWidgetIds(next);
    try {
      await api.saveDashboardWidgets(next);
    } catch (err) {
      setError(err.message);
    }
  }

  // Client-side, not a refetch -- `leads` already holds every lead (Dashboard's own
  // api.listLeads() call has no page/filter params, so it gets the full up-to-500 set),
  // so narrowing by product/tier/date here is instant and doesn't disturb the 15s poll.
  const cutoff = dateCutoff(dateFilter);
  const visibleLeads = leads
    .filter((l) => !productFilter || l.product_id === productFilter)
    .filter((l) => !tierFilter || l.score?.tier === tierFilter)
    .filter((l) => !cutoff || parseUtc(l.created_at) >= cutoff);

  function handleClaimed(leadId) {
    setAlerts((prev) => ({ ...prev, ready_to_claim: prev.ready_to_claim.filter((a) => a.lead_id !== leadId) }));
    setLeads((prev) => prev.map((l) => (l.id === leadId ? { ...l, status: "HOT_LEAD" } : l)));
  }

  function handleContacted(leadId) {
    setAlerts((prev) => ({ ...prev, needs_response: prev.needs_response.filter((a) => a.lead_id !== leadId) }));
    setLeads((prev) => prev.map((l) => (l.id === leadId ? { ...l, status: "ENGAGED" } : l)));
  }

  if (loading) {
    return <p className="mx-auto max-w-7xl px-6 py-10 text-sm text-slate-400">Loading…</p>;
  }

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-6">
      {error && (
        <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-red-100">
          Couldn't reach the backend: {error}
        </div>
      )}

      <AlertsPanel alerts={alerts} onClaimed={handleClaimed} onContacted={handleContacted} />

      <div>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-slate-700">
            Pipeline <span className="font-normal text-slate-400">({visibleLeads.length} leads)</span>
          </h2>
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={productFilter}
              onChange={(e) => setProductFilter(e.target.value)}
              className="rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:border-slate-400 focus:outline-none"
            >
              <option value="">All products</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>{p.title}</option>
              ))}
            </select>
            <div className="flex items-center gap-1.5">
              {TIERS.map((t) => (
                <button
                  key={t}
                  onClick={() => setTierFilter((prev) => (prev === t ? "" : t))}
                  className={`rounded-full px-2.5 py-1 text-[11px] font-semibold transition-colors ${
                    tierFilter === t ? TIER_PILL_ACTIVE[t] : TIER_PILL_INACTIVE
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
            <select
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:border-slate-400 focus:outline-none"
            >
              {DATE_PRESETS.map((d) => (
                <option key={d.value} value={d.value}>{d.label}</option>
              ))}
            </select>
          </div>
        </div>
        <PipelineKanban leads={visibleLeads} />
      </div>

      <RecentReplies />

      {widgetIds.length > 0 && (
        <div>
          <h2 className="mb-3 text-sm font-semibold text-slate-700">
            Your widgets <span className="font-normal text-slate-400">-- pinned from Analytics</span>
          </h2>
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
            {widgetIds.map((id) => (
              <DashboardWidget key={id} id={id} onRemove={removeWidget} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
