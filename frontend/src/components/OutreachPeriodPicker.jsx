import { useEffect, useState } from "react";
import { todayIST, daysAgoIST } from "../lib/istDate";

const PRESETS = [
  { key: "today", label: "Today" },
  { key: "week", label: "7 days" },
  { key: "month", label: "30 days" },
  { key: "all", label: "All time" },
  { key: "custom", label: "Custom" },
];

// Drives OutreachFunnelChart's single selected period -- any ONE of: today, a rolling
// week/month, a picked custom start/end range, or all-time. Calls onChange(start, end)
// with IST "YYYY-MM-DD" strings (both null for all-time) whenever the effective period
// changes. Its own file since both Analytics.jsx and DashboardWidget.jsx's widget need
// the identical control, not a redrawn copy that could drift (same reasoning as every
// other shared chart piece this session).
export default function OutreachPeriodPicker({ onChange }) {
  const [preset, setPreset] = useState("today");
  const [customStart, setCustomStart] = useState(todayIST());
  const [customEnd, setCustomEnd] = useState(todayIST());

  useEffect(() => {
    if (preset === "today") onChange(todayIST(), null);
    else if (preset === "week") onChange(daysAgoIST(6), todayIST());
    else if (preset === "month") onChange(daysAgoIST(29), todayIST());
    else if (preset === "all") onChange(null, null);
    // "custom" waits for the explicit Apply click below, not every keystroke.
  }, [preset]);

  return (
    <div className="mb-3 flex flex-wrap items-center gap-2">
      <div className="flex gap-1">
        {PRESETS.map((p) => (
          <button
            key={p.key}
            onClick={() => setPreset(p.key)}
            className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
              preset === p.key ? "bg-slate-800 text-white" : "text-slate-500 hover:bg-slate-100"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>
      {preset === "custom" && (
        <div className="flex items-center gap-1.5">
          <input
            type="date"
            value={customStart}
            max={customEnd}
            onChange={(e) => setCustomStart(e.target.value)}
            className="rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-700"
          />
          <span className="text-xs text-slate-400">to</span>
          <input
            type="date"
            value={customEnd}
            min={customStart}
            max={todayIST()}
            onChange={(e) => setCustomEnd(e.target.value)}
            className="rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-700"
          />
          <button
            onClick={() => onChange(customStart, customEnd)}
            className="rounded-md bg-slate-800 px-2.5 py-1 text-xs font-medium text-white hover:bg-slate-700"
          >
            Apply
          </button>
        </div>
      )}
    </div>
  );
}
