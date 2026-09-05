// Shared status/tier/outcome pill (CRM_UI_UX_PLAN.md §1.3 -- design system v2, re-tuned
// 2026-09-01 to the parchment/ink-navy/gold palette). Semantic meaning unchanged from
// §1.2, only the hues moved to sit correctly on the new warm parchment surface.
const VARIANTS = {
  HOT: "bg-alert-100 text-alert-700 ring-1 ring-inset ring-alert-600/30",
  WARM: "bg-warm-100 text-warm-700 ring-1 ring-inset ring-warm-600/30",
  COLD: "bg-parchment-raised-2 text-ink-500 ring-1 ring-inset ring-line",
  SUCCESS: "bg-good-100 text-good-700 ring-1 ring-inset ring-good-600/30",
  DANGER: "bg-alert-100 text-alert-700 ring-1 ring-inset ring-alert-600/30",
  WARNING: "bg-warm-100 text-warm-700 ring-1 ring-inset ring-warm-600/30",
  NEUTRAL: "bg-parchment-raised-2 text-ink-700 ring-1 ring-inset ring-line",
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
