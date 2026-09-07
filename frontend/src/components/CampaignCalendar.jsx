import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight, Plus, Clock, Target } from "lucide-react";
import { api } from "../api/client";
import CampaignFormModal from "./CampaignFormModal";
import { industryLabel } from "../lib/targetSegment";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function toDateKey(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

// Monday-first 6-row grid covering the given month, including the leading/trailing days
// from adjacent months needed to fill whole weeks.
function buildMonthGrid(year, month) {
  const first = new Date(year, month, 1);
  const startOffset = (first.getDay() + 6) % 7; // 0=Mon
  const gridStart = new Date(year, month, 1 - startOffset);
  return Array.from({ length: 42 }, (_, i) => {
    const d = new Date(gridStart);
    d.setDate(gridStart.getDate() + i);
    return d;
  });
}

const STATUS_LABEL = {
  PROPOSED: "Proposed",
  APPROVED: "Approved",
  RUNNING: "Running",
  COMPLETED: "Completed",
  PAUSED: "Paused",
};

// Phase 17 Step 17.4 -- replaces the old Pipeline Kanban as the dashboard's primary view
// (the operator's own explicit ask: the pipeline grid goes away, not just gets demoted).
// A lead-level breakdown by stage is still available on the Leads page's own table+filter
// UI (unrelated component, untouched) -- nothing about "which lead is in which stage" was
// actually lost, only this specific grid.
export default function CampaignCalendar() {
  const navigate = useNavigate();
  const [cursor, setCursor] = useState(() => {
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() };
  });
  const [campaigns, setCampaigns] = useState(null);
  const [products, setProducts] = useState([]);
  const [error, setError] = useState(null);
  const [formDate, setFormDate] = useState(null); // non-null (incl. "") shows the create form
  const [formPrefill, setFormPrefill] = useState(null);
  // Phase 21 -- "review pending" now means "this campaign has >=1 real PENDING to-do",
  // not the old whole-day last_approved_date flag (that concept no longer exists -- every
  // to-do is individually resolved in the unified AI Manager Inbox on the Dashboard, not
  // here). A cheap single fetch, same real-item volume as the inbox itself.
  const [campaignIdsWithPendingTodo, setCampaignIdsWithPendingTodo] = useState(new Set());

  useEffect(() => {
    api.listCampaigns().then(setCampaigns).catch((err) => setError(err.message));
    api.listProducts().then(setProducts).catch(() => {});
    api.listTodos()
      .then((items) => setCampaignIdsWithPendingTodo(new Set(items.map((i) => i.campaign_id).filter(Boolean))))
      .catch(() => {});
  }, []);

  const productTitle = useMemo(() => {
    const map = {};
    for (const p of products) map[p.id] = p.title;
    return map;
  }, [products]);

  const campaignsByDate = useMemo(() => {
    const map = {};
    for (const c of campaigns || []) {
      if (!c.scheduled_date) continue;
      (map[c.scheduled_date] ||= []).push(c);
    }
    return map;
  }, [campaigns]);

  const grid = useMemo(() => buildMonthGrid(cursor.year, cursor.month), [cursor]);
  const todayKey = toDateKey(new Date());
  const viewingCurrentMonth =
    cursor.year === new Date().getFullYear() && cursor.month === new Date().getMonth();
  const monthLabel = new Date(cursor.year, cursor.month, 1).toLocaleDateString("en-US", {
    month: "long", year: "numeric",
  });

  function shiftMonth(delta) {
    setCursor((c) => {
      const d = new Date(c.year, c.month + delta, 1);
      return { year: d.getFullYear(), month: d.getMonth() };
    });
  }

  function goToday() {
    const now = new Date();
    setCursor({ year: now.getFullYear(), month: now.getMonth() });
  }

  if (error) return <p className="text-xs text-alert-600">Couldn't reach the backend: {error}</p>;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-display text-lg font-semibold text-ink-900">{monthLabel}</h2>
        <div className="flex items-center gap-2">
          <div className="flex items-center rounded-lg border border-line bg-parchment-raised p-0.5">
            <button
              onClick={() => shiftMonth(-1)}
              className="rounded-md p-1.5 text-ink-500 hover:bg-parchment-raised-2 hover:text-ink-900"
              aria-label="Previous month"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={goToday}
              disabled={viewingCurrentMonth}
              className="rounded-md px-2.5 py-1 font-mono text-[10px] font-semibold uppercase tracking-wide text-ink-700 hover:bg-parchment-raised-2 hover:text-ink-900 disabled:cursor-default disabled:opacity-40"
              title="Jump to this month"
            >
              Today
            </button>
            <button
              onClick={() => shiftMonth(1)}
              className="rounded-md p-1.5 text-ink-500 hover:bg-parchment-raised-2 hover:text-ink-900"
              aria-label="Next month"
            >
              <ChevronRight size={16} />
            </button>
          </div>
          <button
            onClick={() => { setFormPrefill(null); setFormDate(todayKey); }}
            className="flex items-center gap-1.5 rounded-md bg-gold-600 px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90"
          >
            <Plus size={13} /> New campaign
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-line bg-parchment-raised p-2 sm:p-3">
        <div className="grid grid-cols-7 gap-1 sm:gap-1.5">
          {WEEKDAYS.map((w) => (
            <div
              key={w}
              className="px-1 pb-2 text-center font-mono text-[10px] font-semibold uppercase tracking-wide text-ink-500"
            >
              {w}
            </div>
          ))}

          {campaigns === null &&
            Array.from({ length: 14 }).map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-lg bg-parchment-raised-2" />
            ))}

          {campaigns !== null &&
            grid.map((d) => {
              const key = toDateKey(d);
              const inMonth = d.getMonth() === cursor.month;
              const dayCampaigns = campaignsByDate[key] || [];
              const isToday = key === todayKey;
              const isPast = key < todayKey;
              const clickableEmpty = dayCampaigns.length === 0 && inMonth && !isPast;
              return (
                <div
                  key={key}
                  role={clickableEmpty ? "button" : undefined}
                  tabIndex={clickableEmpty ? 0 : undefined}
                  onClick={clickableEmpty ? () => { setFormPrefill(null); setFormDate(key); } : undefined}
                  onKeyDown={
                    clickableEmpty
                      ? (e) => (e.key === "Enter" || e.key === " ") && (setFormPrefill(null), setFormDate(key))
                      : undefined
                  }
                  title={
                    isToday
                      ? (clickableEmpty ? "Today -- click to start a campaign" : "Today")
                      : clickableEmpty
                      ? "Click to start a campaign on this day"
                      : undefined
                  }
                  className={`group relative flex min-h-24 flex-col gap-1 rounded-lg border p-1.5 transition-colors ${
                    isToday
                      ? "border-gold-600 bg-gold-100 shadow-[inset_0_0_0_1px_rgba(184,137,44,0.35)]"
                      : dayCampaigns.length > 0
                      ? "border-gold-500 bg-gold-100/80"
                      : "border-line bg-parchment-raised-2"
                  } ${inMonth ? "" : "opacity-35"} ${
                    isPast && inMonth && !isToday && dayCampaigns.length === 0 ? "opacity-55" : ""
                  } ${
                    clickableEmpty
                      ? "cursor-pointer hover:border-gold-600 hover:bg-gold-100"
                      : ""
                  }`}
                >
                  <div className="flex items-start justify-between gap-1">
                    {isToday ? (
                      <span className="inline-flex items-center gap-1">
                        <span className="rounded-md bg-gold-600 px-1.5 py-0.5 font-mono text-[10px] font-bold leading-none text-white">
                          {d.getDate()}
                        </span>
                        <span className="hidden font-mono text-[8px] font-semibold uppercase tracking-wide text-gold-700 sm:inline">
                          Today
                        </span>
                      </span>
                    ) : (
                      <span
                        className={`font-mono text-[10px] ${
                          inMonth ? "font-medium text-ink-700" : "text-ink-500"
                        }`}
                      >
                        {d.getDate()}
                      </span>
                    )}
                  </div>
                  {dayCampaigns.length === 0 ? (
                    clickableEmpty && (
                      <span
                        className={`mt-auto text-[10px] font-medium text-gold-700 ${
                          isToday ? "opacity-90" : "opacity-0 group-hover:opacity-100"
                        }`}
                      >
                        + Add
                      </span>
                    )
                  ) : (
                    dayCampaigns.map((c) => {
                      // Review-pending indicator (UI Phase 16 revision, 2026-09-02; Phase 21
                      // revision 2026-09-05) -- shows whenever this campaign has a real
                      // PENDING to-do waiting in the unified AI Manager Inbox (Dashboard).
                      const reviewPending = campaignIdsWithPendingTodo.has(c.id);
                      return (
                        <div
                          key={c.id}
                          role="button"
                          tabIndex={0}
                          onClick={() => navigate(`/campaigns/${c.id}`)}
                          onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && navigate(`/campaigns/${c.id}`)}
                          title="Open campaign"
                          className="cursor-pointer rounded-md border border-line/60 bg-parchment-raised px-1.5 py-1 shadow-sm hover:border-gold-500 hover:bg-parchment-raised-2"
                        >
                          <div className="flex items-start justify-between gap-1">
                            <p className="truncate text-[11px] font-semibold text-ink-900" title={c.name}>
                              {c.name}
                            </p>
                            {reviewPending && (
                              <Clock size={10} className="mt-0.5 shrink-0 text-gold-700" aria-label="Review pending" />
                            )}
                          </div>
                          <p className="truncate text-[9px] text-ink-500">
                            {productTitle[c.product_id] || "—"} · {STATUS_LABEL[c.status] || c.status}
                          </p>
                          {/* 2026-09-07, user-flagged real gap: approving a targeting proposal
                              changed the real campaign row, but nowhere on the calendar showed
                              it -- a human had no quick way to confirm "yes, this campaign is
                              now actually targeted." */}
                          {(c.target_segment?.industry || c.target_segment?.location) && (
                            <p className="flex items-center gap-1 truncate text-[9px] text-gold-700">
                              <Target size={9} className="shrink-0" />
                              {industryLabel(c.target_segment) || "—"}
                              {c.target_segment.location && ` · ${c.target_segment.location}`}
                            </p>
                          )}
                          <div className="mt-0.5 flex flex-wrap gap-1 font-mono text-[9px] text-gold-700">
                            <span>{c.metrics.sent} sent</span>
                            <span>{c.metrics.opened} opened</span>
                            {c.metrics.hot > 0 && <span className="text-alert-600">{c.metrics.hot} hot</span>}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              );
            })}
        </div>
      </div>

      {campaigns !== null && campaigns.length === 0 && (
        <p className="mt-3 text-xs text-ink-500">
          No campaigns yet -- click "New campaign" above, or any empty day, to create the first one.
        </p>
      )}

      {formDate !== null && (
        <CampaignFormModal
          products={products}
          defaultDate={formDate}
          prefill={formPrefill}
          onClose={() => { setFormDate(null); setFormPrefill(null); }}
          onCreated={(created) => {
            setCampaigns((prev) => [created, ...(prev || [])]);
            setFormDate(null);
            setFormPrefill(null);
          }}
        />
      )}
    </div>
  );
}
