// Live system monitor (Phase 6 Step 6.3, CRM_UI_UX_PLAN.md §2A Phase 5).
//
// Answers the one question the CRM could not answer at all before: "is the system alive,
// and what is it doing right now?" Two real incidents -- a background process silently not
// running for a whole session, and two leads stranded mid-outreach after a provider outage --
// were both found only by reading logs over SSH. This page is the fix for that blindness.
//
// Read-only by design: no button here changes anything. Plain interval polling, not a
// WebSocket -- the same "don't add infrastructure a simpler mechanism already covers"
// judgement that dropped n8n from the architecture.
import { useCallback, useEffect, useRef, useState } from "react";
import { Activity, AlertTriangle, RefreshCw } from "lucide-react";
import { api } from "../api/client";
import Badge from "../components/ui/Badge";

const POLL_MS = 5000;

// Human labels -- a card reading "jobs.discovery_scheduler" makes the operator translate
// module paths in their head; the module name stays visible underneath as the real identity.
const PROCESS_LABELS = {
  "jobs.worker": "Job Worker",
  "scraper_worker.async_runner": "Lead Scraper",
  "jobs.discovery_scheduler": "Discovery Scheduler",
  "jobs.inbound_poller": "Inbound Poller",
};

const PROCESS_BLURB = {
  "jobs.worker": "Sends outreach email/WhatsApp, classifies replies",
  "scraper_worker.async_runner": "Discovers, enriches, reviews and scores leads",
  "jobs.discovery_scheduler": "Decides who to target, paces outreach, nightly report",
  "jobs.inbound_poller": "Checks the inbox for replies",
};

const STATE_UI = {
  UP: { dot: "bg-emerald-500", ring: "ring-emerald-200", label: "Running", variant: "SUCCESS" },
  ERROR: { dot: "bg-amber-500", ring: "ring-amber-200", label: "Erroring", variant: "WARNING" },
  DOWN: { dot: "bg-red-500", ring: "ring-red-200", label: "Down", variant: "DANGER" },
  NEVER_SEEN: { dot: "bg-slate-300", ring: "ring-slate-200", label: "Never started", variant: "NEUTRAL" },
  UNKNOWN_PROCESS: { dot: "bg-slate-300", ring: "ring-slate-200", label: "Unknown", variant: "NEUTRAL" },
};

// A process being UP says nothing about whether it's actually DOING anything right now --
// discovery_scheduler loops and beats identically whether discovery_enabled is true or
// false, it just no-ops the tick when it's off. Found live: an operator switched discovery
// off from Settings and had no way anywhere in the CRM to confirm it had taken effect.
const TOGGLE_LABELS = {
  discovery_enabled: "Discovery",
  autonomous_outreach_enabled: "Autonomous outreach",
  auto_reply_enabled: "Auto-reply (low-risk objections)",
  acknowledgment_reply_enabled: "Acknowledgment reply",
};

// SQLite writes CURRENT_TIMESTAMP with no timezone marker, in UTC. Parsing the bare string
// would make the browser assume local time and shift every timestamp by the local offset
// (5.5h here) -- same trap the backend avoids by computing ages in SQL, and the same helper
// Dashboard.jsx already uses.
function parseUtc(s) {
  if (!s) return null;
  return new Date(s.replace(" ", "T") + "Z");
}

