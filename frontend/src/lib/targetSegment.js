// 2026-09-07 -- target_segment.industry can now be a single vertical (string) or several
// (array, when a campaign genuinely targets more than one business type at once). Every
// display site used to assume a plain string; this is the one place that formats either
// shape consistently instead of each component reinventing its own join logic.
export function industryLabel(target) {
  const industry = target?.industry;
  if (Array.isArray(industry)) return industry.filter(Boolean).join(", ");
  return industry || "";
}

// 2026-09-08 -- same dual shape for location (one city string, or several cities).
export function locationLabel(target) {
  const location = target?.location ?? target;
  if (Array.isArray(location)) return location.filter(Boolean).join(", ");
  if (typeof location === "string") return location;
  return "";
}
