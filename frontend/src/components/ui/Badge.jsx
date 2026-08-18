// Shared status/tier/outcome pill (CRM_UI_UX_PLAN.md §1.2) -- replaces the ad-hoc
// TIER_STYLES-style objects that used to get re-declared per-component.
const VARIANTS = {
  HOT: "bg-red-50 text-red-700 ring-1 ring-inset ring-red-200",
  WARM: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200",
  COLD: "bg-slate-100 text-slate-500 ring-1 ring-inset ring-slate-200",
  SUCCESS: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200",
  DANGER: "bg-red-50 text-red-700 ring-1 ring-inset ring-red-200",
  WARNING: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200",
  NEUTRAL: "bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-200",
};

export default function Badge({ variant = "NEUTRAL", children, className = "" }) {
  const style = VARIANTS[variant] || VARIANTS.NEUTRAL;
  return (
    <span
      className={`inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-[11px] font-semibold ${style} ${className}`}
    >
      {children}
    </span>
  );
}
