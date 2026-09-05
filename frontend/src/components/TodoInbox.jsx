import { useEffect, useState } from "react";
import { Inbox } from "lucide-react";
import { api } from "../api/client";
import TodoItemCard from "./TodoItemCard";
import CampaignFormModal from "./CampaignFormModal";

// Phase 21 -- the unified AI Manager Inbox: every real, PENDING to-do the AI Sales
// Manager has raised, across every campaign AND every product's own "start a new
// campaign for X" idea, in one place. Replaces the old per-campaign daily_todo (only
// visible by clicking into that campaign's own Detail page one at a time) and the old
// "Suggested for today" section on the Calendar (folded into this same queue, scope
// GLOBAL). No fixed schedule gates what shows up here -- items arrive whenever the
// backend's daily floor or signal-driven tick judged something needed attention; this
// component just polls the same real queue any human review happens against.
const POLL_MS = 30000;

export default function TodoInbox() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);
  const [products, setProducts] = useState([]);
  const [formPrefill, setFormPrefill] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function refresh() {
      try {
        const data = await api.listTodos();
        if (!cancelled) setItems(data);
      } catch (err) {
        if (!cancelled) setError(err.message);
      }
    }
    refresh();
    const id = setInterval(refresh, POLL_MS);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  useEffect(() => {
    api.listProducts().then(setProducts).catch(() => {});
  }, []);

  function handleResolved(id) {
    setItems((prev) => (prev || []).filter((i) => i.id !== id));
  }

  if (error) {
    return (
      <div className="rounded-xl border border-line bg-parchment-raised p-4">
        <p className="text-sm text-alert-600">Couldn't reach the backend: {error}</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-line bg-parchment-raised p-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gold-100 text-gold-700">
          <Inbox size={14} />
        </span>
        <h2 className="font-display text-sm font-semibold text-ink-900">AI Manager Inbox</h2>
        {items && items.length > 0 && (
          <span className="rounded-full bg-gold-100 px-2 py-0.5 text-xs font-semibold text-gold-700">
            {items.length}
          </span>
        )}
      </div>

      {items === null && (
        <div className="flex flex-col gap-2">
          <div className="h-20 animate-pulse rounded-lg bg-parchment-raised-2" />
          <div className="h-20 animate-pulse rounded-lg bg-parchment-raised-2" />
        </div>
      )}

      {items && items.length === 0 && (
        <p className="text-sm text-ink-500">
          Nothing needs your attention right now -- the AI will add something here the moment it judges a
          real signal is worth a look, or at the latest by tomorrow's daily check.
        </p>
      )}

      {items && items.length > 0 && (
        <div className="flex flex-col gap-2.5">
          {items.map((item) => (
            <TodoItemCard
              key={item.id}
              item={item}
              showSourceChip
              onResolved={handleResolved}
              onApproveGlobal={(prefill) => setFormPrefill(prefill)}
            />
          ))}
        </div>
      )}

      {formPrefill && (
        <CampaignFormModal
          products={products}
          defaultDate={new Date().toISOString().slice(0, 10)}
          prefill={formPrefill}
          onClose={() => setFormPrefill(null)}
          onCreated={() => setFormPrefill(null)}
        />
      )}
    </div>
  );
}
