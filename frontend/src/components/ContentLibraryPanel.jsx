import { useEffect, useState } from "react";
import { Plus, Trash2, Link2, ImageUp } from "lucide-react";
import { api } from "../api/client";
import ChipInput from "./ui/ChipInput";
import Badge from "./ui/Badge";

// IMAGE_URL added 2026-09-09, real user ask: a real uploaded image (for a WhatsApp
// template header or an email banner), not just a pasted demo/video link.
const ASSET_TYPES = ["DEMO_URL", "VIDEO_URL", "IMAGE_URL", "CASE_STUDY", "TESTIMONIAL", "TEXT_BLOCK"];

const EMPTY_DRAFT = { asset_type: "DEMO_URL", title: "", value: "", tags: [] };

// Phase 8 Step 8.2/8.5 -- the closed library the Outreach Agent selects from. Never a
// place to write freehand copy the AI might invent from -- title/value/tags only.
export default function ContentLibraryPanel({ productId }) {
  const [assets, setAssets] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [draft, setDraft] = useState(EMPTY_DRAFT);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [uploadingImage, setUploadingImage] = useState(false);

  async function handleImageFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingImage(true);
    setError(null);
    try {
      const { url } = await api.uploadContentAssetImage(file);
      setDraft((d) => ({ ...d, value: url }));
    } catch (err) {
      setError(err.message);
    } finally {
      setUploadingImage(false);
    }
  }

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
      {error && <p className="text-xs text-alert-600">{error}</p>}

      {assets && assets.length > 0 && (
        <div className="flex flex-col gap-2">
          {assets.map((a) => (
            <div key={a.id} className="flex items-center justify-between gap-2 rounded-md bg-parchment p-2.5">
              {a.asset_type === "IMAGE_URL" && (
                <img src={a.value} alt={a.title} className="h-10 w-10 shrink-0 rounded-md border border-line object-cover" />
              )}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <Badge variant={a.is_active ? "SUCCESS" : "NEUTRAL"}>{a.asset_type}</Badge>
                  <span className="truncate text-xs font-medium text-ink-700">{a.title}</span>
                </div>
                <p className="mt-0.5 flex items-center gap-1 truncate text-[11px] text-ink-500">
                  <Link2 size={10} className="shrink-0" /> {a.value}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <button onClick={() => toggleActive(a)} className="text-[11px] font-medium text-ink-500 hover:text-ink-900">
                  {a.is_active ? "Deactivate" : "Activate"}
                </button>
                <button onClick={() => remove(a)} title="Delete" className="text-ink-500 hover:text-alert-600">
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {assets && assets.length === 0 && !showAddForm && (
        <p className="text-xs text-ink-500">No content assets for this product yet -- the AI has nothing to select from.</p>
      )}

      {!showAddForm && (
        <button
          onClick={() => setShowAddForm(true)}
          className="flex w-fit items-center gap-1 rounded-md bg-ink-900 px-2.5 py-1.5 text-[11px] font-medium text-parchment-raised hover:opacity-90"
        >
          <Plus size={12} /> Add asset
        </button>
      )}

      {showAddForm && (
        <form onSubmit={addAsset} className="flex flex-col gap-2 rounded-md border border-line p-3">
          <div className="flex flex-wrap gap-1.5">
            {ASSET_TYPES.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setDraft((d) => ({ ...d, asset_type: t }))}
                className={`rounded-md px-2 py-1 text-[11px] font-medium transition-colors ${
                  draft.asset_type === t ? "bg-ink-900 text-parchment-raised" : "bg-parchment-raised text-ink-700 ring-1 ring-inset ring-line hover:bg-parchment"
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
            className="rounded-md border border-line px-3 py-1.5 text-xs text-ink-900 placeholder:text-ink-500 focus:border-gold-500 focus:outline-none"
          />
          {draft.asset_type === "IMAGE_URL" ? (
            <div className="flex flex-col gap-1.5 rounded-md border border-dashed border-line p-2.5">
              <label className="flex w-fit cursor-pointer items-center gap-1.5 rounded-md bg-parchment-raised-2 px-2.5 py-1.5 text-[11px] font-medium text-ink-700 hover:bg-parchment">
                <ImageUp size={12} />
                {uploadingImage ? "Uploading…" : draft.value ? "Replace image" : "Choose image"}
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp,image/gif"
                  onChange={handleImageFile}
                  disabled={uploadingImage}
                  className="hidden"
                />
              </label>
              {draft.value && !uploadingImage && (
                <div className="flex items-center gap-2">
                  <img src={draft.value} alt="Uploaded preview" className="h-14 w-14 rounded-md border border-line object-cover" />
                  <p className="truncate text-[11px] text-ink-500">{draft.value}</p>
                </div>
              )}
            </div>
          ) : (
            <input
              required
              value={draft.value}
              onChange={(e) => setDraft((d) => ({ ...d, value: e.target.value }))}
              placeholder={draft.asset_type === "TEXT_BLOCK" ? "The text itself" : "https://…"}
              className="rounded-md border border-line px-3 py-1.5 text-xs text-ink-900 placeholder:text-ink-500 focus:border-gold-500 focus:outline-none"
            />
          )}
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
              className="rounded-md bg-ink-900 px-3 py-1.5 text-xs font-medium text-parchment-raised hover:opacity-90 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save asset"}
            </button>
            <button
              type="button"
              onClick={() => { setShowAddForm(false); setDraft(EMPTY_DRAFT); }}
              className="rounded-md px-3 py-1.5 text-xs font-medium text-ink-500 hover:bg-parchment-raised-2"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
