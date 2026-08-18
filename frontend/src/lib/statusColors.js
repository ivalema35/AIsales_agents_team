// Single source of truth for a lead's pipeline STATUS color -- used everywhere a status
// is shown (Kanban columns, LeadCard/LeadDetail status badges, the Analytics funnel) so
// "SCORED" (for example) is always the same color, not a different one per page. This is
// deliberately separate from TIER color (HOT/WARM/COLD, in Badge.jsx) -- a lead's tier and
// its pipeline status are two different facts shown side by side, not the same thing.
//
// `hex` matches the dataviz skill's validated categorical palette (references/palette.md)
// where a slot was available, so the Analytics charts and these badges read as the same
// color language; the remaining statuses use adjacent Tailwind hues chosen for enough
// separation from both the palette slots and each other.
export const STATUS_COLORS = {
  DISCOVERED: { hex: "#94a3b8", badge: "bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-300" },
  ENRICHED: { hex: "#38bdf8", badge: "bg-sky-50 text-sky-700 ring-1 ring-inset ring-sky-200" },
  REVIEWED: { hex: "#818cf8", badge: "bg-indigo-50 text-indigo-700 ring-1 ring-inset ring-indigo-200" },
  SCORED: { hex: "#2a78d6", badge: "bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-200" },
  OUTREACHING: { hex: "#eda100", badge: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200" },
  OUTREACHED: { hex: "#eb6834", badge: "bg-orange-50 text-orange-700 ring-1 ring-inset ring-orange-200" },
  ENGAGED: { hex: "#1baf7a", badge: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200" },
  HOT_LEAD: { hex: "#e34948", badge: "bg-red-50 text-red-700 ring-1 ring-inset ring-red-200" },
  CONVERTED: { hex: "#008300", badge: "bg-green-50 text-green-700 ring-1 ring-inset ring-green-200" },
  REJECTED: { hex: "#9ca3af", badge: "bg-slate-100 text-slate-400 ring-1 ring-inset ring-slate-200" },
};

export function statusHex(status) {
  return STATUS_COLORS[status]?.hex || "#94a3b8";
}

export function statusBadgeClass(status) {
  return STATUS_COLORS[status]?.badge || STATUS_COLORS.DISCOVERED.badge;
}
