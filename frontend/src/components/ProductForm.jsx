import { useState } from "react";
import {
  Building2, FileText, Sparkles, MapPin, Globe2, Tag, UserCircle2, Plus, Save, Layers, MessageSquare,
} from "lucide-react";
import { api } from "../api/client";
import ChipInput, { FieldLabel } from "./ui/ChipInput";

const EMPTY = {
  title: "",
  description: "",
  value_proposition: "",
  default_tone: "",
  default_format: "",
  target_regions: [],
  target_country: "IN",
  target_business_categories: [],
  target_person_roles: [],
  cross_sell_product_ids: [],
};

// A handful of common targets as one-click pills instead of a free-text 2-letter box --
// the field this feeds (`Product.target_country`) drives real phone-parsing logic for
// WhatsApp sends, so getting it right matters more than most fields here. "Other" still
// escapes to a raw code for anything not listed.
const COMMON_COUNTRIES = [
  { code: "IN", label: "India" },
  { code: "CA", label: "Canada" },
  { code: "US", label: "United States" },
  { code: "GB", label: "United Kingdom" },
  { code: "AU", label: "Australia" },
  { code: "AE", label: "UAE" },
];

function toFormState(product) {
  return {
    title: product.title || "",
    description: product.description || "",
    value_proposition: product.value_proposition || "",
    default_tone: product.default_tone || "",
    default_format: product.default_format || "",
    target_regions: product.target_regions || [],
    target_country: product.target_country || "IN",
    target_business_categories: product.target_business_categories || [],
    target_person_roles: product.target_person_roles || [],
    cross_sell_product_ids: product.cross_sell_product_ids || [],
  };
}

const inputClass =
  "w-full rounded-lg border border-line bg-parchment-raised-2 px-3 py-2.5 text-sm text-ink-900 placeholder:text-ink-500/60 focus:border-gold-500 focus:outline-none focus:ring-2 focus:ring-gold-100";

function StepCard({ step, title, blurb, children }) {
  return (
    <section className="rounded-xl border border-line bg-parchment-raised-2/60 p-4 sm:p-5">
      <div className="mb-4 flex gap-3">
        <span
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gold-600 font-mono text-xs font-bold text-white"
          aria-hidden
        >
          {step}
        </span>
        <div className="min-w-0">
          <h3 className="font-display text-sm font-semibold text-ink-900">{title}</h3>
          <p className="mt-0.5 text-[12px] leading-relaxed text-ink-500">{blurb}</p>
        </div>
      </div>
      {children}
    </section>
  );
}

