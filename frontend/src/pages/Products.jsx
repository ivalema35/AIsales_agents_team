import { useEffect, useState } from "react";
import { Pencil, Plus, MapPin, ChevronDown, X } from "lucide-react";
import { api } from "../api/client";
import ProductForm from "../components/ProductForm";
import Modal from "../components/ui/Modal";
import ContentLibraryPanel from "../components/ContentLibraryPanel";
import KnowledgeBasePanel from "../components/KnowledgeBasePanel";

function StrategyView({ productId }) {
  const [strategy, setStrategy] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getProductStrategy(productId).then(setStrategy).catch((err) => setError(err.message));
  }, [productId]);

  if (error) return <p className="text-xs text-alert-600">{error}</p>;
  if (!strategy) return <p className="text-xs text-ink-500">Loading strategy...</p>;

  if (strategy.active_strategies.length === 0) {
    return (
      <p className="text-xs text-ink-500">
        No AI strategy yet -- the discovery scheduler generates one automatically once this
        product has at least one target region and the scheduler runs.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {strategy.active_strategies.map((s) => (
        <div key={s.id} className="rounded-md bg-parchment-raised-2 p-3 text-xs">
          <span className="mb-1 inline-block rounded-full bg-parchment-raised px-2 py-0.5 font-medium text-ink-700">
            {s.source}
          </span>
          <p className="mt-1">
            <strong>Search queries:</strong> {s.search_queries.join(", ") || "—"}
          </p>
          {s.target_complaints.length > 0 && (
            <p className="mt-1">
              <strong>Target complaints:</strong> {s.target_complaints.join(", ")}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

function DiscoveryToggle({ product, onChanged }) {
  // Same explicit-inline-style pattern as SystemToggles.jsx's Toggle -- Tailwind
  // translate-x utility classes inside a ternary previously rendered ambiguously (looked
  // "on" while actually off), so every toggle in this app avoids that pattern.
  const checked = !!product.is_active;
  const [busy, setBusy] = useState(false);

  async function toggle(e) {
    e.stopPropagation();
    setBusy(true);
    try {
      const updated = await api.updateProduct(product.id, { is_active: !checked });
      onChanged(updated);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex shrink-0 items-center gap-2" onClick={(e) => e.stopPropagation()}>
      <span className={`text-xs font-semibold ${checked ? "text-good-700" : "text-ink-500"}`}>
        {checked ? "Discovery ON" : "Discovery OFF"}
      </span>
      <button
        role="switch"
        aria-checked={checked}
        disabled={busy}
        onClick={toggle}
        style={{ backgroundColor: checked ? "#3f7a57" : "#c7bd9f" }}
        className="relative h-6 w-11 shrink-0 rounded-full transition-colors disabled:opacity-50"
      >
        <span
          style={{ left: checked ? "22px" : "2px" }}
          className="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all"
        />
      </button>
    </div>
  );
}

const TABS = [
  { id: "strategy", label: "AI targeting strategy" },
  { id: "library", label: "Content library" },
  { id: "knowledge", label: "Knowledge base" },
];

// Phase 8 Step 8.5 -- content library UI, alongside the existing AI strategy view rather
// than replacing it. Tabbed so the expanded card doesn't get cluttered with unrelated
// panels visible at once. The "Message format" tab that used to live here was removed
// (2026-08-26) -- Phase 11/13 replaced that whole admin-format-driven path with the
// structured section engine every real email now goes through (jobs/outreach_handler.py
// no longer calls resolve_active_format() at all), so the tab was a real, live dead end:
// an admin could save a format here and it would never affect a single real email.
// MessageFormatPanel.jsx itself is left in place, not deleted -- same "dead code kept,
// not unilaterally removed" precedent the backend side of this already set.
function ExpandedTabs({ productId }) {
  const [tab, setTab] = useState("strategy");
  return (
    <div>
      <div className="mb-3 flex gap-1 border-b border-line">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-2.5 py-1.5 text-[11px] font-semibold uppercase tracking-wide transition-colors ${
              tab === t.id ? "border-b-2 border-ink-900 text-ink-900" : "text-ink-500 hover:text-ink-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === "strategy" && <StrategyView productId={productId} />}
      {tab === "library" && <ContentLibraryPanel productId={productId} />}
      {tab === "knowledge" && <KnowledgeBasePanel productId={productId} />}
    </div>
  );
}

function ProductCard({ product, expanded, onToggleExpand, onChanged, onEdit }) {
  const regions = product.target_regions || [];
  return (
    <div className="rounded-lg border border-line bg-parchment-raised shadow-sm transition-shadow hover:shadow-md">
      <div
        role="button"
        tabIndex={0}
        onClick={onToggleExpand}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onToggleExpand()}
        className="flex w-full cursor-pointer items-start justify-between gap-3 p-4 text-left"
      >
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium text-ink-900">{product.title}</p>
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                product.is_active ? "bg-good-100 text-good-700 ring-1 ring-inset ring-good-600/30" : "bg-parchment-raised-2 text-ink-700 ring-1 ring-inset ring-line"
              }`}
            >
              {product.is_active ? "Active" : "Inactive"}
            </span>
            <span className="rounded bg-parchment-raised-2 px-1.5 py-0.5 text-[10px] font-semibold text-ink-500">
              {product.target_country}
            </span>
          </div>
          <p className="mt-1 text-xs text-ink-500 line-clamp-1">{product.description}</p>
          {regions.length > 0 && (
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              <MapPin size={11} className="shrink-0 text-ink-500" />
              {regions.map((r) => (
                <span key={r} className="rounded bg-parchment-raised-2 px-1.5 py-0.5 text-[10px] text-ink-500">{r}</span>
              ))}
            </div>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <DiscoveryToggle product={product} onChanged={onChanged} />
          <button
            onClick={(e) => { e.stopPropagation(); onEdit(product); }}
            title="Edit product"
            className="flex h-7 w-7 items-center justify-center rounded-md text-ink-500 hover:bg-parchment-raised-2 hover:text-ink-900"
          >
            <Pencil size={14} />
          </button>
          <ChevronDown size={16} className={`shrink-0 text-ink-500 transition-transform ${expanded ? "rotate-180" : ""}`} />
        </div>
      </div>
      {expanded && (
        <div className="border-t border-line px-4 pb-4 pt-3">
          <ExpandedTabs productId={product.id} />
        </div>
      )}
    </div>
  );
}

export default function Products() {
  const [products, setProducts] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [error, setError] = useState(null);

  function refresh() {
    api.listProducts().then(setProducts).catch((err) => setError(err.message));
  }

  useEffect(refresh, []);

  function handleChanged(updated) {
    setProducts((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
  }

  function handleCreated(created) {
    setProducts((prev) => [created, ...prev]);
    setShowAddForm(false);
  }

  function handleSaved(updated) {
    handleChanged(updated);
    setEditingProduct(null);
  }

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-lg font-semibold text-ink-900">Products & Services</h1>
          <p className="mt-0.5 text-sm text-ink-500">
            "Discovery" controls whether the scheduler searches for new leads for this product at
            all -- turn it off for products you don't want actively discovered right now.
          </p>
        </div>
        <button
          onClick={() => setShowAddForm((v) => !v)}
          className="flex shrink-0 items-center gap-1.5 rounded-md bg-ink-900 px-3.5 py-2 text-sm font-medium text-parchment-raised hover:opacity-90"
        >
          {showAddForm ? <X size={14} /> : <Plus size={14} />}
          {showAddForm ? "Cancel" : "Add product"}
        </button>
      </div>

      {error && <p className="text-sm text-alert-600">{error}</p>}

      {showAddForm && <ProductForm allProducts={products} onCreated={handleCreated} />}

      <div className="flex flex-col gap-3">
        {products.map((p) => (
          <ProductCard
            key={p.id}
            product={p}
            expanded={expandedId === p.id}
            onToggleExpand={() => setExpandedId(expandedId === p.id ? null : p.id)}
            onChanged={handleChanged}
            onEdit={setEditingProduct}
          />
        ))}
      </div>

      {editingProduct && (
        <Modal title={`Edit — ${editingProduct.title}`} onClose={() => setEditingProduct(null)}>
          <ProductForm product={editingProduct} allProducts={products} onSaved={handleSaved} onCancel={() => setEditingProduct(null)} />
        </Modal>
      )}
    </div>
  );
}
