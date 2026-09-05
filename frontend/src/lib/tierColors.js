// Same tier hues used elsewhere (ProductTable's distribution bar). Two intensities per
// tier: a translucent WASH for a card/row's own background and the solid hex for a left
// border accent, which stays a touch bolder than the wash so the edge still reads as a
// defined line rather than just fading into the tint. Color is a SUPPLEMENT to the
// Badge text, never a replacement for it (never color-alone) -- the badge still carries
// the exact label for anyone who needs it explicitly. Shared by LeadCard (Kanban) and
// the Leads table so a HOT lead reads the same red wash everywhere, not a redrawn one.
// CRM_UI_UX_PLAN.md §1.3 (design system v2) -- re-tuned 2026-09-05 to match Badge.jsx's
// already-migrated HOT/WARM/COLD tokens, so a Kanban card's wash/edge and its own Badge
// text agree on the same tier color instead of two different palettes for one fact.
export const TIER_BG = { HOT: "bg-alert-100/70", WARM: "bg-warm-100/60", COLD: "bg-parchment-raised-2/70" };
export const TIER_BORDER = { HOT: "#a83b32", WARM: "#96631c", COLD: "#6c7093" };