// Dynamic product registration (MASTER PRD §5 Step 4.4) -- adding a new product/service
// here is all that's needed for the discovery scheduler to start targeting it; no code
// change required. target_keywords is deliberately NOT a field here -- the ICP Strategy
// Agent decides those on its own from the description (tracker.md §A.2).
//
// Doubles as the edit form -- pass `product` to pre-fill from it and PUT instead of
// POST on submit (the backend's PUT /products/<id> already supported every one of these
// fields; only the create-only UI was missing an edit path to it).
export default function ProductForm({ product, allProducts = [], onCreated, onSaved, onCancel }) {
  const isEdit = !!product;
  const [form, setForm] = useState(isEdit ? toFormState(product) : EMPTY);
  const [customCountry, setCustomCountry] = useState(
    !COMMON_COUNTRIES.some((c) => c.code === (isEdit ? product.target_country : "IN"))
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  // A product can never cross-sell itself; on the create form there's no id yet, so
  // every existing product is a valid option.
  const otherProducts = allProducts.filter((p) => !isEdit || p.id !== product.id);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        title: form.title,
        description: form.description,
        value_proposition: form.value_proposition || undefined,
        default_tone: form.default_tone || undefined,
        default_format: form.default_format || undefined,
        target_regions: form.target_regions,
        target_country: form.target_country || "IN",
        target_business_categories: form.target_business_categories,
        target_person_roles: form.target_person_roles,
        cross_sell_product_ids: form.cross_sell_product_ids,
      };
      if (isEdit) {
        const updated = await api.updateProduct(product.id, payload);
        onSaved?.(updated);
      } else {
        const created = await api.createProduct(payload);
        setForm(EMPTY);
        onCreated?.(created);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={
        isEdit
          ? "flex flex-col gap-4"
          : "flex flex-col gap-4 rounded-xl border border-line bg-parchment-raised p-5 shadow-sm"
      }
    >
      {!isEdit && (
        <div>
          <h3 className="font-display text-base font-semibold text-ink-900">Add a product</h3>
          <p className="mt-1 text-xs text-ink-500">
            Tell us what you sell in plain words. The AI uses this to find matching businesses and write emails.
          </p>
        </div>
      )}
      {error && <p className="rounded-lg bg-alert-100 px-3 py-2 text-xs text-alert-700">{error}</p>}

      <StepCard
        step={1}
        title="What are you selling?"
        blurb="Start with a clear name and a short description. This is the most important part."
      >
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <label className="flex flex-col lg:col-span-2">
            <FieldLabel icon={Building2}>Product name</FieldLabel>
            <input
              required
              value={form.title}
              onChange={(e) => update("title", e.target.value)}
              className={inputClass}
              placeholder="e.g. Barber shop management software"
            />
          </label>

          <label className="flex flex-col lg:col-span-2">
            <FieldLabel icon={FileText} hint="In simple words: what it does, and who it helps.">
              What does it do?
            </FieldLabel>
            <textarea
              required
              rows={3}
              value={form.description}
              onChange={(e) => update("description", e.target.value)}
              className={inputClass}
              placeholder="e.g. Online booking, payments, staff commissions, and reports in one place for salon owners."
            />
          </label>

          <label className="flex flex-col lg:col-span-2">
            <FieldLabel icon={Sparkles} hint="Optional. One short line a customer would remember.">
              Why pick you? (optional)
            </FieldLabel>
            <input
              value={form.value_proposition}
              onChange={(e) => update("value_proposition", e.target.value)}
              className={inputClass}
              placeholder="e.g. Save 5 hours a week on booking and payroll"
            />
          </label>
        </div>
      </StepCard>

      <StepCard
        step={2}
        title="How should emails sound?"
        blurb="Optional. Leave blank if you're happy with the normal style."
      >
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <label className="flex flex-col">
            <FieldLabel icon={MessageSquare} hint="e.g. friendly and short, or formal and ROI-focused.">
              Tone of voice
            </FieldLabel>
            <input
              value={form.default_tone}
              onChange={(e) => update("default_tone", e.target.value)}
              className={inputClass}
              placeholder="Friendly, short, and clear"
            />
          </label>
          <label className="flex flex-col">
            <FieldLabel icon={Layers} hint="e.g. short paragraphs, or with a clear bullet list.">
              Email layout style
            </FieldLabel>
            <input
              value={form.default_format}
              onChange={(e) => update("default_format", e.target.value)}
              className={inputClass}
              placeholder="Short plain text, no long bullet lists"
            />
          </label>
        </div>
      </StepCard>

      <StepCard
        step={3}
        title="Who do you usually sell to?"
        blurb="Optional hints for the AI when it suggests a campaign. Each campaign can still pick its own target later."
      >
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {/* 2026-09-07, user-flagged real mismatch: these two fields' copy still described
              pre-Step-17.7 behavior ("discovery searches each region", "the AI only searches
              these exact categories") -- since discovery became campaign-driven, a campaign's
              own target_segment (CampaignFormModal) is what actually runs, not these. Relabeled
              + rewritten so a non-technical user doesn't believe setting these here locks what
              gets searched. */}
          <ChipInput
            icon={MapPin}
            label="Cities or areas"
            hint="Type a place and press Enter. Example: Edmonton, Ahmedabad."
            values={form.target_regions}
            onChange={(v) => update("target_regions", v)}
            placeholder="Add a city…"
          />

          <ChipInput
            icon={Tag}
            label="Types of businesses"
            hint="Type a business type and press Enter. Example: barber shop, dental clinic."
            values={form.target_business_categories}
            onChange={(v) => update("target_business_categories", v)}
            placeholder="Add a business type…"
          />

          <ChipInput
            icon={UserCircle2}
            label="People to contact"
            hint="Job titles to look for when finding a person. Example: Owner, Manager."
            values={form.target_person_roles}
            onChange={(v) => update("target_person_roles", v)}
            placeholder="Add a role…"
          />

          <label className="flex flex-col">
            <FieldLabel icon={Globe2} hint="Used so WhatsApp numbers are formatted for the right country.">
              Country for phone numbers
            </FieldLabel>
            <div className="flex flex-wrap items-center gap-1.5">
              {COMMON_COUNTRIES.map((c) => (
                <button
                  key={c.code}
                  type="button"
                  title={c.label}
                  onClick={() => { update("target_country", c.code); setCustomCountry(false); }}
                  className={`rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors ${
                    !customCountry && form.target_country === c.code
                      ? "bg-ink-900 text-parchment-raised"
                      : "bg-parchment-raised text-ink-700 ring-1 ring-inset ring-line hover:bg-parchment"
                  }`}
                >
                  {c.label}
                </button>
              ))}
              <button
                type="button"
                onClick={() => setCustomCountry(true)}
                className={`rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors ${
                  customCountry
                    ? "bg-ink-900 text-parchment-raised"
                    : "bg-parchment-raised text-ink-700 ring-1 ring-inset ring-line hover:bg-parchment"
                }`}
              >
                Other
              </button>
              {customCountry && (
                <input
                  value={form.target_country}
                  onChange={(e) => update("target_country", e.target.value.toUpperCase())}
                  maxLength={2}
                  className={`w-16 uppercase ${inputClass}`}
                  placeholder="IN"
                  aria-label="Two-letter country code"
                />
              )}
            </div>
          </label>
        </div>
      </StepCard>

      <StepCard
        step={4}
        title="Mention other products?"
        blurb="Optional. If this product isn't a fit, the AI may gently mention one of these instead — never a hard pitch."
      >
        {otherProducts.length === 0 ? (
          <p className="text-xs text-ink-500">
            Add another product first if you want cross-sell options here.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {otherProducts.map((p) => {
              const checked = form.cross_sell_product_ids.includes(p.id);
              return (
                <label
                  key={p.id}
                  className={`flex cursor-pointer items-start gap-2.5 rounded-lg border px-3 py-2.5 text-sm transition-colors ${
                    checked
                      ? "border-gold-500 bg-gold-100 text-ink-900"
                      : "border-line bg-parchment-raised text-ink-700 hover:border-gold-500/50"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(e) =>
                      update(
                        "cross_sell_product_ids",
                        e.target.checked
                          ? [...form.cross_sell_product_ids, p.id]
                          : form.cross_sell_product_ids.filter((id) => id !== p.id)
                      )
                    }
                    className="mt-0.5 rounded border-line"
                  />
                  <span className="min-w-0 leading-snug">{p.title}</span>
                </label>
              );
            })}
          </div>
        )}
      </StepCard>

      <div className="sticky bottom-0 -mx-1 flex items-center gap-2 border-t border-line bg-parchment-raised px-1 pt-4">
        <button
          type="submit"
          disabled={submitting}
          className="flex items-center gap-1.5 rounded-lg bg-ink-900 px-4 py-2.5 text-sm font-semibold text-parchment-raised transition-colors hover:opacity-90 disabled:opacity-50"
        >
          {isEdit ? <Save size={14} /> : <Plus size={14} />}
          {submitting ? "Saving…" : isEdit ? "Save changes" : "Add product"}
        </button>
        {isEdit && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg px-4 py-2.5 text-sm font-medium text-ink-700 hover:bg-parchment-raised-2"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
