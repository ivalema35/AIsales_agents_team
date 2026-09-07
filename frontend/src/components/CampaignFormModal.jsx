import { useEffect, useState } from "react";
import { X, Rocket, Sparkles } from "lucide-react";
import { api } from "../api/client";
import { useToast } from "../lib/ToastContext";

const inputClass =
  "rounded-md border border-line bg-parchment-raised px-3 py-2 text-sm text-ink-900 placeholder:text-ink-500/60 focus:border-gold-500 focus:outline-none focus:ring-2 focus:ring-gold-100";

function Field({ label, hint, error, children }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs font-semibold text-ink-900">{label}</span>
      {hint && <span className="text-[11px] leading-relaxed text-ink-500">{hint}</span>}
      {children}
      {error && <span className="text-[11px] font-medium text-alert-600">{error}</span>}
    </label>
  );
}

// Phase 17.4 real gap (user-flagged 2026-09-02): the backend campaign CRUD existed but
// nothing let an actual human create one -- the one real campaign in the system was made
// by a raw script. This is that missing "human creates the campaign" entry point, kept
// deliberately plain-language: no raw JSON, no status dropdown (every campaign starts
// PROPOSED, same as the backend default).
//
// The "who are you targeting?" section was removed the same day (it was pure decoration --
// target_segment was read by nothing) and re-added once Step 18.1 made it real: the AI
// Sales Manager's daily strategist actually reads/proposes target_segment/lead_count_goal
// now, so a human who already knows their target can set it here directly, or leave it
// blank and let the strategist propose one within a day (reviewed on the Daily Review
// card, same as any other proposal).
//
// `prefill` (optional): {product_id, target_segment, lead_count_goal, suggestion} -- passed
// when this form is opened from a Dashboard suggestion card (Step 18.1 follow-up) instead
// of the blank "+ New campaign" button, so the human doesn't retype what the AI already
// proposed -- they still review/edit/confirm it here, nothing is auto-submitted.
export default function CampaignFormModal({ products, defaultDate, prefill, onCreated, onClose }) {
  const toast = useToast();
  const [productId, setProductId] = useState(prefill?.product_id || products[0]?.id || "");
  const [name, setName] = useState("");
  const [date, setDate] = useState(defaultDate || "");
  const [industry, setIndustry] = useState(prefill?.target_segment?.industry || "");
  const [location, setLocation] = useState(prefill?.target_segment?.location || "");
  const [leadCountGoal, setLeadCountGoal] = useState(
    prefill?.lead_count_goal != null ? String(prefill.lead_count_goal) : ""
  );
  const [angle, setAngle] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);

  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function validate() {
    const errs = {};
    if (!productId) errs.productId = "Please pick a product.";
    if (!name.trim()) errs.name = "Give this campaign a short name.";
    if (!date) errs.date = "Pick a date to start on.";
    if (leadCountGoal && (!/^\d+$/.test(leadCountGoal) || Number(leadCountGoal) <= 0)) {
      errs.leadCountGoal = "Enter a whole number greater than 0, or leave it blank.";
    }
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError(null);
    if (!validate()) return;

    const target_segment = {};
    if (industry.trim()) target_segment.industry = industry.trim();
    if (location.trim()) target_segment.location = location.trim();

    setSubmitting(true);
    try {
      const created = await api.createCampaign({
        product_id: productId,
        name: name.trim(),
        scheduled_date: date,
        target_segment: Object.keys(target_segment).length > 0 ? target_segment : undefined,
        lead_count_goal: leadCountGoal ? Number(leadCountGoal) : undefined,
        strategy_angle: angle.trim() || undefined,
      });
      toast.success(`"${created.name}" created -- it'll show up in today's review once it's live.`);
      onCreated(created);
    } catch (err) {
      setFormError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/50 p-4"
      onClick={onClose}
    >
      <form
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
        onSubmit={handleSubmit}
        className="flex max-h-[90vh] w-full max-w-md flex-col overflow-y-auto rounded-xl border border-line bg-parchment-raised-2 shadow-xl"
      >
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gold-100 text-gold-700">
              <Rocket size={15} />
            </span>
            <div>
              <h3 className="font-display text-base font-semibold text-ink-900">New campaign</h3>
              <p className="text-[11px] text-ink-500">A few simple questions -- takes a minute.</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 text-ink-500 hover:bg-parchment-raised hover:text-ink-900"
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        <div className="flex flex-col gap-4 px-5 py-4">
          {formError && (
            <p className="rounded-md bg-alert-100 px-3 py-2 text-xs text-alert-700">{formError}</p>
          )}

          {prefill?.suggestion && (
            <div className="flex items-start gap-2 rounded-md border border-dashed border-gold-600 bg-gold-100 p-2.5">
              <Sparkles size={13} className="mt-0.5 shrink-0 text-gold-700" />
              <p className="text-[11px] text-ink-900">
                Pre-filled from your AI Sales Manager's suggestion: <span className="italic">"{prefill.suggestion}"</span> -- edit anything below before creating.
              </p>
            </div>
          )}

          <Field label="Which product is this for?" error={fieldErrors.productId}>
            {products.length === 0 ? (
              <p className="text-xs text-ink-500">Add a product first, from the Products page.</p>
            ) : (
              <select
                value={productId}
                onChange={(e) => setProductId(e.target.value)}
                className={inputClass}
              >
                {products.map((p) => (
                  <option key={p.id} value={p.id}>{p.title}</option>
                ))}
              </select>
            )}
          </Field>

          <Field label="Give it a name" hint="Just for you -- e.g. “Ahmedabad push, September”" error={fieldErrors.name}>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Ahmedabad app development push"
              className={inputClass}
            />
          </Field>

          <Field label="When should it start?" error={fieldErrors.date}>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className={inputClass}
            />
          </Field>

          <div className="flex flex-col gap-2.5 rounded-lg border border-line bg-parchment-raised p-3">
            <span className="text-xs font-semibold text-ink-900">Who should this target?</span>
            <span className="-mt-1.5 text-[11px] leading-relaxed text-ink-500">
              Optional -- know exactly who you want? Type it below. Leave it blank and your AI Sales
              Manager will propose a target within a day (you'll review it on the Daily Review card
              before anything happens). This is what THIS campaign actually searches for -- it can be
              different from your product's own "Usual regions/business types" (set on the Products
              page, which are just background hints for the AI).
            </span>
            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
              <input
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder="Business type, e.g. cake shops"
                className={inputClass}
              />
              <input
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Region, e.g. Ahmedabad"
                className={inputClass}
              />
            </div>
            <label className="flex flex-col gap-1">
              <input
                value={leadCountGoal}
                onChange={(e) => setLeadCountGoal(e.target.value)}
                placeholder="Lead count goal, e.g. 100"
                inputMode="numeric"
                className={inputClass}
              />
              {fieldErrors.leadCountGoal && (
                <span className="text-[11px] font-medium text-alert-600">{fieldErrors.leadCountGoal}</span>
              )}
            </label>
          </div>

          <Field
            label="What's the story or angle, just for this campaign?"
            hint={'Optional -- different from your product\'s usual "Default tone" (that\'s your everyday style, set on the Products page). This one only kicks in for this campaign\'s leads and its daily plan -- e.g. "urgent, limited slots this month" or "casual, focus on local trust". Leave blank to just use your usual style.'}
          >
            <textarea
              rows={2}
              value={angle}
              onChange={(e) => setAngle(e.target.value)}
              placeholder="How should this campaign feel?"
              className={inputClass}
            />
          </Field>
        </div>

        <div className="flex items-center gap-2 border-t border-line px-5 py-4">
          <button
            type="submit"
            disabled={submitting || products.length === 0}
            className="flex items-center gap-1.5 rounded-md bg-gold-600 px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
          >
            {submitting ? "Creating…" : "Create campaign"}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-4 py-2 text-sm font-medium text-ink-500 hover:bg-parchment-raised hover:text-ink-900"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
