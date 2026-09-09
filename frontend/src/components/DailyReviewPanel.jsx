import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, BookOpen, ChevronDown, ChevronUp, Mail, MessageCircle, MessageSquareWarning, Sparkles } from "lucide-react";
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
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div className="min-w-0">
              <button
                onClick={() => setExpanded((e) => !e)}
                className="flex items-center gap-1.5 text-left"
              >
                {expanded ? <ChevronUp size={14} className="shrink-0 text-ink-500" /> : <ChevronDown size={14} className="shrink-0 text-ink-500" />}
                <span className="font-display text-base font-semibold text-ink-900">
                  How your messages look
                </span>
              </button>
              <p className="mt-0.5 pl-5 text-xs text-ink-500">
                {review.sample_is_kickoff_template
                  ? "Starter examples — real names fill in once leads are tagged."
                  : review.sample_lead_company
                    ? `Example for ${review.sample_lead_company}. Real sends use each lead’s own name and details.`
                    : "Example of what goes out. Real sends use each lead’s own name and details."}
              </p>
            </div>
          </div>

          {expanded && (
            <div className="mt-3 flex flex-col gap-3">
              {/* Channel picker — two clear choices, not tiny chips */}
              <div className="grid grid-cols-2 gap-2 sm:max-w-md">
                <button
                  type="button"
                  onClick={() => setPreviewChannel("email")}
                  className={`flex items-center justify-center gap-2 rounded-lg border px-3 py-2.5 text-sm font-semibold transition-colors ${
                    previewChannel === "email"
                      ? "border-ink-900 bg-ink-900 text-parchment-raised"
                      : "border-line bg-parchment text-ink-700 hover:border-ink-500"
                  }`}
                >
                  <Mail size={15} /> Email
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewChannel("whatsapp")}
                  disabled={!review.sample_whatsapp}
                  className={`flex items-center justify-center gap-2 rounded-lg border px-3 py-2.5 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
                    previewChannel === "whatsapp"
                      ? "border-ink-900 bg-ink-900 text-parchment-raised"
                      : "border-line bg-parchment text-ink-700 hover:border-ink-500"
                  }`}
                >
                  <MessageCircle size={15} /> WhatsApp
                </button>
              </div>

              {previewChannel === "email" && review.sample_draft && (
                <>
                  <div className="flex flex-col gap-1.5">
                    <p className="text-[11px] font-medium text-ink-600">Email look</p>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        disabled={settingMode || review.email_render_mode === "HTML"}
                        onClick={() => setEmailRenderMode("HTML")}
                        className={`rounded-lg border px-3 py-1.5 text-xs font-semibold disabled:opacity-60 ${
                          review.email_render_mode === "HTML"
                            ? "border-ink-900 bg-ink-900 text-parchment-raised"
                            : "border-line bg-parchment text-ink-600 hover:border-ink-500"
                        }`}
                      >
                        Designed email
                      </button>
                      <button
                        type="button"
                        disabled={settingMode || review.email_render_mode === "TEXT"}
                        onClick={() => setEmailRenderMode("TEXT")}
                        className={`rounded-lg border px-3 py-1.5 text-xs font-semibold disabled:opacity-60 ${
                          review.email_render_mode === "TEXT"
                            ? "border-ink-900 bg-ink-900 text-parchment-raised"
                            : "border-line bg-parchment text-ink-600 hover:border-ink-500"
                        }`}
                      >
                        Plain text
                      </button>
                    </div>
                    <p className="text-[11px] leading-relaxed text-ink-500">
                      {review.email_render_mode === "HTML"
                        ? "Designed = sections and layout, like a branded email."
                        : "Plain text = short note, like someone typed it in Gmail."}
                    </p>
                  </div>

                  {review.sample_is_kickoff_template && (
                    <p className="rounded-lg border border-line bg-parchment px-3 py-2 text-xs leading-relaxed text-ink-600">
                      Placeholders like <span className="font-medium text-ink-800">[Business Name]</span> and{" "}
                      <span className="font-medium text-ink-800">[Pain Point]</span> will be replaced with each
                      real lead’s details when you send.
                    </p>
                  )}

                  {review.email_render_mode === "HTML" && review.sample_draft_html ? (
                    <div className="overflow-hidden rounded-lg border border-line bg-white shadow-sm">
                      <iframe
                        title="Email preview"
                        srcDoc={review.sample_draft_html}
                        sandbox=""
                        className="h-[420px] w-full border-0 bg-white"
                      />
                    </div>
                  ) : (
                    <div className="rounded-lg border border-line bg-parchment p-4 shadow-sm">
                      <p className="text-[10px] font-semibold uppercase tracking-wide text-ink-500">Subject</p>
                      <p className="mt-1 text-sm font-semibold text-ink-900">{review.sample_draft.subject}</p>
                      <div className="my-3 border-t border-line" />
                      <p className="whitespace-pre-line text-sm leading-relaxed text-ink-700">{review.sample_draft.body}</p>
                    </div>
                  )}

                  {pushback && (
                    <div className="rounded-lg border border-dashed border-alert-600 bg-alert-100 p-3">
                      <span className="flex items-center gap-1.5 text-[11px] font-semibold text-alert-700">
                        <MessageSquareWarning size={12} /> Honest note from AI
                      </span>
                      <p className="mt-1 text-xs leading-relaxed text-ink-900">{pushback}</p>
                    </div>
                  )}

                  {aiSuggestion && (
                    <div className="rounded-lg border border-dashed border-gold-600 bg-gold-100 p-3">
                      <span className="text-[11px] font-semibold text-gold-700">AI also suggests</span>
                      <p className="mt-1 text-xs leading-relaxed text-ink-900">{aiSuggestion}</p>
                    </div>
                  )}

                  {showFeedback ? (
                    <form onSubmit={submitFeedback} className="flex flex-col gap-2 rounded-lg border border-line bg-parchment p-3">
                      <label className="text-[11px] font-medium text-ink-700">Change this email</label>
                      <input
                        autoFocus
                        value={instruction}
                        onChange={(e) => setInstruction(e.target.value)}
                        placeholder="e.g. make it shorter, warmer, less salesy"
                        className="rounded-md border border-line bg-parchment-raised px-3 py-2 text-sm text-ink-900 placeholder:text-ink-500 focus:border-gold-500 focus:outline-none"
                      />
                      <div className="flex items-center gap-2">
                        <button
                          type="submit"
                          disabled={revising || !instruction.trim()}
                          className="rounded-lg bg-gold-600 px-3.5 py-2 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
                        >
                          {revising ? "Updating…" : "Update email"}
                        </button>
                        <button
                          type="button"
                          onClick={() => setShowFeedback(false)}
                          className="text-xs font-medium text-ink-500 hover:text-ink-900"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  ) : (
                    <button
                      onClick={() => setShowFeedback(true)}
                      className="w-fit rounded-lg border border-line bg-parchment px-3.5 py-2 text-xs font-semibold text-ink-800 hover:border-ink-500"
                    >
                      Ask for a change
                    </button>
                  )}
                </>
              )}

              {previewChannel === "whatsapp" && review.sample_whatsapp && (
                <>
                  <div className="rounded-lg border border-line bg-parchment px-3 py-2.5 text-xs leading-relaxed text-ink-600">
                    <span className="font-semibold text-ink-800">WhatsApp rule: </span>
                    First messages must use a fixed template WhatsApp has already approved.
                    You can pick or request a template here — you cannot freely rewrite the words like email.
                  </div>

                  {/* Chat-style preview */}
                  <div className="rounded-lg border border-line bg-[#e8e2d4] p-4">
                    <p className="mb-2 text-[10px] font-medium text-ink-500">
                      Preview for {review.sample_whatsapp.filled_for}
                    </p>
                    <div className="ml-auto max-w-[92%] rounded-2xl rounded-tr-sm bg-ink-900 px-3.5 py-2.5 text-sm leading-relaxed text-parchment-raised shadow-sm">
                      <p className="whitespace-pre-wrap">{review.sample_whatsapp.body}</p>
                    </div>
                    <p className="mt-2 text-[10px] text-ink-500">
                      Template: {review.sample_whatsapp.template_name}
                      {review.sample_whatsapp.source === "product"
                        ? " · set for this product"
                        : review.sample_whatsapp.source === "library"
                          ? " · shared default"
                          : " · shared approved"}
                    </p>
                  </div>

                  {waCandidates && waCandidates.length > 0 && (
                    <label className="flex flex-col gap-1.5">
                      <span className="text-[11px] font-semibold text-ink-800">Which template should this product use?</span>
                      <select
                        value={(waCandidates.find((t) => t.product_id === campaign.product_id) || {}).id || ""}
                        onChange={(e) => selectWaTemplate(e.target.value)}
                        disabled={selectingTemplate}
                        className="rounded-lg border border-line bg-parchment-raised px-3 py-2.5 text-sm text-ink-900 focus:border-gold-500 focus:outline-none disabled:opacity-50"
                      >
                        <option value="">
                          {(() => {
                            // 2026-09-09, real bug found live: this used to pick the shared
                            // candidate via array order from list_templates() (created_at DESC),
                            // while the REAL backend selection (get_approved_first_touch_
                            // template, used for the actual preview/send) tie-breaks on
                            // updated_at DESC instead -- two different rules for "the same"
                            // answer meant the dropdown's label and the preview above it could
                            // genuinely name two different templates. Sorting by the exact same
                            // column here removes the disagreement at the root.
                            const sharedFallback = waCandidates
                              .filter((t) => !t.product_id)
                              .sort((a, b) => (b.updated_at > a.updated_at ? 1 : -1))[0];
                            return sharedFallback
                              ? `Shared default — “${sharedFallback.name}”`
                              : "Shared default (built-in)";
                          })()}
                        </option>
                        {waCandidates.filter((t) => t.product_id).map((t) => (
                          <option key={t.id} value={t.id}>
                            {t.name}
                            {t.product_id === campaign.product_id
                              ? " (current for this product)"
                              : t.product_title
                                ? ` — borrow from ${t.product_title} (moves it away from them)`
                                : ""}
                          </option>
                        ))}
                      </select>
                      <span className="text-[11px] leading-relaxed text-ink-500">
                        {selectingTemplate
                          ? "Updating preview…"
                          : "Changing this updates the preview above right away. No new WhatsApp approval needed when you pick an already-approved template. Picking \"Shared default\" makes this product use whatever template is currently shared — which also affects every OTHER product that has no template of its own."}
                      </span>
                    </label>
                  )}

                  <div className="flex flex-col gap-2.5 rounded-lg border border-dashed border-gold-600/70 bg-gold-100/50 p-3.5">
                    <p className="text-xs leading-relaxed text-ink-700">
                      {review.sample_whatsapp.source !== "product"
                        ? "This product doesn’t have its own WhatsApp yet — sends use the shared message above. Ask AI to draft one written for this product."
                        : "This product already has its own WhatsApp. You can still ask AI for another version (for example with a button)."}
                    </p>
                    <div className="flex flex-wrap items-center gap-2.5">
                      <button
                        onClick={askAiForWaTemplate}
                        disabled={askingWaTemplate}
                        className="flex items-center gap-1.5 rounded-lg bg-gold-600 px-3.5 py-2 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
                      >
                        <Sparkles size={13} /> {askingWaTemplate ? "Working…" : "Ask AI for a WhatsApp"}
                      </button>
                      <label className="flex items-center gap-1.5 text-xs text-ink-600">
                        <input
                          type="checkbox"
                          checked={waAskWithButton}
                          onChange={(e) => setWaAskWithButton(e.target.checked)}
                          disabled={askingWaTemplate}
                          className="rounded"
                        />
                        Include a tap button
                      </label>
                    </div>
                    {waAskResult && !waAskResult.proposed && (
                      <p className="text-[11px] text-ink-500">{waAskResult.message}</p>
                    )}
                    {waAskResult?.proposed && waAskWithButton && !waAskResult.template?.button_url && (
                      <p className="text-[11px] leading-relaxed text-warm-700">
                        Draft created, but no button — this product has no demo/video link yet.
                        Add one under Products → Content Library, then ask again.
                      </p>
                    )}
                    {waDrafts && waDrafts.length > 0 && (
                      <div className="flex flex-col gap-2 border-t border-gold-600/30 pt-2.5">
                        <p className="text-[11px] font-semibold text-ink-700">Waiting for your OK</p>
                        {waDrafts.map((t) => (
                          <WhatsappDraftCard key={t.id} item={t} onResolved={onWaDraftResolved} />
                        ))}
                      </div>
                    )}
                  </div>

                  <Link
                    to={campaign.product_id ? `/whatsapp-templates?product_id=${campaign.product_id}` : "/whatsapp-templates"}
                    className="w-fit text-xs font-medium text-ink-600 underline decoration-line underline-offset-2 hover:text-ink-900"
                  >
                    Open full WhatsApp Templates page →
                  </Link>
                </>
              )}
            </div>
          )}
        </div>
      ) : (
        <p className="mt-4 border-t border-line pt-4 text-xs text-ink-500">
          No message preview yet — try refreshing the page in a moment.
        </p>
      )}
    </div>
  );
}

