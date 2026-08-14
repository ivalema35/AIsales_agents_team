import { useEffect, useState } from "react";
import { api } from "../api/client";

function Toggle({ label, description, checked, onChange, disabled, dangerous }) {
  // Inline styles for the track color and knob position -- not Tailwind utility
  // classes -- so there's zero ambiguity about which state renders which way
  // (a user-reported bug had the knob look "on" while the setting was actually off).
  const trackColor = checked ? (dangerous ? "#dc2626" : "#059669") : "#d1d5db";
  const knobLeft = checked ? "22px" : "2px";

  return (
    <div className="flex items-center justify-between gap-4 py-2">
      <div>
        <p className="text-sm font-medium text-slate-900">{label}</p>
        <p className="text-xs text-slate-500">{description}</p>
      </div>
      <div className="flex items-center gap-2">
        <span className={`text-xs font-semibold ${checked ? "text-slate-900" : "text-slate-400"}`}>
          {checked ? "ON" : "OFF"}
        </span>
        <button
          role="switch"
          aria-checked={checked}
          disabled={disabled}
          onClick={() => onChange(!checked)}
          style={{ backgroundColor: trackColor }}
          className="relative h-6 w-11 shrink-0 rounded-full transition-colors disabled:opacity-50"
        >
          <span
            style={{ left: knobLeft }}
            className="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all"
          />
        </button>
      </div>
    </div>
  );
}

export default function SystemToggles() {
  const [settings, setSettings] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.getSettings().then(setSettings).catch((err) => setError(err.message));
  }, []);

  async function update(key, value) {
    // Turning on real outreach to real businesses is a big deal -- confirm explicitly,
    // matching the project's non-negotiable "no autonomous real send without explicit
    // opt-in" rule (tracker.md A.3). Discovery has no such real-world side effect.
    if (key === "autonomous_outreach_enabled" && value) {
      const ok = window.confirm(
        "This will let the system start REALLY emailing/WhatsApp-ing real businesses " +
        "automatically. Are you sure you want to turn this on?"
      );
      if (!ok) return;
    }

    setBusy(true);
    setError(null);
    try {
      const updated = await api.patchSettings({ [key]: value });
      setSettings(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (!settings) return null;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <h2 className="mb-1 text-sm font-semibold text-slate-800">System controls</h2>
      {error && <p className="mb-2 text-xs text-red-600">{error}</p>}
      <div className="divide-y divide-slate-100">
        <Toggle
          label="Discovery"
          description="AI searches for and scores new leads across your products."
          checked={settings.discovery_enabled}
          disabled={busy}
          onChange={(v) => update("discovery_enabled", v)}
        />
        <Toggle
          label="Autonomous outreach"
          description="AI actually sends emails/WhatsApp to real businesses. Off = safe."
          checked={settings.autonomous_outreach_enabled}
          disabled={busy}
          dangerous
          onChange={(v) => update("autonomous_outreach_enabled", v)}
        />
      </div>
    </div>
  );
}
