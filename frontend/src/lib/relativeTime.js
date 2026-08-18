// Minute/hour/day granularity -- for a "this lead just replied" alert, "20m ago" vs
// "3h ago" carries real urgency information that a day-only relative time would lose.
export function relativeTime(dateStr) {
  const then = new Date(dateStr.replace(" ", "T") + "Z").getTime();
  const mins = Math.floor((Date.now() - then) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}
