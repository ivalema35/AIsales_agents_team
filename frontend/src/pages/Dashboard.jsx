import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import PipelineKanban from "../components/PipelineKanban";
import AlertsPanel from "../components/AlertsPanel";
import SystemToggles from "../components/SystemToggles";

const POLL_MS = 15000;

export default function Dashboard() {
  const [leads, setLeads] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [leadsRes, alertsRes] = await Promise.all([api.listLeads(), api.listAlerts()]);
      setLeads(leadsRes);
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

  function handleClaimed(leadId) {
    setAlerts((prev) => prev.filter((a) => a.lead_id !== leadId));
    setLeads((prev) => prev.map((l) => (l.id === leadId ? { ...l, status: "HOT_LEAD" } : l)));
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

      <SystemToggles />

      <AlertsPanel alerts={alerts} onClaimed={handleClaimed} />

      <div>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">
          Pipeline <span className="font-normal text-slate-400">({leads.length} leads)</span>
        </h2>
        <PipelineKanban leads={leads} />
      </div>
    </div>
  );
}
