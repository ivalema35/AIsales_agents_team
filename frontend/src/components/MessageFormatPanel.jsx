import { useEffect, useState } from "react";
import { ListOrdered, Plus, Save, X, History } from "lucide-react";
import { api } from "../api/client";
import ChipInput from "./ui/ChipInput";
import Badge from "./ui/Badge";

const CHANNELS = ["EMAIL", "WHATSAPP"];

// Phase 8 Step 8.5 -- format builder UI. "sections" is a GUIDELINE list (tracker.md A.7:
// the AI still writes its own adaptive copy, this only sets the shape/order it follows),
// so the editor here is deliberately the same free-text chip list as target_regions/
// target_business_categories, not a rigid form with fixed fields.
export default function MessageFormatPanel({ productId }) {
  const [formats, setFormats] = useState(null);
  const [channel, setChannel] = useState("EMAIL");
  const [editing, setEditing] = useState(false);
  const [draftSections, setDraftSections] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  function refresh() {
    api.listMessageFormats({ product_id: productId, channel }).then(setFormats).catch((err) => setError(err.message));
  }

  useEffect(refresh, [productId, channel]);

  const active = formats?.find((f) => f.status === "ACTIVE");
  const history = formats?.filter((f) => f.status !== "ACTIVE") || [];

  function startEdit() {
    setDraftSections(active ? [...active.sections] : []);
    setEditing(true);
  }

  async function save() {
    if (draftSections.length === 0) return;
    setSaving(true);
    setError(null);
    try {
      await api.createMessageFormat({ product_id: productId, channel, sections: draftSections });
      setEditing(false);
      refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function clearFormat() {
    if (!active) return;
    setSaving(true);
    try {
      await api.deactivateMessageFormat(active.id);
      refresh();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-1.5">
        {CHANNELS.map((c) => (
          <button
            key={c}
            onClick={() => { setChannel(c); setEditing(false); }}
            className={`rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors ${
              channel === c ? "bg-slate-800 text-white" : "bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-50"
            }`}
          >
            {c}
          </button>
        ))}
        {channel === "WHATSAPP" && (
          <span className="text-[11px] text-amber-600">
            not yet used by sends -- WhatsApp cold-outreach is Meta-template-based, not free-form
          </span>
        )}
      </div>

      {error && <p className="text-xs text-red-600">{error}</p>}

      {!editing && (
        <>
          {active ? (
            <div className="rounded-md bg-slate-50 p-3">
              <div className="mb-2 flex items-center justify-between">
                <Badge variant="SUCCESS">v{active.version} · ACTIVE</Badge>
                <div className="flex gap-2">
                  <button onClick={startEdit} className="text-[11px] font-medium text-slate-600 hover:text-slate-900">
                    Edit (new version)
                  </button>
                  <button onClick={clearFormat} disabled={saving} className="text-[11px] font-medium text-red-500 hover:text-red-700">
                    Clear (revert to free-form)
                  </button>
                </div>
              </div>
              <ol className="list-decimal space-y-1 pl-4 text-xs text-slate-700">
                {active.sections.map((s, i) => <li key={i}>{s}</li>)}
              </ol>
            </div>
          ) : (
            <div className="flex items-center justify-between rounded-md bg-slate-50 p-3">
              <p className="text-xs text-slate-500">
                No format set for {channel} -- the AI drafts freely (today's default behavior).
              </p>
              {channel === "EMAIL" && (
                <button
                  onClick={startEdit}
                  className="flex shrink-0 items-center gap-1 rounded-md bg-slate-800 px-2.5 py-1.5 text-[11px] font-medium text-white hover:bg-slate-900"
                >
                  <Plus size={12} /> Define a format
                </button>
              )}
            </div>
          )}

          {history.length > 0 && (
            <div>
              <button
                onClick={() => setShowHistory((v) => !v)}
                className="flex items-center gap-1 text-[11px] font-medium text-slate-400 hover:text-slate-600"
              >
                <History size={11} /> {showHistory ? "Hide" : "Show"} {history.length} superseded version{history.length > 1 ? "s" : ""}
              </button>
              {showHistory && (
                <div className="mt-2 flex flex-col gap-2">
                  {history.map((f) => (
                    <div key={f.id} className="rounded-md border border-slate-100 p-2">
                      <Badge variant="NEUTRAL">v{f.version}</Badge>
                      <ol className="mt-1 list-decimal space-y-0.5 pl-4 text-[11px] text-slate-400">
                        {f.sections.map((s, i) => <li key={i}>{s}</li>)}
                      </ol>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {editing && (
        <div className="flex flex-col gap-2 rounded-md border border-slate-200 p-3">
          <ChipInput
            icon={ListOrdered}
            label="Format sections (guidelines, in order)"
            hint="Each entry is an instruction the AI follows while writing its own adaptive copy -- not literal text it inserts."
            values={draftSections}
            onChange={setDraftSections}
            placeholder="Personal greeting, mention 2-3 real pain points, demo link…"
          />
          <div className="flex items-center gap-2">
            <button
              onClick={save}
              disabled={saving || draftSections.length === 0}
              className="flex items-center gap-1.5 rounded-md bg-slate-800 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-900 disabled:opacity-50"
            >
              <Save size={12} /> {saving ? "Saving…" : "Save as new version"}
            </button>
            <button
              onClick={() => setEditing(false)}
              className="flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-medium text-slate-500 hover:bg-slate-100"
            >
              <X size={12} /> Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
