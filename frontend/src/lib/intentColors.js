// A reply's intent isn't uniformly "urgent" -- INTERESTED/DEMO_REQUESTED is good news
// (green), OBJECTION means tread carefully (amber). Shared by LeadCard (Kanban) and the
// Leads table so a HOT_LEAD's intent badge reads the same color everywhere, not a
// redrawn palette per page.
export const INTENT_STYLES = {
  INTERESTED: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  DEMO_REQUESTED: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  OBJECTION: "bg-amber-50 text-amber-700 ring-amber-200",
  STOP: "bg-slate-100 text-slate-500 ring-slate-200",
};

export function intentBadgeClass(intent) {
  return INTENT_STYLES[intent] || "bg-red-50 text-red-600 ring-red-200";
}
