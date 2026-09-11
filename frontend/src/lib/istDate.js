// The business (and every backend day-bucket) runs on IST, not the browser's local
// timezone -- a "Today" preset built from the browser's own local date would pick the
// wrong calendar day for anyone not physically in IST. Mirrors backend's IST_OFFSET
// (+5:30, services/reporting_service.py).
const IST_OFFSET_MS = (5 * 60 + 30) * 60 * 1000;

export function todayIST() {
  const now = new Date();
  const utcMs = now.getTime() + now.getTimezoneOffset() * 60000;
  return new Date(utcMs + IST_OFFSET_MS).toISOString().slice(0, 10);
}

export function daysAgoIST(n) {
  const now = new Date();
  const utcMs = now.getTime() + now.getTimezoneOffset() * 60000;
  return new Date(utcMs + IST_OFFSET_MS - n * 86400000).toISOString().slice(0, 10);
}

// Converts a raw backend timestamp (Python's str(datetime) -- "YYYY-MM-DD HH:MM:SS[.ffffff]",
// UTC, no timezone suffix) to its real IST calendar-date string. Naively slicing the raw
// string's first 10 characters compares a UTC date against an IST "today" -- wrong for
// any timestamp in the 00:00-05:29 IST window (still "yesterday" in UTC). Same fix
// pattern as LeadDetail.jsx's timeLabel()/dayLabel() (append "Z" so Date parses it as UTC).
export function toISTDateString(rawDateStr) {
  if (!rawDateStr) return "";
  const ms = new Date(String(rawDateStr).replace(" ", "T") + "Z").getTime();
  if (Number.isNaN(ms)) return "";
  return new Date(ms + IST_OFFSET_MS).toISOString().slice(0, 10);
}
