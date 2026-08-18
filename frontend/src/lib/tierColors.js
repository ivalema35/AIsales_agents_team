// Same tier hues used elsewhere (ProductTable's distribution bar). Two intensities per
// tier: a translucent WASH for a card/row's own background and the solid hex for a left
// border accent, which stays a touch bolder than the wash so the edge still reads as a
// defined line rather than just fading into the tint. Color is a SUPPLEMENT to the
// Badge text, never a replacement for it (never color-alone) -- the badge still carries
// the exact label for anyone who needs it explicitly. Shared by LeadCard (Kanban) and
// the Leads table so a HOT lead reads the same red wash everywhere, not a redrawn one.
export const TIER_BG = { HOT: "bg-red-50/70", WARM: "bg-amber-50/60", COLD: "bg-slate-100/70" };
export const TIER_BORDER = { HOT: "#dc2626", WARM: "#d97706", COLD: "#94a3b8" };
