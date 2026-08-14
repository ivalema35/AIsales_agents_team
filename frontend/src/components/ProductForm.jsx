import { useState } from "react";
import { api } from "../api/client";

const EMPTY = {
  title: "",
  description: "",
  value_proposition: "",
  target_regions: "",
};

// Dynamic product registration (MASTER PRD §5 Step 4.4) -- adding a new product/service
// here is all that's needed for the discovery scheduler to start targeting it; no code
// change required. target_keywords is deliberately NOT a field here -- the ICP Strategy
// Agent decides those on its own from the description (tracker.md §A.2).
export default function ProductForm({ onCreated }) {
  const [form, setForm] = useState(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const regions = form.target_regions
        .split(",")
        .map((r) => r.trim())
        .filter(Boolean);
      const created = await api.createProduct({
        title: form.title,
        description: form.description,
        value_proposition: form.value_proposition || undefined,
        target_regions: regions,
      });
      setForm(EMPTY);
      onCreated?.(created);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="text-sm font-semibold text-slate-800">Add a product / service</h3>
      {error && <p className="text-xs text-red-600">{error}</p>}

      <label className="flex flex-col gap-1 text-xs text-slate-600">
        Title
        <input
          required
          value={form.title}
          onChange={(e) => update("title", e.target.value)}
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          placeholder="e.g. IVinfotech -- Website Development"
        />
      </label>

      <label className="flex flex-col gap-1 text-xs text-slate-600">
        Description
        <textarea
          required
          rows={3}
          value={form.description}
          onChange={(e) => update("description", e.target.value)}
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          placeholder="What it is, who it's for -- the AI reads this to decide who to target"
        />
      </label>

      <label className="flex flex-col gap-1 text-xs text-slate-600">
        Value proposition (optional)
        <input
          value={form.value_proposition}
          onChange={(e) => update("value_proposition", e.target.value)}
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
        />
      </label>

      <label className="flex flex-col gap-1 text-xs text-slate-600">
        Target regions (comma-separated)
        <input
          value={form.target_regions}
          onChange={(e) => update("target_regions", e.target.value)}
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          placeholder="Ahmedabad, Surat, Vadodara"
        />
      </label>

      <button
        type="submit"
        disabled={submitting}
        className="self-start rounded-md bg-slate-800 px-4 py-1.5 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-50"
      >
        {submitting ? "Adding..." : "Add product"}
      </button>
    </form>
  );
}
