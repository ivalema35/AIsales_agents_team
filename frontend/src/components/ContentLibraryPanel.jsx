import { useEffect, useState } from "react";
import { Plus, Trash2, Link2 } from "lucide-react";
import { api } from "../api/client";
import ChipInput from "./ui/ChipInput";
import Badge from "./ui/Badge";

const ASSET_TYPES = ["DEMO_URL", "VIDEO_URL", "CASE_STUDY", "TESTIMONIAL", "TEXT_BLOCK"];

const EMPTY_DRAFT = { asset_type: "DEMO_URL", title: "", value: "", tags: [] };

// Phase 8 Step 8.2/8.5 -- the closed library the Outreach Agent selects from. Never a
// place to write freehand copy the AI might invent from -- title/value/tags only.
export default function ContentLibraryPanel({ productId }) {
  const [assets, setAssets] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [draft, setDraft] = useState(EMPTY_DRAFT);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  function refresh() {
    api.listContentAssets({ product_id: productId }).then(setAssets).catch((err) => setError(err.message));
  }

  useEffect(refresh, [productId]);

  async function addAsset(e) {
    e.preventDefault();
    if (!draft.title.trim() || !draft.value.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await api.createContentAsset({ ...draft, product_id: productId });
      setDraft(EMPTY_DRAFT);
      setShowAddForm(false);
      refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(asset) {
    await api.updateContentAsset(asset.id, { is_active: !asset.is_active });
    refresh();
  }

  async function remove(asset) {
    await api.deleteContentAsset(asset.id);
    refresh();
  }

  return (
    <div className="flex flex-col gap-3">
      {error && <p className="text-xs text-red-600">{error}</p>}

      {assets && assets.length > 0 && (
        <div className="flex flex-col gap-2">
          {assets.map((a) => (
            <div key={a.id} className="flex items-center justify-between gap-2 rounded-md bg-slate-50 p-2.5">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <Badge variant={a.is_active ? "SUCCESS" : "NEUTRAL"}>{a.asset_type}</Badge>
                  <span className="truncate text-xs font-medium text-slate-700">{a.title}</span>
                </div>
                <p className="mt-0.5 flex items-center gap-1 truncate text-[11px] text-slate-400">
                  <Link2 size={10} className="shrink-0" /> {a.value}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <button onClick={() => toggleActive(a)} className="text-[11px] font-medium text-slate-500 hover:text-slate-800">
                  {a.is_active ? "Deactivate" : "Activate"}
                </button>
                <button onClick={() => remove(a)} title="Delete" className="text-slate-300 hover:text-red-500">
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {assets && assets.length === 0 && !showAddForm && (
        <p className="text-xs text-slate-500">No content assets for this product yet -- the AI has nothing to select from.</p>
      )}

      {!showAddForm && (
        <button
          onClick={() => setShowAddForm(true)}
          className="flex w-fit items-center gap-1 rounded-md bg-slate-800 px-2.5 py-1.5 text-[11px] font-medium text-white hover:bg-slate-900"
        >
          <Plus size={12} /> Add asset
        </button>
      )}

      {showAddForm && (
        <form onSubmit={addAsset} className="flex flex-col gap-2 rounded-md border border-slate-200 p-3">
          <div className="flex flex-wrap gap-1.5">
            {ASSET_TYPES.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setDraft((d) => ({ ...d, asset_type: t }))}
                className={`rounded-md px-2 py-1 text-[11px] font-medium transition-colors ${
                  draft.asset_type === t ? "bg-slate-800 text-white" : "bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-50"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
          <input
            required
            value={draft.title}
            onChange={(e) => setDraft((d) => ({ ...d, title: e.target.value }))}
            placeholder="Title (e.g. Live product demo)"
            className="rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-800 placeholder:text-slate-300 focus:border-slate-400 focus:outline-none"
          />
          <input
            required
            value={draft.value}
            onChange={(e) => setDraft((d) => ({ ...d, value: e.target.value }))}
            placeholder={draft.asset_type === "TEXT_BLOCK" ? "The text itself" : "https://…"}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-800 placeholder:text-slate-300 focus:border-slate-400 focus:outline-none"
          />
          <ChipInput
            icon={Link2}
            label="Tags"
            hint="Optional -- for future matching against a lead's pain points."
            values={draft.tags}
            onChange={(tags) => setDraft((d) => ({ ...d, tags }))}
            placeholder="onboarding, pricing…"
          />
          <div className="flex items-center gap-2">
            <button
              type="submit"
              disabled={saving}
              className="rounded-md bg-slate-800 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-900 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save asset"}
            </button>
            <button
              type="button"
              onClick={() => { setShowAddForm(false); setDraft(EMPTY_DRAFT); }}
              className="rounded-md px-3 py-1.5 text-xs font-medium text-slate-500 hover:bg-slate-100"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
