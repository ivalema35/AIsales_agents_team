import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useConfirm } from "../lib/ConfirmContext";

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

// Text/number settings (CRM_UI_UX_PLAN.md Phase 2) -- explicit Save, not save-on-keystroke,
// so a half-typed value never gets committed and a change is always a deliberate action
// (same reasoning as LeadDetail.jsx's ContactInfoForm).
function EditableField({ label, description, value, type, onSave, disabled }) {
  const [draft, setDraft] = useState(value);
  const [saving, setSaving] = useState(false);
  const dirty = String(draft) !== String(value);

  async function save() {
    setSaving(true);
    try {
      await onSave(type === "number" ? Number(draft) : draft);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex items-center justify-between gap-4 py-2">
      <div className="min-w-0">
        <p className="text-sm font-medium text-slate-900">{label}</p>
        <p className="text-xs text-slate-500">{description}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <input
          type={type}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          disabled={disabled}
          className={`rounded-md border border-slate-200 px-2 py-1 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-400 ${
            type === "number" ? "w-16" : "w-56"
          }`}
        />
        <button
          onClick={save}
          disabled={!dirty || saving || disabled}
          className="rounded-md bg-slate-800 px-2.5 py-1 text-xs font-medium text-white transition-colors hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {saving ? "…" : "Save"}
        </button>
      </div>
    </div>
  );
}

export default function SystemToggles() {
  const [settings, setSettings] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const confirm = useConfirm();

  useEffect(() => {
    api.getSettings().then(setSettings).catch((err) => setError(err.message));
  }, []);

  async function update(key, value) {
    // Turning on any real, unattended send to real businesses is a big deal -- confirm
    // explicitly, matching the project's non-negotiable "no autonomous real send without
    // explicit opt-in" rule (tracker.md A.3). Discovery has no such real-world side effect.
    const REAL_SEND_SWITCHES = {
      autonomous_outreach_enabled: "start REALLY emailing/WhatsApp-ing real businesses automatically",
      auto_reply_enabled: "let the AI send its own drafted replies to real businesses without a human reviewing them first",
      acknowledgment_reply_enabled: "let the AI send its own grounded reply to real businesses on any escalated inbound message, without a human reviewing it first",
    };
    if (value && REAL_SEND_SWITCHES[key]) {
      const ok = await confirm({
        title: "Turn this on?",
        message: `This will ${REAL_SEND_SWITCHES[key]}. Are you sure you want to turn this on?`,
        confirmLabel: "Turn on",
      });
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
    <>
    <div id="system-controls" className="scroll-mt-20 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
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
        <Toggle
          label="AI auto-reply"
          description="AI sends its own drafted reply for low-risk inbound objections. INTERESTED/DEMO/pricing always stay human-only."
          checked={settings.auto_reply_enabled}
          disabled={busy}
          dangerous
          onChange={(v) => update("auto_reply_enabled", v)}
        />
        <Toggle
          label="Escalation reply"
          description="Sends a real, grounded reply (from verified pain points + product info) plus a 'team will follow up' note, immediately, for any inbound message escalated to a human -- so leads aren't met with silence."
          checked={settings.acknowledgment_reply_enabled}
          disabled={busy}
          dangerous
          onChange={(v) => update("acknowledgment_reply_enabled", v)}
        />
      </div>
    </div>

    <div id="operational-settings" className="mt-5 scroll-mt-20 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-1 text-sm font-semibold text-slate-800">Operational settings</h2>
      <p className="mb-1 text-xs text-slate-400">
        Used to be .env-only (needed a restart to change) -- now dashboard-editable, takes effect on the next tick.
      </p>
      <div className="divide-y divide-slate-100">
        <EditableField
          label="EOD report email recipients"
          description="Comma-separated. Who gets the daily executive report by email."
          type="text"
          value={settings.eod_report_recipients}
          disabled={busy}
          onSave={(v) => update("eod_report_recipients", v)}
        />
        <EditableField
          label="EOD report WhatsApp recipients"
          description="Comma-separated phone numbers. Who gets the daily report on WhatsApp."
          type="text"
          value={settings.eod_report_whatsapp_recipients}
          disabled={busy}
          onSave={(v) => update("eod_report_whatsapp_recipients", v)}
        />
        <EditableField
          label="Daily email send cap"
          description="Max autonomous outreach emails per day, across all products."
          type="number"
          value={settings.outreach_daily_cap_email}
          disabled={busy}
          onSave={(v) => update("outreach_daily_cap_email", v)}
        />
        <EditableField
          label="Daily WhatsApp send cap"
          description="Max autonomous outreach WhatsApp messages per day, across all products."
          type="number"
          value={settings.outreach_daily_cap_whatsapp}
          disabled={busy}
          onSave={(v) => update("outreach_daily_cap_whatsapp", v)}
        />
        <EditableField
          label="Discovery cooldown (hours)"
          description="How long before the same product+query+region search can run again."
          type="number"
          value={settings.discovery_cooldown_hours}
          disabled={busy}
          onSave={(v) => update("discovery_cooldown_hours", v)}
        />
      </div>
    </div>
    </>
  );
}
