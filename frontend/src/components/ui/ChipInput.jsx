import { useState } from "react";
import { X } from "lucide-react";

export function FieldLabel({ icon: Icon, children, hint }) {
  return (
    <div className="mb-1.5">
      <span className="flex items-center gap-1.5 text-xs font-medium text-slate-700">
        <Icon size={13} className="text-slate-400" /> {children}
      </span>
      {hint && <p className="mt-0.5 text-[11px] leading-relaxed text-slate-400">{hint}</p>}
    </div>
  );
}

// Reusable chip-input behavior: type + Enter/comma to add, Backspace on empty input to
// pop the last chip, blur to commit whatever's typed. Originally built for
// target_regions/target_business_categories/target_person_roles (Phase 7 Step 7.1),
// moved here (from ProductForm.jsx) so Phase 8 Step 8.5's format-builder can reuse the
// exact same UX for a format's ordered guideline sections, instead of a second copy.
export default function ChipInput({ icon, label, hint, values, onChange, placeholder }) {
  const [draft, setDraft] = useState("");

  function commit() {
    const v = draft.trim();
    if (v && !values.includes(v)) onChange([...values, v]);
    setDraft("");
  }

  function remove(v) {
    onChange(values.filter((x) => x !== v));
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      commit();
    } else if (e.key === "Backspace" && !draft && values.length > 0) {
      remove(values[values.length - 1]);
    }
  }

  return (
    <label className="flex flex-col">
      <FieldLabel icon={icon} hint={hint}>{label}</FieldLabel>
      <div className="flex flex-wrap items-center gap-1.5 rounded-md border border-slate-300 px-2 py-1.5 focus-within:border-slate-400 focus-within:ring-2 focus-within:ring-slate-100">
        {values.map((v) => (
          <span key={v} className="flex items-center gap-1 rounded bg-slate-100 px-2 py-1 text-xs text-slate-700">
            {v}
            <button
              type="button"
              onClick={() => remove(v)}
              className="text-slate-400 hover:text-slate-700"
              aria-label={`Remove ${v}`}
            >
              <X size={11} />
            </button>
          </span>
        ))}
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={commit}
          placeholder={values.length === 0 ? placeholder : "Add another…"}
          className="min-w-[110px] flex-1 border-none px-1 py-1 text-sm text-slate-800 placeholder:text-slate-300 outline-none"
        />
      </div>
    </label>
  );
}
