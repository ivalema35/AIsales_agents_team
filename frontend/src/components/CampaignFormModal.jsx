import { useEffect, useState } from "react";
import { X, Rocket, Sparkles, Package, CalendarDays, Users, MessageSquare } from "lucide-react";
import { api } from "../api/client";
import { useToast } from "../lib/ToastContext";

const inputClass =
  "w-full rounded-lg border border-line bg-parchment-raised-2 px-3 py-2.5 text-sm text-ink-900 placeholder:text-ink-500/60 focus:border-gold-500 focus:outline-none focus:ring-2 focus:ring-gold-100";

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

function StepCard({ step, title, blurb, icon: Icon, children }) {
  return (
    <section className="rounded-xl border border-line bg-parchment-raised p-4 sm:p-5">
      <div className="mb-4 flex gap-3">
        <span
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gold-600 font-mono text-xs font-bold text-white"
          aria-hidden
        >
          {step}
        </span>
        <div className="min-w-0">
          <h4 className="flex items-center gap-1.5 font-display text-sm font-semibold text-ink-900">
            {Icon && <Icon size={14} className="text-gold-700" />}
            {title}
          </h4>
          <p className="mt-0.5 text-[12px] leading-relaxed text-ink-500">{blurb}</p>
        </div>
      </div>
      {children}
    </section>
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
  const [industry, setIndustry] = useState(
    Array.isArray(prefill?.target_segment?.industry)
      ? prefill.target_segment.industry.filter(Boolean).join(", ")
      : (prefill?.target_segment?.industry || "")
  );
  const [location, setLocation] = useState(
    Array.isArray(prefill?.target_segment?.location)
      ? prefill.target_segment.location.filter(Boolean).join(", ")
      : (prefill?.target_segment?.location || "")
  );
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
    if (!date) errs.date = "Pick a start date.";
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
        className="flex max-h-[90vh] w-full max-w-4xl flex-col overflow-y-auto rounded-xl border border-line bg-parchment-raised-2 shadow-xl"
      >
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <div className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gold-100 text-gold-700">
              <Rocket size={16} />
            </span>
            <div>
              <h3 className="font-display text-base font-semibold text-ink-900">New campaign</h3>
              <p className="text-[11px] text-ink-500">
                Four short steps. You can leave optional parts blank — the AI can suggest them later.
              </p>
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
            <p className="rounded-lg bg-alert-100 px-3 py-2 text-xs text-alert-700">{formError}</p>
          )}

          {prefill?.suggestion && (
            <div className="flex items-start gap-2 rounded-lg border border-dashed border-gold-600 bg-gold-100 p-3">
              <Sparkles size={14} className="mt-0.5 shrink-0 text-gold-700" />
              <p className="text-[12px] leading-relaxed text-ink-900">
                Pre-filled from an AI suggestion:{" "}
                <span className="italic">"{prefill.suggestion}"</span>
                {" "}— change anything below before you create it.
              </p>
            </div>
          )}

          <StepCard
            step={1}
            icon={Package}
            title="What is this campaign for?"
            blurb="Pick the product and give the campaign a name you'll recognize later."
          >
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Field label="Which product?" error={fieldErrors.productId}>
                {products.length === 0 ? (
                  <p className="text-xs text-ink-500">Add a product first from the Products page.</p>
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

              <Field
                label="Campaign name"
                hint='Just for you — e.g. "Edmonton barbers, September"'
                error={fieldErrors.name}
              >
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Edmonton barber shops push"
                  className={inputClass}
                />
              </Field>
            </div>
          </StepCard>

          <StepCard
            step={2}
            icon={CalendarDays}
            title="When should it start?"
            blurb="Pick the date this campaign is scheduled for on your calendar."
          >
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Field label="Start date" error={fieldErrors.date}>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className={inputClass}
                />
              </Field>
              <div className="flex items-end">
                <p className="rounded-lg border border-line bg-parchment-raised-2 px-3 py-2.5 text-[11px] leading-relaxed text-ink-500">
                  Tip: click an empty day on the calendar to open this form with that date already filled.
                </p>
              </div>
            </div>
          </StepCard>

          <StepCard
            step={3}
            icon={Users}
            title="Who should we look for?"
            blurb="Optional. Know your target? Fill it in. Leave blank and the AI can propose one for you to review."
          >
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Field label="Business type" hint='e.g. "barber shops" or "cake shops"'>
                <input
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  placeholder="e.g. barber shops"
                  className={inputClass}
                />
              </Field>
              <Field label="City or area" hint='e.g. "Edmonton" or "Ahmedabad"'>
                <input
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Edmonton"
                  className={inputClass}
                />
              </Field>
              <Field
                label="How many leads? (optional)"
                hint="A rough goal for this campaign — e.g. 50 or 100."
                error={fieldErrors.leadCountGoal}
              >
                <input
                  value={leadCountGoal}
                  onChange={(e) => setLeadCountGoal(e.target.value)}
                  placeholder="e.g. 100"
                  inputMode="numeric"
                  className={inputClass}
                />
              </Field>
            </div>
          </StepCard>

          <StepCard
            step={4}
            icon={MessageSquare}
            title="Any special message style?"
            blurb="Optional. Only for this campaign. Leave blank to use your product's usual email style."
          >
            <Field
              label="Angle or story"
              hint='e.g. "urgent — limited slots this month" or "friendly, focus on local trust"'
            >
              <textarea
                rows={2}
                value={angle}
                onChange={(e) => setAngle(e.target.value)}
                placeholder="How should this campaign feel?"
                className={inputClass}
              />
            </Field>
          </StepCard>
        </div>

        <div className="sticky bottom-0 flex items-center gap-2 border-t border-line bg-parchment-raised-2 px-5 py-4">
          <button
            type="submit"
            disabled={submitting || products.length === 0}
            className="flex items-center gap-1.5 rounded-lg bg-gold-600 px-4 py-2.5 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
          >
            {submitting ? "Creating…" : "Create campaign"}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-4 py-2.5 text-sm font-medium text-ink-500 hover:bg-parchment-raised hover:text-ink-900"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