function humanAge(seconds) {
  if (seconds === null || seconds === undefined) return "—";
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

function humanUptime(startedAt) {
  const start = parseUtc(startedAt);
  if (!start) return null;
  const secs = Math.max(0, Math.floor((Date.now() - start.getTime()) / 1000));
  if (secs < 60) return `${secs}s`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ${Math.floor((secs % 3600) / 60)}m`;
  return `${Math.floor(secs / 86400)}d ${Math.floor((secs % 86400) / 3600)}h`;
}

function clockTime(s) {
  const d = parseUtc(s);
  return d ? d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : "—";
}

function ProcessCard({ proc }) {
  const ui = STATE_UI[proc.state] || STATE_UI.UNKNOWN_PROCESS;
  const uptime = humanUptime(proc.started_at);

  return (
    <div className={`rounded-xl border border-slate-200 bg-white p-4 ring-1 ring-inset ${ui.ring}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${ui.dot}`} />
            <h3 className="truncate text-sm font-semibold text-slate-900">
              {PROCESS_LABELS[proc.name] || proc.name}
            </h3>
          </div>
          <p className="mt-1 text-[11px] leading-snug text-slate-500">
            {PROCESS_BLURB[proc.name] || proc.name}
          </p>
        </div>
        <Badge variant={ui.variant}>{ui.label}</Badge>
      </div>

      <dl className="mt-3 space-y-1 border-t border-slate-100 pt-3 text-xs">
        <div className="flex justify-between gap-2">
          <dt className="text-slate-500">Last seen</dt>
          <dd className="font-medium text-slate-700">{humanAge(proc.age_seconds)}</dd>
        </div>
        {/* Uptime, not just "healthy": a process crash-looping under systemd's Restart=always
            shows "Running" on every poll -- only a resetting uptime reveals it. */}
        <div className="flex justify-between gap-2">
          <dt className="text-slate-500">Uptime</dt>
          <dd className="font-medium text-slate-700">{uptime || "—"}</dd>
        </div>
        {proc.expected_interval_seconds && (
          <div className="flex justify-between gap-2">
            <dt className="text-slate-500">Beats every</dt>
            <dd className="font-medium text-slate-700">{proc.expected_interval_seconds}s</dd>
          </div>
        )}
      </dl>

      <p className="mt-2 truncate font-mono text-[10px] text-slate-400" title={proc.name}>
        {proc.name}
      </p>
    </div>
  );
}

function AutomationToggles({ toggles }) {
  const entries = Object.entries(TOGGLE_LABELS);
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="text-sm font-semibold text-slate-900">Automation</h2>
      <p className="mt-1 text-xs text-slate-500">
        What's actually turned on right now -- a process can be running and still doing
        nothing if its switch is off.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        {entries.map(([key, label]) => {
          const on = Boolean(toggles?.[key]);
          return (
            <span
              key={key}
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${
                on
                  ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
                  : "bg-slate-100 text-slate-500 ring-slate-200"
              }`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${on ? "bg-emerald-500" : "bg-slate-400"}`} />
              {label}: {on ? "ON" : "OFF"}
            </span>
          );
        })}
      </div>
    </section>
  );
}

function JobBoard({ jobs }) {
  const byStatus = jobs?.by_status || {};
  const order = ["PENDING", "CLAIMED", "DONE", "FAILED", "DEAD"];
  const present = order.filter((s) => byStatus[s] !== undefined);
  const types = Object.entries(jobs?.by_type || {});

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="text-sm font-semibold text-slate-900">Job queue</h2>

      {present.length === 0 ? (
        <p className="mt-3 text-xs text-slate-400">No jobs in the queue.</p>
      ) : (
        <div className="mt-3 flex flex-wrap gap-2">
          {present.map((s) => {
            // DEAD is pulled out visually because it is the one state that always means a
            // human has to look -- it has exhausted every retry and nothing will move it on.
            const dead = s === "DEAD" && byStatus[s] > 0;
            return (
              <div
                key={s}
                className={`rounded-lg px-3 py-2 ring-1 ring-inset ${
                  dead ? "bg-red-50 ring-red-200" : "bg-slate-50 ring-slate-200"
                }`}
              >
                <div className={`text-lg font-semibold ${dead ? "text-red-700" : "text-slate-900"}`}>
                  {byStatus[s].toLocaleString()}
                </div>
                <div className={`text-[11px] font-medium ${dead ? "text-red-600" : "text-slate-500"}`}>
                  {dead && <AlertTriangle size={11} className="mr-0.5 inline align-[-1px]" />}
                  {s === "DEAD" ? "Stuck" : s.charAt(0) + s.slice(1).toLowerCase()}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {types.length > 0 && (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-left text-[11px] uppercase tracking-wide text-slate-400">
                <th className="pb-1.5 font-medium">Type</th>
                {present.map((s) => (
                  <th key={s} className="pb-1.5 text-right font-medium">
                    {s === "DEAD" ? "Stuck" : s.charAt(0) + s.slice(1).toLowerCase()}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {types.map(([type, counts]) => (
                <tr key={type}>
                  <td className="py-1.5 font-mono text-[11px] text-slate-700">{type}</td>
                  {present.map((s) => (
                    <td
                      key={s}
                      className={`py-1.5 text-right tabular-nums ${
                        s === "DEAD" && counts[s] ? "font-semibold text-red-600" : "text-slate-600"
                      }`}
                    >
                      {counts[s] ?? <span className="text-slate-300">–</span>}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function ActivityFeed({ activity }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex items-center gap-2">
        <Activity size={15} className="text-slate-400" />
        <h2 className="text-sm font-semibold text-slate-900">Live activity</h2>
      </div>

      {activity.length === 0 ? (
        <p className="mt-3 text-xs text-slate-400">
          Nothing has happened yet. The system is connected and idle.
        </p>
      ) : (
        <ul className="mt-3 divide-y divide-slate-100">
          {activity.map((a, i) => (
            <li key={i} className="flex items-baseline gap-3 py-2 text-xs">
              <span className="w-16 shrink-0 font-mono text-[11px] text-slate-400">
                {clockTime(a.created_at)}
              </span>
              <span className="w-24 shrink-0 font-semibold text-slate-700">{a.agent}</span>
              <span className="min-w-0 flex-1 truncate text-slate-600">
                {a.company_name || <span className="italic text-slate-400">product-level</span>}
                <span className="text-slate-400"> · {a.action_type}</span>
              </span>
              {a.outcome && (
                <span className="shrink-0 text-[11px] text-slate-500">{a.outcome}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function SystemMonitor() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [lastOk, setLastOk] = useState(null);
  const timer = useRef(null);

  const load = useCallback(async () => {
    try {
      const d = await api.getSystemLive();
      setData(d);
      setError(null);
      setLastOk(new Date());
    } catch (e) {
      // Deliberately keep the last good `data` on screen alongside the error banner --
      // blanking the page would throw away the most recent known-good picture at exactly
      // the moment the operator most wants to see it.
      setError(e.message || "request failed");
    }
  }, []);

  useEffect(() => {
    load();
    timer.current = setInterval(load, POLL_MS);
    return () => clearInterval(timer.current);
  }, [load]);

  // Three distinct states, never collapsed into one. An empty page that looks identical to
  // a dead backend manufactures false confidence -- "all quiet" when nothing is answering
  // at all is the exact failure this whole phase exists to prevent.
  if (!data && !error) {
    return (
      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <RefreshCw size={14} className="animate-spin" />
          Loading system state…
        </div>
      </main>
    );
  }

  const processes = data?.processes || [];
  const problems = processes.filter((p) => p.state === "DOWN" || p.state === "ERROR");

  return (
    <main className="mx-auto max-w-7xl space-y-5 px-6 py-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-slate-900">System</h1>
          <p className="text-xs text-slate-500">
            What the background system is doing right now. Refreshes every {POLL_MS / 1000}s.
          </p>
        </div>
        <div className="text-right text-[11px] text-slate-400">
          {lastOk ? `Updated ${lastOk.toLocaleTimeString()}` : "Not yet updated"}
        </div>
      </header>

      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <div>
            <p className="font-semibold">Can’t reach the backend</p>
            <p className="mt-0.5 text-xs text-red-700">
              {error}
              {data && " — showing the last known state below, which may be out of date."}
            </p>
          </div>
        </div>
      )}

      {!error && problems.length > 0 && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <p>
            <span className="font-semibold">
              {problems.length} process{problems.length > 1 ? "es" : ""} need attention:
            </span>{" "}
            {problems.map((p) => PROCESS_LABELS[p.name] || p.name).join(", ")}
          </p>
        </div>
      )}

      <section>
        <div className="mb-2 flex items-baseline justify-between">
          <h2 className="text-sm font-semibold text-slate-900">Background processes</h2>
          <span className="text-[11px] text-slate-400">
            API: <span className="font-semibold text-emerald-600">up</span>
          </span>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {processes.map((p) => (
            <ProcessCard key={p.name} proc={p} />
          ))}
        </div>
      </section>

      <AutomationToggles toggles={data?.toggles} />

      <div className="grid gap-5 lg:grid-cols-2">
        <JobBoard jobs={data?.jobs} />
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold text-slate-900">Leads mid-outreach</h2>
          <p className="mt-3 text-3xl font-semibold text-slate-900">
            {data?.leads_in_flight ?? "—"}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Currently being sent to. A lead sitting here for a long time means a send was
            interrupted — Step 6.4 will flag those automatically.
          </p>
        </section>
      </div>

      <ActivityFeed activity={data?.activity || []} />
    </main>
  );
}
