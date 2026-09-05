import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight, Plus, Sparkles, Clock } from "lucide-react";
import { api } from "../api/client";
import CampaignFormModal from "./CampaignFormModal";

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
  // Step 18.1 follow-up (2026-09-02) -- proactive, product-scoped suggestions surfaced
  // BEFORE any campaign exists, so a human can act on one in a click instead of waiting
  // to notice a gap themselves. `_run_daily_plan_tick` already generates these daily.
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    api.listCampaigns().then(setCampaigns).catch((err) => setError(err.message));
    api.listProducts().then(setProducts).catch(() => {});
    api.listCampaignSuggestions().then(setSuggestions).catch(() => {});
  }, []);

  function openFormFromSuggestion(s) {
    setFormPrefill({
      product_id: s.product_id,
      target_segment: s.target_segment,
      lead_count_goal: s.lead_count_goal,
      suggestion: s.suggestion,
    });
    setFormDate(todayKey);
  }

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
  const monthLabel = new Date(cursor.year, cursor.month, 1).toLocaleDateString("en-US", {
    month: "long", year: "numeric",
  });

  function shiftMonth(delta) {
    setCursor((c) => {
      const d = new Date(c.year, c.month + delta, 1);
      return { year: d.getFullYear(), month: d.getMonth() };
    });
  }

  if (error) return <p className="text-xs text-alert-600">Couldn't reach the backend: {error}</p>;

  return (
    <div>
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="font-display text-lg font-semibold text-ink-900">{monthLabel}</h2>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <button
              onClick={() => shiftMonth(-1)}
              className="rounded-md p-1.5 text-ink-500 hover:bg-parchment-raised-2 hover:text-ink-900"
              aria-label="Previous month"
            >
              <ChevronLeft size={16} />
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

      {suggestions.length > 0 && (
        <div className="mb-3 flex flex-col gap-1.5">
          {suggestions.map((s) => (
            <div
              key={s.product_id}
              className="flex items-start justify-between gap-3 rounded-lg border border-dashed border-gold-600 bg-gold-100 p-2.5"
            >
              <div className="flex items-start gap-2 min-w-0">
                <Sparkles size={13} className="mt-0.5 shrink-0 text-gold-700" />
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-ink-900">{s.product_title}</p>
                  <p className="mt-0.5 text-[11px] text-ink-700">{s.suggestion}</p>
                </div>
              </div>
              <button
                onClick={() => openFormFromSuggestion(s)}
                className="shrink-0 rounded-md bg-gold-600 px-2.5 py-1.5 text-[11px] font-semibold text-white hover:opacity-90"
              >
                Create this campaign
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-7 gap-1.5">
        {WEEKDAYS.map((w) => (
          <div key={w} className="px-1 pb-1 font-mono text-[10px] font-semibold uppercase tracking-wide text-ink-500">
            {w}
          </div>
        ))}

        {campaigns === null &&
          Array.from({ length: 7 }).map((_, i) => (
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
                title={clickableEmpty ? "Click to start a campaign on this day" : undefined}
                className={`group flex min-h-24 flex-col gap-1 rounded-lg border p-1.5 ${
                  dayCampaigns.length > 0
                    ? "border-gold-500 bg-gold-100"
                    : "border-line bg-parchment-raised"
                } ${inMonth ? "" : "opacity-40"} ${
                  clickableEmpty ? "cursor-pointer hover:border-gold-500 hover:bg-gold-100/60" : ""
                }`}
              >
                <span
                  className={`font-mono text-[10px] ${
                    isToday ? "font-bold text-gold-700" : "text-ink-500"
                  }`}
                >
                  {d.getDate()}
                </span>
                {dayCampaigns.length === 0 ? (
                  <span className="hidden text-[10px] font-medium text-gold-700 group-hover:inline">
                    {clickableEmpty ? "+ Add" : ""}
                  </span>
                ) : (
                  dayCampaigns.map((c) => {
                    // Review-pending indicator (UI Phase 16 revision, 2026-09-02) -- the
                    // Daily Review card itself lives on this campaign's own Detail page now,
                    // not as a flat Dashboard list, so the calendar box is what has to show
                    // "this one needs a look today" instead. Reuses `last_approved_date`
                    // already present on every campaign the list endpoint returns -- no
                    // extra fetch per box.
                    const activeStatus = ["PROPOSED", "APPROVED", "RUNNING"].includes(c.status);
                    const reviewPending = activeStatus && c.last_approved_date !== todayKey;
                    return (
                      <div
                        key={c.id}
                        role="button"
                        tabIndex={0}
                        onClick={() => navigate(`/campaigns/${c.id}`)}
                        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && navigate(`/campaigns/${c.id}`)}
                        title="Open campaign"
                        className="cursor-pointer rounded-md bg-parchment-raised-2 px-1.5 py-1 hover:bg-parchment-raised"
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
            // the suggestion this campaign came from (if any) is now acted-on -- drop it
            // locally instead of waiting for a refetch, same product_id can't suggest twice.
            setSuggestions((prev) => prev.filter((s) => s.product_id !== created.product_id));
            setFormDate(null);
            setFormPrefill(null);
          }}
        />
      )}
    </div>
  );
}
