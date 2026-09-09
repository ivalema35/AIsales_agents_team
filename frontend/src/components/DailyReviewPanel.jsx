import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, BookOpen, ChevronDown, ChevronUp, MessageSquareWarning, Sparkles } from "lucide-react";
import { api } from "../api/client";
import TodoItemCard from "./TodoItemCard";
import WhatsappDraftCard from "./WhatsappDraftCard";

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
  // Email vs WhatsApp preview — Formatted/Simple chips only apply to email.
  const [previewChannel, setPreviewChannel] = useState("email");
  // 2026-09-08, real user ask: when WhatsApp falls back to the shared library template
  // instead of a real pitch written for this product, let a human ask the AI for a
  // product-specific one right here, instead of only a passive link to a different page.
  const [askingWaTemplate, setAskingWaTemplate] = useState(false);
  const [waAskResult, setWaAskResult] = useState(null);
  // 2026-09-09, real user ask: "button add karo bhi bol sakta he to button wala template" --
  // a human may want a call-to-action button on the very first ask, not only via feedback
  // later. Resolved from this product's own real content assets, never invented.
  const [waAskWithButton, setWaAskWithButton] = useState(false);
  // 2026-09-08, real user ask: "campaign ke liye template yahin select karna he, preview
  // dekh ke -- dusre page kyu jaun?" -- every currently-APPROVED template (shared library +
  // any real, already-Meta-approved DB one) picked right here; picking one just reassigns
  // its (Meta-invisible) product_id -- no new Meta call, and the real preview below updates
  // immediately so a human can see it before committing to keeping it.
  const [waCandidates, setWaCandidates] = useState(null);
  const [selectingTemplate, setSelectingTemplate] = useState(false);
  // 2026-09-09, real user ask: "ye campign page me whatsapp template review me hi bhi
  // handle ho jaye, yaha ana na pade" -- an AI-drafted template for this product's own
  // FIRST_TOUCH gap is reviewed/feedback-given/approved right here, using the SAME shared
  // WhatsappDraftCard the standalone WhatsApp Templates page uses (never two independently-
  // drifting designs, same reasoning as TodoItemCard being shared with the Dashboard inbox).
  const [waDrafts, setWaDrafts] = useState(null);

  useEffect(() => {
    api.getCampaignDailyReview(campaign.id).then(setReview).catch((err) => setError(err.message));
  }, [campaign.id]);

  function loadWaCandidates() {
    if (!campaign.product_id) return;
    api.listWhatsappTemplates({ status: "APPROVED", purpose: "FIRST_TOUCH" })
      .then(setWaCandidates)
      .catch(() => {});
  }

  function loadWaDrafts() {
    if (!campaign.product_id) return;
    api.listWhatsappTemplates({ status: "DRAFT", product_id: campaign.product_id, purpose: "FIRST_TOUCH" })
      .then(setWaDrafts)
      .catch(() => {});
  }

  useEffect(() => {
    if (previewChannel === "whatsapp") { loadWaCandidates(); loadWaDrafts(); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [previewChannel, campaign.product_id]);

  // A draft got Approved or Rejected -- drop it from the inline list and refresh the
  // candidate/preview state, since an approve may now supply a real product-specific
  // template where only the shared fallback existed before.
  function onWaDraftResolved(id) {
    setWaDrafts((prev) => (prev || []).filter((t) => t.id !== id));
    loadWaCandidates();
    api.getCampaignDailyReview(campaign.id).then(setReview).catch(() => {});
  }

  async function selectWaTemplate(templateId) {
    setSelectingTemplate(true);
    setError(null);
    try {
      const currentlyAssigned = (waCandidates || []).find((t) => t.product_id === campaign.product_id);
      if (!templateId) {
        // "Shared library (default)" -- release this product's own template, if any,
        // back to shared so select_template()'s own default fallback applies again.
        if (currentlyAssigned) await api.updateWhatsappTemplate(currentlyAssigned.id, { product_id: null });
      } else {
        if (currentlyAssigned && currentlyAssigned.id !== templateId) {
          await api.updateWhatsappTemplate(currentlyAssigned.id, { product_id: null });
        }
        await api.updateWhatsappTemplate(templateId, { product_id: campaign.product_id });
      }
      const fresh = await api.getCampaignDailyReview(campaign.id);
      setReview(fresh);
      loadWaCandidates();
    } catch (err) {
      setError(err.message);
    } finally {
      setSelectingTemplate(false);
    }
  }

  async function askAiForWaTemplate() {
    setAskingWaTemplate(true);
    setWaAskResult(null);
    try {
      // Passing campaignId makes this a mandatory, human-requested ask (see propose_new_
      // template's `guarantee` mode, backend/services/outreach/whatsapp_template_service.py)
      // -- a real, confirmed gap always comes back with a draft to review now, instead of
      // an AI quality-check silently deciding the human never gets to see one.
      const res = await api.proposeWhatsappTemplate("FIRST_TOUCH", null, campaign.product_id, {
        campaignId: campaign.id, withButton: waAskWithButton,
      });
      setWaAskResult(res);
      if (res.proposed) loadWaDrafts();
    } catch (err) {
      setWaAskResult({ proposed: false, message: err.message });
    } finally {
      setAskingWaTemplate(false);
    }
  }

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

      {(review.sample_draft || review.sample_whatsapp) ? (
        <div className="mt-4 border-t border-line pt-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <button
              onClick={() => setExpanded((e) => !e)}
              className="flex items-center gap-1.5 text-xs font-medium text-ink-600 hover:text-ink-900"
            >
              {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              {review.sample_is_kickoff_template
                ? "Preview: starter message templates"
                : `Preview: sample messages${review.sample_lead_company ? ` for ${review.sample_lead_company}` : ""}`}
            </button>
          </div>

          {expanded && (
            <div className="mt-2 flex flex-col gap-2.5">
              <div className="flex flex-wrap items-center gap-1">
                <button
                  type="button"
                  onClick={() => setPreviewChannel("email")}
                  className={`rounded-md px-2.5 py-1 text-[11px] font-semibold ${
                    previewChannel === "email"
                      ? "bg-ink-900 text-parchment-raised"
                      : "bg-parchment-raised-2 text-ink-500 hover:text-ink-900"
                  }`}
                >
                  Email
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewChannel("whatsapp")}
                  disabled={!review.sample_whatsapp}
                  className={`rounded-md px-2.5 py-1 text-[11px] font-semibold disabled:opacity-40 ${
                    previewChannel === "whatsapp"
                      ? "bg-ink-900 text-parchment-raised"
                      : "bg-parchment-raised-2 text-ink-500 hover:text-ink-900"
                  }`}
                >
                  WhatsApp
                </button>
                {previewChannel === "email" && review.sample_draft && (
                  <>
                    <span className="mx-1 text-ink-500">·</span>
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
                      Formatted
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
                  </>
                )}
              </div>

              {previewChannel === "email" && review.sample_draft && (
                <>
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
                        This is a real, worked email example -- not a copy sent as-is. [Business Name] here ={" "}
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
                </>
              )}

              {previewChannel === "whatsapp" && review.sample_whatsapp && (
                <>
                  <p className="text-[10px] italic text-ink-500">
                    Filled first-touch WhatsApp for{" "}
                    <span className="font-medium">{review.sample_whatsapp.filled_for}</span>
                    {" "}using template{" "}
                    <span className="font-medium">{review.sample_whatsapp.template_name}</span>
                    {review.sample_whatsapp.source === "library"
                      ? " (shared library)"
                      : review.sample_whatsapp.source === "product"
                        ? " (this product)"
                        : " (shared approved)"}.
                    Real sends use this same template — wording is Meta-approved, not free-drafted.
                  </p>
                  <div className="rounded-md border border-line bg-parchment p-3">
                    <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-ink-500">
                      WhatsApp · {review.sample_whatsapp.template_name}
                    </p>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink-800">
                      {review.sample_whatsapp.body}
                    </p>
                  </div>
                  {waCandidates && waCandidates.length > 0 && (
                    <label className="flex flex-col gap-1">
                      <span className="text-[11px] font-medium text-ink-700">
                        Choose a template for this product
                      </span>
                      <select
                        value={(waCandidates.find((t) => t.product_id === campaign.product_id) || {}).id || ""}
                        onChange={(e) => selectWaTemplate(e.target.value)}
                        disabled={selectingTemplate}
                        className="rounded-md border border-line bg-parchment-raised px-2.5 py-1.5 text-xs text-ink-900 focus:border-gold-500 focus:outline-none disabled:opacity-50"
                      >
                        {/* 2026-09-09, real user ask: "template badle to preview bhi badalna
                           chahiye" -- this WASN'T stale, "Shared library (default)" was just a
                           misleading fixed label: the real fallback is whichever DB template is
                           currently marked shared (product_id NULL), which can easily be this
                           SAME template -- so the preview correctly stayed identical. Naming it
                           explicitly here removes the confusion instead of hiding it. */}
                        <option value="">
                          {(() => {
                            const sharedFallback = waCandidates.find((t) => !t.product_id);
                            return sharedFallback
                              ? `No override — falls back to "${sharedFallback.name}" (shared)`
                              : "No override — falls back to the built-in shared library";
                          })()}
                        </option>
                        {waCandidates.filter((t) => t.product_id).map((t) => (
                          <option key={t.id} value={t.id}>
                            {t.name} — currently used by {t.product_title}
                          </option>
                        ))}
                      </select>
                      <span className="font-mono text-[10px] text-ink-500">
                        Picking one just points this product at it (no new Meta submission) — the
                        preview above updates right away so you can see it before keeping it.
                        Choosing "No override" makes this product use whatever the current shared
                        default is -- which affects every OTHER product with no override too.
                      </span>
                    </label>
                  )}
                  <p className="text-[11px] text-ink-600">{review.sample_whatsapp.manage_hint}</p>
                  {/* 2026-09-09, real user ask: this box used to hide entirely once the product
                     had its own approved template -- but a human may still want to ask again
                     (e.g. a button-enabled version once a real demo/video link exists), so it
                     always shows now, with wording that matches whichever case is real. */}
                  <div className="flex flex-col gap-1.5 rounded-md border border-dashed border-gold-600 bg-gold-100/40 p-2.5">
                    <p className="text-[11px] leading-relaxed text-ink-700">
                      {review.sample_whatsapp.source !== "product"
                        ? "This product doesn't have its own approved WhatsApp template yet, so real sends use the shared, generic one above instead of a pitch written for it."
                        : "This product already has its own approved template above. You can ask again for another version -- e.g. with a call-to-action button."}
                    </p>
                    <div className="flex flex-wrap items-center gap-2.5">
                      <button
                        onClick={askAiForWaTemplate}
                        disabled={askingWaTemplate}
                        className="flex w-fit items-center gap-1.5 rounded-md bg-gold-600 px-2.5 py-1.5 text-[11px] font-medium text-parchment-raised hover:opacity-90 disabled:opacity-50"
                      >
                        <Sparkles size={11} /> {askingWaTemplate ? "Thinking…" : "Ask AI for a template for this product"}
                      </button>
                      <label className="flex items-center gap-1.5 text-[11px] text-ink-600">
                        <input
                          type="checkbox"
                          checked={waAskWithButton}
                          onChange={(e) => setWaAskWithButton(e.target.checked)}
                          disabled={askingWaTemplate}
                        />
                        Include a button
                      </label>
                    </div>
                    {waAskResult && !waAskResult.proposed && (
                      <p className="text-[11px] text-ink-500">{waAskResult.message}</p>
                    )}
                    {waAskResult?.proposed && waAskWithButton && !waAskResult.template?.button_url && (
                      <p className="text-[11px] leading-relaxed text-warm-700">
                        The draft was created, but no button was added -- this product has no real
                        demo/video link set up yet. Add one under Products → Content Library, then ask again.
                      </p>
                    )}
                    {waDrafts && waDrafts.length > 0 && (
                      <div className="flex flex-col gap-2 pt-1">
                        {waDrafts.map((t) => (
                          <WhatsappDraftCard key={t.id} item={t} onResolved={onWaDraftResolved} />
                        ))}
                      </div>
                    )}
                  </div>
                  <Link
                    to={campaign.product_id ? `/whatsapp-templates?product_id=${campaign.product_id}` : "/whatsapp-templates"}
                    className="w-fit text-[11px] font-medium text-ink-700 underline decoration-line underline-offset-2 hover:text-ink-900"
                  >
                    Open WhatsApp Templates
                  </Link>
                </>
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

