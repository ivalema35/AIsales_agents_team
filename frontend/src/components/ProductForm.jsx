import { useState } from "react";
import { Building2, FileText, Sparkles, MapPin, Globe2, Plus, X, Save } from "lucide-react";
import { api } from "../api/client";

const EMPTY = {
  title: "",
  description: "",
  value_proposition: "",
  target_regions: [],
  target_country: "IN",
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
    target_regions: product.target_regions || [],
    target_country: product.target_country || "IN",
  };
}

function FieldLabel({ icon: Icon, children, hint }) {
  return (
    <div className="mb-1.5">
      <span className="flex items-center gap-1.5 text-xs font-medium text-slate-700">
        <Icon size={13} className="text-slate-400" /> {children}
      </span>
      {hint && <p className="mt-0.5 text-[11px] leading-relaxed text-slate-400">{hint}</p>}
    </div>
  );
}

const inputClass =
  "rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder:text-slate-300 focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-100";

// Dynamic product registration (MASTER PRD §5 Step 4.4) -- adding a new product/service
// here is all that's needed for the discovery scheduler to start targeting it; no code
// change required. target_keywords is deliberately NOT a field here -- the ICP Strategy
// Agent decides those on its own from the description (tracker.md §A.2).
//
// Doubles as the edit form -- pass `product` to pre-fill from it and PUT instead of
// POST on submit (the backend's PUT /products/<id> already supported every one of these
// fields; only the create-only UI was missing an edit path to it).
export default function ProductForm({ product, onCreated, onSaved, onCancel }) {
  const isEdit = !!product;
  const [form, setForm] = useState(isEdit ? toFormState(product) : EMPTY);
  const [regionInput, setRegionInput] = useState("");
  const [customCountry, setCustomCountry] = useState(
    !COMMON_COUNTRIES.some((c) => c.code === (isEdit ? product.target_country : "IN"))
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  function addRegion() {
    const v = regionInput.trim();
    if (v && !form.target_regions.includes(v)) {
      update("target_regions", [...form.target_regions, v]);
    }
    setRegionInput("");
  }

  function removeRegion(r) {
    update("target_regions", form.target_regions.filter((x) => x !== r));
  }

  function handleRegionKeyDown(e) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addRegion();
    } else if (e.key === "Backspace" && !regionInput && form.target_regions.length > 0) {
      removeRegion(form.target_regions[form.target_regions.length - 1]);
    }
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
        target_regions: form.target_regions,
        target_country: form.target_country || "IN",
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
      className={isEdit ? "flex flex-col gap-5" : "flex flex-col gap-5 rounded-lg border border-slate-200 bg-white p-5 shadow-sm"}
    >
      {!isEdit && <h3 className="text-sm font-semibold text-slate-800">Add a product / service</h3>}
      {error && <p className="rounded-md bg-red-50 px-3 py-2 text-xs text-red-600">{error}</p>}

      <div className="flex flex-col gap-4">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Basic details</p>

        <label className="flex flex-col">
          <FieldLabel icon={Building2}>Title</FieldLabel>
          <input
            required
            value={form.title}
            onChange={(e) => update("title", e.target.value)}
            className={inputClass}
            placeholder="e.g. IVinfotech -- Website Development"
          />
        </label>

        <label className="flex flex-col">
          <FieldLabel icon={FileText} hint="What it is, who it's for -- the AI reads this to decide who to target.">
            Description
          </FieldLabel>
          <textarea
            required
            rows={3}
            value={form.description}
            onChange={(e) => update("description", e.target.value)}
            className={inputClass}
            placeholder="Describe the product/service in a few sentences"
          />
        </label>

        <label className="flex flex-col">
          <FieldLabel icon={Sparkles} hint="Optional -- one line on why a customer would pick this.">
            Value proposition
          </FieldLabel>
          <input
            value={form.value_proposition}
            onChange={(e) => update("value_proposition", e.target.value)}
            className={inputClass}
          />
        </label>
      </div>

      <div className="flex flex-col gap-4 border-t border-slate-100 pt-4">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Targeting</p>

        <label className="flex flex-col">
          <FieldLabel icon={MapPin} hint="Type a city and press Enter -- discovery searches each region separately.">
            Target regions
          </FieldLabel>
          <div className="flex flex-wrap items-center gap-1.5 rounded-md border border-slate-300 px-2 py-1.5 focus-within:border-slate-400 focus-within:ring-2 focus-within:ring-slate-100">
            {form.target_regions.map((r) => (
              <span key={r} className="flex items-center gap-1 rounded bg-slate-100 px-2 py-1 text-xs text-slate-700">
                {r}
                <button
                  type="button"
                  onClick={() => removeRegion(r)}
                  className="text-slate-400 hover:text-slate-700"
                  aria-label={`Remove ${r}`}
                >
                  <X size={11} />
                </button>
              </span>
            ))}
            <input
              value={regionInput}
              onChange={(e) => setRegionInput(e.target.value)}
              onKeyDown={handleRegionKeyDown}
              onBlur={addRegion}
              placeholder={form.target_regions.length === 0 ? "Ahmedabad, Surat, Vadodara…" : "Add another…"}
              className="min-w-[110px] flex-1 border-none px-1 py-1 text-sm text-slate-800 placeholder:text-slate-300 outline-none"
            />
          </div>
        </label>

        <label className="flex flex-col">
          <FieldLabel icon={Globe2} hint="Controls how leads' phone numbers get parsed for WhatsApp.">
            Target country
          </FieldLabel>
          <div className="flex flex-wrap items-center gap-1.5">
            {COMMON_COUNTRIES.map((c) => (
              <button
                key={c.code}
                type="button"
                title={c.label}
                onClick={() => { update("target_country", c.code); setCustomCountry(false); }}
                className={`rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors ${
                  !customCountry && form.target_country === c.code
                    ? "bg-slate-800 text-white"
                    : "bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-50"
                }`}
              >
                {c.code}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setCustomCountry(true)}
              className={`rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors ${
                customCountry ? "bg-slate-800 text-white" : "bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-50"
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
              />
            )}
          </div>
        </label>
      </div>

      <div className="flex items-center gap-2 border-t border-slate-100 pt-4">
        <button
          type="submit"
          disabled={submitting}
          className="flex items-center gap-1.5 self-start rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-900 disabled:opacity-50"
        >
          {isEdit ? <Save size={14} /> : <Plus size={14} />}
          {submitting ? "Saving…" : isEdit ? "Save changes" : "Add product"}
        </button>
        {isEdit && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
