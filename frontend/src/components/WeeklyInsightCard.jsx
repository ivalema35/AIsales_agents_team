import { useEffect, useState } from "react";
import { Lightbulb, TrendingUp, TrendingDown } from "lucide-react";
import { api } from "../api/client";

// Step 19.5 -- the human-visible face of Phase 19's reflection engine. Without this
// card, ACTIVE strategy_insights only feed the daily strategist's prompt (Step 19.4)
// and the operator never *sees* that the system learned anything. Plain language, gold
// accent (AI-authored signal per design system), no edit controls -- insights are
// written by reflection, never by typing into this UI (Step 19.6).

function ConfidencePill({ confidence }) {
  if (confidence == null) return null;
  const pct = Math.round(confidence * 100);
  const strong = confidence >= 0.7;
  return (
    <span
      className={`shrink-0 rounded-full px-2 py-0.5 font-mono text-[10px] font-semibold ${
        strong ? "bg-good-100 text-good-700" : "bg-gold-100 text-gold-700"
      }`}
    >
      {pct}% sure
    </span>
  );
}

function InsightCard({ insight }) {
  return (
    <article className="rounded-lg border border-gold-600/25 bg-gold-100/40 p-4 transition-colors hover:border-gold-600/40">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-mono text-[10px] font-semibold uppercase tracking-wide text-gold-700">
            {insight.domain}
            {insight.product_title && (
              <span className="font-sans font-normal normal-case tracking-normal text-ink-500">
                {" "}
                · {insight.product_title}
              </span>
            )}
          </p>
          <h3 className="mt-1.5 font-display text-sm font-semibold leading-snug text-ink-900">
            “{insight.winning_angle}” works better
            {insight.losing_angle ? (
              <span className="font-sans font-normal text-ink-700">
                {" "}
                than “{insight.losing_angle}”
              </span>
            ) : null}
          </h3>
        </div>
        <ConfidencePill confidence={insight.confidence} />
      </div>

      {insight.rationale && (
        <p className="mt-2.5 text-xs leading-relaxed text-ink-700">{insight.rationale}</p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-gold-600/15 pt-2.5 text-[11px]">
        <span className="flex items-center gap-1 text-good-700">
          <TrendingUp size={12} /> Winning angle
        </span>
        {insight.losing_angle && (
          <span className="flex items-center gap-1 text-ink-500">
            <TrendingDown size={12} /> Losing compared
          </span>
        )}
        {insight.created_at && (
          <span className="ml-auto font-mono text-ink-500">
            {String(insight.created_at).slice(0, 10)}
          </span>
        )}
      </div>
    </article>
  );
}

export default function WeeklyInsightCard() {
  const [insights, setInsights] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .listStrategyInsights({ limit: 5 })
      .then(setInsights)
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return (
      <p className="rounded-lg bg-alert-100 px-4 py-3 text-sm text-alert-700">
        Couldn't load strategy insights: {error}
      </p>
    );
  }

  if (!insights) {
    return <div className="h-28 animate-pulse rounded-lg bg-parchment-raised-2" />;
  }

  return (
    <section className="rounded-xl border border-line bg-parchment-raised p-5 shadow-sm">
      <div className="mb-4 flex items-start gap-3">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gold-100 text-gold-700">
          <Lightbulb size={16} />
        </span>
        <div className="min-w-0">
          <h2 className="font-display text-base font-semibold text-ink-900">What the AI learned</h2>
          <p className="mt-0.5 text-xs text-ink-500">
            Validated strategy rules from real outreach numbers — used in the next daily plan once
            you approve it. Not guesses.
          </p>
        </div>
      </div>

      {insights.length === 0 ? (
        <div className="rounded-lg border border-dashed border-line bg-parchment px-4 py-8 text-center">
          <p className="text-sm font-medium text-ink-700">No validated insights yet</p>
          <p className="mx-auto mt-1.5 max-w-md text-xs leading-relaxed text-ink-500">
            Once enough real sends land for a domain (past the sample-size floor), a weekly
            reflection writes a plain-language rule here — e.g. which pitch angle actually got
            more replies. Until then the daily strategist still plans from live metrics alone.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {insights.map((insight) => (
            <InsightCard key={insight.id} insight={insight} />
          ))}
        </div>
      )}
    </section>
  );
}
