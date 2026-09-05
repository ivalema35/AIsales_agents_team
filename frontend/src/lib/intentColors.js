// A reply's intent isn't uniformly "urgent" -- INTERESTED/DEMO_REQUESTED is good news
// (green), OBJECTION means tread carefully (amber). Shared by LeadCard (Kanban) and the
// Leads table so a HOT_LEAD's intent badge reads the same color everywhere, not a
// redrawn palette per page.
// CRM_UI_UX_PLAN.md §1.3 (design system v2) -- re-tuned 2026-09-05 to the same
// good/warm/alert semantic tokens Badge.jsx and tierColors.js already use, so "good
// news"/"tread carefully"/"needs attention" read as one consistent color language
// wherever they show up, not a separate palette per file.
export const INTENT_STYLES = {
  INTERESTED: "bg-good-100 text-good-700 ring-good-600/30",
  DEMO_REQUESTED: "bg-good-100 text-good-700 ring-good-600/30",
  OBJECTION: "bg-warm-100 text-warm-700 ring-warm-600/30",
  STOP: "bg-parchment-raised-2 text-ink-500 ring-line",
};

export function intentBadgeClass(intent) {
  return INTENT_STYLES[intent] || "bg-alert-100 text-alert-700 ring-alert-600/30";
}
