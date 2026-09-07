import { useEffect, useState } from "react";
import { AlertTriangle, BookOpen, ChevronDown, ChevronUp, MessageSquareWarning } from "lucide-react";
import { api } from "../api/client";
import TodoItemCard from "./TodoItemCard";

// UI Phase 16 revision (2026-09-02): no longer rendered as a flat, cross-campaign list on
// the Dashboard -- it moved onto each campaign's own Detail page (CampaignDetail.jsx),
// scoped to that one campaign, per the operator's own "campaign ke around sab kuch" ask.
// Phase 21 (2026-09-05): the to-do list + single whole-day Approve button are gone --
// this campaign's real PENDING TodoItems render via the SAME per-item TodoItemCard the
// Dashboard's AI Manager Inbox uses (never two independently-drifting card designs),
// each individually feedback-able/approved/dismissed. Everything else on this card
// (watchdog banner, journal, sample-draft preview/feedback, HTML/TEXT chips) is
// unaffected -- none of it ever went through daily_todo/approve_campaign_today.
export function CampaignReviewCard({ campaign, onApproved }) {
  const [review, setReview] = useState(null);
  const [expanded, setExpanded] = useState(true);
  const [showFeedback, setShowFeedback] = useState(false);
  const [instruction, setInstruction] = useState("");
  const [revising, setRevising] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [pushback, setPushback] = useState(null);
  const [error, setError] = useState(null);
  const [clearingWatchdog, setClearingWatchdog] = useState(false);
  const [journalExpanded, setJournalExpanded] = useState(false);
  const [settingMode, setSettingMode] = useState(false);

  useEffect(() => {
    api.getCampaignDailyReview(campaign.id).then(setReview).catch((err) => setError(err.message));
  }, [campaign.id]);

  // A to-do's proposal (target_segment/lead_count_goal/strategy_angle/email_render_mode)
  // applies to the real campaign row the moment ITS OWN card is approved (TodoItemCard's
  // own logic) -- this just drops the resolved item from the list and tells the parent
  // page (CampaignDetail) to refresh, since the campaign's own header/progress bar may
  // now be stale (a targeting/angle change did just land on the real row).
  function handleTodoResolved(id) {
    setReview((r) => ({ ...r, todo_items: r.todo_items.filter((i) => i.id !== id) }));
    onApproved?.();
  }

  async function setEmailRenderMode(mode) {
    if (!mode || mode === review?.email_render_mode) return;
    setSettingMode(true);
    setError(null);
    try {
      await api.setCampaignEmailRenderMode(campaign.id, mode);
      const fresh = await api.getCampaignDailyReview(campaign.id);
      setReview(fresh);
      setExpanded(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setSettingMode(false);
    }
  }

  // Phase 16 Step 16.5's existing revise-draft endpoint, reused here for the daily
  // review's own sample draft -- the human's free-text instruction reshapes THIS
  // preview; approving still needs a separate click afterward, feedback never
  // auto-approves. Sends the CURRENT draft back each time (2026-09-01, user-flagged
  // real gap) so a second/third round of feedback builds on every earlier accepted
  // edit instead of silently forgetting it.
  async function submitFeedback(e) {
    e.preventDefault();
    if (!instruction.trim()) return;
    // Kickoff template (no real lead yet) uses the campaign-scoped revise endpoint;
    // a real sample lead still uses the existing Step 16.5 lead revise path.
    if (!review?.sample_is_kickoff_template && !review?.sample_lead_id) return;
    setRevising(true);
    setError(null);
    try {
      const result = review.sample_is_kickoff_template
        ? await api.reviseKickoffDraft(campaign.id, instruction, review.sample_draft)
        : await api.reviseOutreachDraft(review.sample_lead_id, instruction, review.sample_draft);
      const { draft, ai_suggestion, pushback: newPushback, email_render_mode, sample_draft_html } = result;
      setReview((r) => ({
        ...r,
        sample_draft: draft,
        ...(email_render_mode ? { email_render_mode } : {}),
        ...(sample_draft_html !== undefined ? { sample_draft_html } : {}),
      }));
      setAiSuggestion(ai_suggestion);
      // Phase 20 Step 20.4 -- an honest, additive disagreement, if the instruction
      // genuinely conflicted with real data. The draft above already reflects the
      // instruction exactly as given either way; this is shown alongside it, never
      // instead of it.
      setPushback(newPushback || null);
      setInstruction("");
      setShowFeedback(false);
      setExpanded(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setRevising(false);
    }
  }

  // Phase 20 Step 20.3 -- the only way a real watchdog alert clears: an explicit human
  // decision here. Never automatic, never re-checked by the system on its own.
  async function resumeSending() {
    setClearingWatchdog(true);
    setError(null);
    try {
      await api.clearCampaignWatchdogAlert(campaign.id);
      setReview((r) => ({ ...r, watchdog_alert: null }));
    } catch (err) {
      setError(err.message);
    } finally {
      setClearingWatchdog(false);
    }
  }

  // Initial load failure only — action errors (mode chip / feedback / approve) stay inline
  // so a 404 on a new route never wipes the whole review card.
  if (!review && error) return <p className="text-xs text-alert-600">{campaign.name}: {error}</p>;
  if (!review) return <div className="h-16 animate-pulse rounded-lg bg-parchment-raised-2" />;

  return (
    <div className="rounded-xl border border-line bg-parchment-raised p-5 shadow-sm">
      {error && (
        <p className="mb-2 text-xs text-alert-600">{error}</p>
      )}
      {review.watchdog_alert && (
        <div className="mb-4 rounded-md border border-alert-600 bg-alert-100 p-3">
          <span className="flex items-center gap-1.5 text-[11px] font-semibold text-alert-700">
            <AlertTriangle size={13} /> Sending paused — {review.watchdog_alert.bounce_count} sends failed in a row
          </span>
          <p className="mt-1.5 text-xs leading-relaxed text-ink-900">{review.watchdog_alert.message}</p>
          <button
            onClick={resumeSending}
            disabled={clearingWatchdog}
            className="mt-2 rounded-md bg-ink-900 px-3 py-1.5 text-[11px] font-semibold text-parchment-raised hover:opacity-90 disabled:opacity-50"
          >
            {clearingWatchdog ? "Resuming…" : "Resume sending for this campaign"}
          </button>
        </div>
      )}

      <div className="min-w-0">
        <h2 className="font-display text-lg font-semibold text-ink-900">AI Sales Manager</h2>
        <p className="mt-0.5 text-xs text-ink-500">
          Suggestions, notes, and a sample message for this campaign — review and approve what you agree with.
        </p>
      </div>

      {review.todo_items.length > 0 ? (
        <div className="mt-4 flex flex-col gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-500">Needs your decision</p>
          {review.todo_items.map((item) => (
            <TodoItemCard key={item.id} item={item} onResolved={handleTodoResolved} />
          ))}
        </div>
      ) : (
        <p className="mt-4 rounded-md border border-line bg-parchment px-3 py-2.5 text-sm text-ink-600">
          {campaign.status === "PROPOSED"
            ? "No AI suggestions waiting right now. Campaign status can still say Draft even after leads are found — use Mark as approved at the top if you want to formally OK the plan."
            : "Nothing new to decide today — no fresh AI suggestions for this campaign."}
        </p>
      )}

      {/* Phase 20 Step 20.1 -- the strategist's own persistent, dated narrative for this
          campaign, separate from today's todo/proposal. Today's entry may not exist yet
          if generate_campaign_todo hasn't run today (e.g. a review opened before the
          daily tick) -- in that case there's simply nothing to show, no placeholder. */}
      {(review.journal || review.recent_journal?.length > 0) && (
        <div className="mt-4 border-t border-line pt-4">
          <button
            onClick={() => setJournalExpanded((e) => !e)}
            className="flex items-center gap-1.5 text-xs font-medium text-ink-600 hover:text-ink-900"
          >
            {journalExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            <BookOpen size={13} /> AI&apos;s notes on this campaign
          </button>
          {journalExpanded && (
            <div className="mt-2 flex flex-col gap-2">
              {[...(review.recent_journal || []), ...(review.journal ? [review.journal] : [])].map((entry, i) => (
                <div key={entry.day ?? i} className="rounded-md border border-line bg-parchment p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-ink-500">{entry.day}</p>
                  <p className="mt-1 text-xs leading-relaxed text-ink-900">{entry.hypothesis}</p>
                  {entry.observation && (
                    <p className="mt-1.5 text-xs text-ink-700">
                      <span className="font-semibold text-ink-600">What we saw:</span> {entry.observation}
                    </p>
                  )}
                  {entry.pivot_decision && (
                    <p className="mt-1 text-xs text-gold-700">
                      <span className="font-semibold">Changing approach:</span> {entry.pivot_decision}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {review.sample_draft ? (
        <div className="mt-4 border-t border-line pt-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <button
              onClick={() => setExpanded((e) => !e)}
              className="flex items-center gap-1.5 text-xs font-medium text-ink-600 hover:text-ink-900"
            >
              {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              {review.sample_is_kickoff_template
                ? "Preview: starter message template"
                : `Preview: sample message${review.sample_lead_company ? ` for ${review.sample_lead_company}` : ""}`}
            </button>
            <div className="flex items-center gap-1">
              <button
                type="button"
                disabled={settingMode || review.email_render_mode === "HTML"}
                onClick={() => setEmailRenderMode("HTML")}
                className={`rounded-md px-2.5 py-1 text-[11px] font-semibold disabled:opacity-60 ${
                  review.email_render_mode === "HTML"
                    ? "bg-ink-900 text-parchment-raised"
                    : "bg-parchment-raised-2 text-ink-500 hover:text-ink-900"
                }`}
              >
                Formatted email
              </button>
              <button
                type="button"
                disabled={settingMode || review.email_render_mode === "TEXT"}
                onClick={() => setEmailRenderMode("TEXT")}
                className={`rounded-md px-2.5 py-1 text-[11px] font-semibold disabled:opacity-60 ${
                  review.email_render_mode === "TEXT"
                    ? "bg-ink-900 text-parchment-raised"
                    : "bg-parchment-raised-2 text-ink-500 hover:text-ink-900"
                }`}
              >
                Simple text
              </button>
            </div>
          </div>
          {expanded && (
            <div className="mt-2 flex flex-col gap-2.5">
              <p className="text-[10px] italic text-ink-500">
                {review.sample_is_kickoff_template ? (
                  <>
                    No leads tagged yet -- this is a <span className="font-medium">template</span> using
                    literal <span className="font-medium">[Business Name]</span> and{" "}
                    <span className="font-medium">[Pain Point]</span>. Shape and tone only; each real
                    send later fills that lead&apos;s own name and pain. Give feedback below to reshape
                    it before Approve.
                  </>
                ) : (
                  <>
                    This is a real, worked example -- not a copy sent as-is. [Business Name] here ={" "}
                    <span className="font-medium">{review.sample_lead_company}</span>
                    {review.sample_pain_points?.length > 0 && (
                      <> · [Pain Point] here = <span className="font-medium">{review.sample_pain_points[0]}</span></>
                    )}
                    . Each real lead&apos;s own message uses their own real business name and pain point.
                  </>
                )}
              </p>
              {review.email_render_mode === "HTML" && review.sample_draft_html ? (
                <div className="overflow-hidden rounded-md border border-line bg-white">
                  <iframe
                    title="Email HTML preview"
                    srcDoc={review.sample_draft_html}
                    sandbox=""
                    className="h-[420px] w-full border-0 bg-white"
                  />
                </div>
              ) : (
                <div className="rounded-md bg-parchment-raised-2 p-2.5">
                  <p className="text-xs font-semibold text-ink-900">{review.sample_draft.subject}</p>
                  <p className="mt-1 whitespace-pre-line text-xs text-ink-700">{review.sample_draft.body}</p>
                </div>
              )}

              {/* Phase 20 Step 20.4 -- an honest, additive disagreement when the instruction
                  above genuinely conflicted with real data. The draft already reflects the
                  instruction as given; this never blocks or undoes that, it's shown
                  alongside so a human sees the AI's real reaction, not silent compliance. */}
              {pushback && (
                <div className="rounded-md border border-dashed border-alert-600 bg-alert-100 p-2.5">
                  <span className="flex items-center gap-1.5 text-[11px] font-semibold text-alert-700">
                    <MessageSquareWarning size={11} /> AI&apos;s honest take
                  </span>
                  <p className="mt-1 text-xs text-ink-900">{pushback}</p>
                </div>
              )}

              {aiSuggestion && (
                <div className="rounded-md border border-dashed border-gold-600 bg-gold-100 p-2.5">
                  <span className="text-[11px] font-semibold text-gold-700">
                    AI also suggests
                  </span>
                  <p className="mt-1 text-xs text-ink-900">{aiSuggestion}</p>
                </div>
              )}

              {showFeedback ? (
                <form onSubmit={submitFeedback} className="flex flex-col gap-1.5">
                  <input
                    autoFocus
                    value={instruction}
                    onChange={(e) => setInstruction(e.target.value)}
                    placeholder="e.g. isko formal karo, ek ROI line add karo"
                    className="rounded-md border border-line bg-parchment-raised px-2.5 py-1.5 text-xs text-ink-900 placeholder:text-ink-500 focus:border-gold-500 focus:outline-none"
                  />
                  <div className="flex items-center gap-2">
                    <button
                      type="submit"
                      disabled={revising || !instruction.trim()}
                      className="rounded-md bg-gold-600 px-3 py-1.5 text-[11px] font-semibold text-white hover:opacity-90 disabled:opacity-50"
                    >
                      {revising ? "Revising…" : "Regenerate"}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowFeedback(false)}
                      className="text-[11px] font-medium text-ink-500 hover:text-ink-900"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              ) : (
                <button
                  onClick={() => setShowFeedback(true)}
                  className="w-fit text-[11px] font-medium text-ink-500 hover:text-ink-900"
                >
                  Give feedback
                </button>
              )}
            </div>
          )}
        </div>
      ) : (
        <p className="mt-4 border-t border-line pt-4 text-xs text-ink-500">
          No message preview yet — drafting may still be loading. Refresh the page to try again.
        </p>
      )}
    </div>
  );
}

