import { useEffect, useState } from "react";
import { Plus, Trash2, Pencil } from "lucide-react";
import { api } from "../api/client";
import Badge from "./ui/Badge";

const KINDS = ["FACT", "OBJECTION", "PROOF", "MARKETING_ASSET"];

const EMPTY_DRAFT = { kind: "FACT", title: "", body: "" };

const KIND_VARIANT = {
  FACT: "NEUTRAL",
  OBJECTION: "WARNING",
  PROOF: "SUCCESS",
  MARKETING_ASSET: "WARM",
};

// Phase 16 Step 16.1/16.2 -- the ONLY UI that can write a knowledge_base_items row.
// Plain text in, plain text out, no AI-assisted "suggest a starting entry" anywhere near
// this screen -- the zero-fabrication rule has to hold in the UI too, not just the API.
export default function KnowledgeBasePanel({ productId }) {
  const [items, setItems] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState(EMPTY_DRAFT);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  function refresh() {
    api.listKnowledgeBaseItems({ product_id: productId }).then(setItems).catch((err) => setError(err.message));
  }

  useEffect(refresh, [productId]);

  function startEdit(item) {
    setEditingId(item.id);
    setDraft({ kind: item.kind, title: item.title, body: item.body });
    setShowAddForm(true);
  }

  function cancelForm() {
    setShowAddForm(false);
    setEditingId(null);
    setDraft(EMPTY_DRAFT);
  }

  async function saveItem(e) {
    e.preventDefault();
    if (!draft.title.trim() || !draft.body.trim()) return;
    setSaving(true);
    setError(null);
    try {
      if (editingId) {
        await api.updateKnowledgeBaseItem(editingId, draft);
      } else {
        await api.createKnowledgeBaseItem({ ...draft, product_id: productId });
      }
      cancelForm();
      refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function remove(item) {
    await api.deleteKnowledgeBaseItem(item.id);
    refresh();
  }

  return (
    <div className="flex flex-col gap-3">
      {error && <p className="text-xs text-alert-600">{error}</p>}

      {items && items.length > 0 && (
        <div className="flex flex-col gap-2">
          {items.map((item) => (
            <div key={item.id} className="flex items-start justify-between gap-2 rounded-md bg-parchment-raised-2 p-2.5">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <Badge variant={KIND_VARIANT[item.kind] || "NEUTRAL"}>{item.kind}</Badge>
                  <span className="truncate text-xs font-medium text-ink-700">{item.title}</span>
                </div>
                <p className="mt-0.5 line-clamp-2 text-[11px] text-ink-500">{item.body}</p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <button onClick={() => startEdit(item)} title="Edit" className="text-ink-500 hover:text-ink-900">
                  <Pencil size={13} />
                </button>
                <button onClick={() => remove(item)} title="Delete" className="text-ink-500 hover:text-alert-600">
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {items && items.length === 0 && !showAddForm && (
        <p className="text-xs text-ink-500">
          No knowledge base entries for this product yet -- outreach replies have nothing specific to draw on.
        </p>
      )}

      {!showAddForm && (
        <button
          onClick={() => setShowAddForm(true)}
          className="flex w-fit items-center gap-1 rounded-md bg-ink-900 px-2.5 py-1.5 text-[11px] font-medium text-parchment-raised hover:opacity-90"
        >
          <Plus size={12} /> Add entry
        </button>
      )}

      {showAddForm && (
        <form onSubmit={saveItem} className="flex flex-col gap-2 rounded-md border border-line p-3">
          <div className="flex flex-wrap gap-1.5">
            {KINDS.map((k) => (
              <button
                key={k}
                type="button"
                onClick={() => setDraft((d) => ({ ...d, kind: k }))}
                className={`rounded-md px-2 py-1 text-[11px] font-medium transition-colors ${
                  draft.kind === k ? "bg-ink-900 text-parchment-raised" : "bg-parchment-raised text-ink-700 ring-1 ring-inset ring-line hover:bg-parchment-raised-2"
                }`}
              >
                {k}
              </button>
            ))}
          </div>
          <input
            required
            value={draft.title}
            onChange={(e) => setDraft((d) => ({ ...d, title: e.target.value }))}
            placeholder="Title (e.g. Pricing starts at)"
            className="rounded-md border border-line bg-parchment-raised px-3 py-1.5 text-xs text-ink-900 placeholder:text-ink-500 focus:border-gold-500 focus:outline-none"
          />
          <textarea
            required
            rows={4}
            value={draft.body}
            onChange={(e) => setDraft((d) => ({ ...d, body: e.target.value }))}
            placeholder="The real fact / objection answer / proof point, in your own words"
            className="rounded-md border border-line bg-parchment-raised px-3 py-1.5 text-xs text-ink-900 placeholder:text-ink-500 focus:border-gold-500 focus:outline-none"
          />
          <div className="flex items-center gap-2">
            <button
              type="submit"
              disabled={saving}
              className="rounded-md bg-ink-900 px-3 py-1.5 text-xs font-medium text-parchment-raised hover:opacity-90 disabled:opacity-50"
            >
              {saving ? "Saving…" : editingId ? "Save changes" : "Save entry"}
            </button>
            <button
              type="button"
              onClick={cancelForm}
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
