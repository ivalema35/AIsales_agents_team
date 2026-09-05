import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import CampaignCalendar from "../components/CampaignCalendar";
import AlertsPanel from "../components/AlertsPanel";
import DashboardWidget from "../components/DashboardWidget";
import RecentReplies from "../components/RecentReplies";
import WeeklyInsightCard from "../components/WeeklyInsightCard";

const POLL_MS = 15000;

export default function Dashboard() {
  const [alerts, setAlerts] = useState({ needs_response: [], ready_to_claim: [] });
  const [widgetIds, setWidgetIds] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setAlerts(await api.listAlerts());
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

  function handleClaimed(leadId) {
    setAlerts((prev) => ({ ...prev, ready_to_claim: prev.ready_to_claim.filter((a) => a.lead_id !== leadId) }));
  }

  function handleContacted(leadId) {
    setAlerts((prev) => ({ ...prev, needs_response: prev.needs_response.filter((a) => a.lead_id !== leadId) }));
  }

  if (loading) {
    return <p className="mx-auto max-w-7xl px-6 py-10 text-sm text-ink-500">Loading…</p>;
  }

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-6">
      {error && (
        <div className="rounded-lg bg-alert-100 px-4 py-3 text-sm text-alert-700 ring-1 ring-alert-600/20">
          Couldn't reach the backend: {error}
        </div>
      )}

      <AlertsPanel alerts={alerts} onClaimed={handleClaimed} onContacted={handleContacted} />

      <CampaignCalendar />

      {/* Step 19.5 -- sits above replies/widgets so a learned rule is visible without
          digging into Analytics. Empty state is intentional when no ACTIVE insight yet. */}
      <WeeklyInsightCard />

      <RecentReplies />

      {widgetIds.length > 0 && (
        <div>
          <h2 className="mb-3 font-display text-sm font-semibold text-ink-900">
            Your widgets <span className="font-sans font-normal text-ink-500">— pinned from Analytics</span>
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
