import { useEffect, useState } from "react";
import { Pencil, Plus, MapPin, ChevronDown, X } from "lucide-react";
import { api } from "../api/client";
import ProductForm from "../components/ProductForm";
import Modal from "../components/ui/Modal";
import MessageFormatPanel from "../components/MessageFormatPanel";
import ContentLibraryPanel from "../components/ContentLibraryPanel";

function StrategyView({ productId }) {
  const [strategy, setStrategy] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getProductStrategy(productId).then(setStrategy).catch((err) => setError(err.message));
  }, [productId]);

  if (error) return <p className="text-xs text-red-600">{error}</p>;
  if (!strategy) return <p className="text-xs text-slate-400">Loading strategy...</p>;

  if (strategy.active_strategies.length === 0) {
    return (
      <p className="text-xs text-slate-500">
        No AI strategy yet -- the discovery scheduler generates one automatically once this
        product has at least one target region and the scheduler runs.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {strategy.active_strategies.map((s) => (
        <div key={s.id} className="rounded-md bg-slate-50 p-3 text-xs">
          <span className="mb-1 inline-block rounded-full bg-slate-200 px-2 py-0.5 font-medium text-slate-700">
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
      <span className={`text-xs font-semibold ${checked ? "text-emerald-700" : "text-slate-400"}`}>
        {checked ? "Discovery ON" : "Discovery OFF"}
      </span>
      <button
        role="switch"
        aria-checked={checked}
        disabled={busy}
        onClick={toggle}
        style={{ backgroundColor: checked ? "#059669" : "#d1d5db" }}
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
  { id: "format", label: "Message format" },
  { id: "library", label: "Content library" },
];

// Phase 8 Step 8.5 -- format builder + content library UI, alongside the existing AI
// strategy view rather than replacing it. Tabbed so the expanded card doesn't get
// cluttered with three unrelated panels visible at once.
function ExpandedTabs({ productId }) {
  const [tab, setTab] = useState("strategy");
  return (
    <div>
      <div className="mb-3 flex gap-1 border-b border-slate-100">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-2.5 py-1.5 text-[11px] font-semibold uppercase tracking-wide transition-colors ${
              tab === t.id ? "border-b-2 border-slate-800 text-slate-800" : "text-slate-400 hover:text-slate-600"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === "strategy" && <StrategyView productId={productId} />}
      {tab === "format" && <MessageFormatPanel productId={productId} />}
      {tab === "library" && <ContentLibraryPanel productId={productId} />}
    </div>
  );
}

function ProductCard({ product, expanded, onToggleExpand, onChanged, onEdit }) {
  const regions = product.target_regions || [];
  return (
    <div className="rounded-lg border border-slate-200 bg-white shadow-sm transition-shadow hover:shadow-md">
      <div
        role="button"
        tabIndex={0}
        onClick={onToggleExpand}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onToggleExpand()}
        className="flex w-full cursor-pointer items-start justify-between gap-3 p-4 text-left"
      >
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium text-slate-900">{product.title}</p>
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                product.is_active ? "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200" : "bg-slate-100 text-slate-500 ring-1 ring-inset ring-slate-200"
              }`}
            >
              {product.is_active ? "Active" : "Inactive"}
            </span>
            <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-500">
              {product.target_country}
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500 line-clamp-1">{product.description}</p>
          {regions.length > 0 && (
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              <MapPin size={11} className="shrink-0 text-slate-300" />
              {regions.map((r) => (
                <span key={r} className="rounded bg-slate-50 px-1.5 py-0.5 text-[10px] text-slate-500">{r}</span>
              ))}
            </div>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <DiscoveryToggle product={product} onChanged={onChanged} />
          <button
            onClick={(e) => { e.stopPropagation(); onEdit(product); }}
            title="Edit product"
            className="flex h-7 w-7 items-center justify-center rounded-md text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          >
            <Pencil size={14} />
          </button>
          <ChevronDown size={16} className={`shrink-0 text-slate-400 transition-transform ${expanded ? "rotate-180" : ""}`} />
        </div>
      </div>
      {expanded && (
        <div className="border-t border-slate-100 px-4 pb-4 pt-3">
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
          <h1 className="text-lg font-semibold text-slate-900">Products & Services</h1>
          <p className="mt-0.5 text-sm text-slate-500">
            "Discovery" controls whether the scheduler searches for new leads for this product at
            all -- turn it off for products you don't want actively discovered right now.
          </p>
        </div>
        <button
          onClick={() => setShowAddForm((v) => !v)}
          className="flex shrink-0 items-center gap-1.5 rounded-md bg-slate-800 px-3.5 py-2 text-sm font-medium text-white hover:bg-slate-900"
        >
          {showAddForm ? <X size={14} /> : <Plus size={14} />}
          {showAddForm ? "Cancel" : "Add product"}
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {showAddForm && <ProductForm onCreated={handleCreated} />}

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
          <ProductForm product={editingProduct} onSaved={handleSaved} onCancel={() => setEditingProduct(null)} />
        </Modal>
      )}
    </div>
  );
}
