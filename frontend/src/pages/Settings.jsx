import { useEffect, useMemo, useState } from "react";
import { Info } from "lucide-react";
import { api } from "../api/client";
import SystemToggles from "../components/SystemToggles";

function slugify(name) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}

// One field: text/number for non-secrets (shows the real current value), password-style
// write-only for secrets (never shows the real value -- only a masked hint of what's
// already configured). Explicit Save, same pattern as every other editable field built
// this session (LeadDetail's ContactInfoForm, SystemToggles' EditableField) -- a change
// here is always a deliberate action, never a stray keystroke.
function EnvField({ setting, onSaved }) {
  const [draft, setDraft] = useState(setting.is_secret ? "" : setting.value ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const dirty = setting.is_secret ? draft.length > 0 : draft !== (setting.value ?? "");

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const res = await api.patchEnvSettings({ [setting.key]: draft });
      onSaved(res.settings);
      if (setting.is_secret) setDraft("");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-1.5 border-b border-slate-100 py-3 last:border-0">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-1.5">
          <span className="text-sm font-medium text-slate-800">{setting.label}</span>
          <span className="group relative">
            <Info size={13} className="mt-0.5 text-slate-300 hover:text-slate-500" />
            <span className="pointer-events-none absolute left-1/2 top-5 z-20 w-64 -translate-x-1/2 rounded-md bg-slate-800 px-2.5 py-1.5 text-[11px] leading-relaxed text-white opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
              {setting.hint}
            </span>
          </span>
        </div>
        {setting.is_secret && (
          <span className={`shrink-0 text-[11px] font-medium ${setting.configured ? "text-emerald-600" : "text-amber-600"}`}>
            {setting.configured ? `Configured (${setting.masked})` : "Not set"}
          </span>
        )}
      </div>
      <div className="flex items-center gap-2">
        <input
          // Deliberately type="text", not "password" -- this field is ALWAYS empty by
          // default (secrets are write-only, nothing is ever pre-filled), so there was
          // no real masking benefit to "password", and it actively backfired: browsers
          // treat any type="password" field as a login form and auto-inject a saved
          // credential into it, which doesn't fire a normal input event -- what's visibly
          // shown stops matching this field's real value, so copy/paste on it silently
          // does nothing (found live, 2026-08-17). autoComplete="off" plus the password-
          // manager-specific ignore attributes stop that auto-injection at the source.
          type={setting.type === "int" ? "number" : "text"}
          autoComplete="off"
          autoCorrect="off"
          spellCheck={false}
          data-lpignore="true"
          data-1p-ignore="true"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={setting.is_secret ? "Enter a new value to replace it" : ""}
          className="min-w-0 flex-1 rounded-md border border-slate-200 px-2.5 py-1.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-400"
        />
        <button
          onClick={save}
          disabled={!dirty || saving}
          className="shrink-0 rounded-md bg-slate-800 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {saving ? "Saving…" : "Save"}
        </button>
      </div>
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  );
}

export default function Settings() {
  const [envSettings, setEnvSettings] = useState(null);
  const [error, setError] = useState(null);
  const [savedNote, setSavedNote] = useState(false);

  useEffect(() => {
    api.getEnvSettings().then(setEnvSettings).catch((err) => setError(err.message));
  }, []);

  function handleSaved(updated) {
    setEnvSettings(updated);
    setSavedNote(true);
  }

  const categories = useMemo(() => {
    if (!envSettings) return [];
    const order = [];
    const byCategory = {};
    for (const s of envSettings) {
      if (!byCategory[s.category]) {
        byCategory[s.category] = [];
        order.push(s.category);
      }
      byCategory[s.category].push(s);
    }
    return order.map((name) => ({ name, id: slugify(name), items: byCategory[name] }));
  }, [envSettings]);

  const navItems = [
    { id: "system-controls", label: "System controls" },
    { id: "operational-settings", label: "Operational settings" },
    { id: "company-contact", label: "Company contact details" },
    ...categories.map((c) => ({ id: c.id, label: c.name })),
  ];

  return (
    <div className="mx-auto flex max-w-7xl gap-8 px-6 py-6">
      {/* Sticky section nav -- this page is long (system switches + 6 .env categories),
         a plain scroll made jumping to e.g. "WhatsApp" tedious. Hidden below lg (matches
         CRM_UI_UX_PLAN.md's responsiveness floor) rather than squeezed into a cramped
         column on a laptop-width window. */}
      <aside className="sticky top-20 hidden h-fit w-48 shrink-0 flex-col gap-0.5 lg:flex">
        {navItems.map((item) => (
          <a
            key={item.id}
            href={`#${item.id}`}
            className="rounded-md px-2.5 py-1.5 text-sm text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
          >
            {item.label}
          </a>
        ))}
      </aside>

      <div className="flex min-w-0 flex-1 flex-col gap-6">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">Settings</h1>
          <p className="mt-0.5 text-sm text-slate-500">
            System switches take effect on the next scheduler tick. Everything below that
            (API keys, provider config) is saved to <code className="rounded bg-slate-100 px-1 py-0.5 text-xs">.env</code> and
            needs a backend restart to apply.
          </p>
        </div>

        {savedNote && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-xs text-amber-800">
            Saved to .env -- these values are only read when a backend process starts, so
            restart the affected process(es) for this to actually take effect.
          </div>
        )}

        <SystemToggles />

        {error && <p className="text-sm text-red-600">{error}</p>}
        {!envSettings && !error && <p className="text-sm text-slate-400">Loading…</p>}

        {envSettings && (
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
            {categories.map(({ name, id, items }) => (
              <div key={id} id={id} className="h-fit scroll-mt-20 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                <h3 className="mb-1 text-sm font-semibold text-slate-800">{name}</h3>
                <div>
                  {items.map((s) => (
                    <EnvField key={s.key} setting={s} onSaved={handleSaved} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
