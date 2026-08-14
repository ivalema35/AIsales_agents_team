import { useEffect, useState } from "react";
import { api } from "../api/client";
import ProductForm from "../components/ProductForm";

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
      <p className="text-xs text-slate-500">
        Target regions: {strategy.target_regions.length ? strategy.target_regions.join(", ") : "none set"}
      </p>
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

export default function Products() {
  const [products, setProducts] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [error, setError] = useState(null);

  function refresh() {
    api.listProducts().then(setProducts).catch((err) => setError(err.message));
  }

  useEffect(refresh, []);

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-6">
      {error && <p className="text-sm text-red-600">{error}</p>}

      <ProductForm onCreated={refresh} />

      <div className="flex flex-col gap-2">
        <h2 className="text-sm font-semibold text-slate-700">Products & Services ({products.length})</h2>
        {products.map((p) => (
          <div key={p.id} className="rounded-lg border border-slate-200 bg-white p-4">
            <button
              onClick={() => setExpandedId(expandedId === p.id ? null : p.id)}
              className="flex w-full items-center justify-between text-left"
            >
              <div>
                <p className="text-sm font-medium text-slate-900">{p.title}</p>
                <p className="mt-0.5 text-xs text-slate-500 line-clamp-1">{p.description}</p>
              </div>
              <span className="text-xs text-slate-400">{expandedId === p.id ? "▲" : "▼"}</span>
            </button>
            {expandedId === p.id && (
              <div className="mt-3 border-t border-slate-100 pt-3">
                <StrategyView productId={p.id} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
