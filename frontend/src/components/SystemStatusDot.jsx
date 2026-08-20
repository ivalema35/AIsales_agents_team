// Compact liveness + automation-state indicator for the global nav (Phase 6 Step 6.3).
//
// The point is that the operator should never have to REMEMBER to check the System page.
// A process dying while they're on Leads or Dashboard has to reach them where they already
// are -- otherwise the monitor only works for someone who already suspects a problem.
//
// Two SEPARATE pieces, not one merged into the other:
// 1. Two dots, both showing the SAME health state, purely for looks (per the operator's own
//    direction: "2 dot... health ke liye... alternate bip"). They blink out of phase with
//    each other instead of pulsing in lockstep, which reads as more "alive" than one dot.
// 2. A labeled "Discovery: ON/OFF" badge -- a process can be very much alive while discovery
//    is deliberately off (looping past a no-op every tick), which the health dots alone
//    can't distinguish. Found live: an operator toggled discovery off from Settings and had
//    no way, anywhere in the CRM, to confirm it had taken effect.
import { useEffect, useRef, useState } from "react";
import { NavLink } from "react-router-dom";
import { api } from "../api/client";

const POLL_MS = 8000;

export default function SystemStatusDot() {
  const [state, setState] = useState("LOADING"); // LOADING | OK | PROBLEM | UNREACHABLE
  const [detail, setDetail] = useState("");
  const [discoveryOn, setDiscoveryOn] = useState(null); // null while unknown
  const timer = useRef(null);

  useEffect(() => {
    let alive = true;

    async function check() {
      try {
        const d = await api.getSystemLive();
        if (!alive) return;
        const bad = (d.processes || []).filter(
          (p) => p.state === "DOWN" || p.state === "ERROR"
        );
        setState(bad.length ? "PROBLEM" : "OK");
        setDetail(
          bad.length
            ? `${bad.length} process${bad.length > 1 ? "es" : ""} need attention`
            : "All processes running"
        );
        setDiscoveryOn(Boolean(d.toggles?.discovery_enabled));
      } catch {
        if (!alive) return;
        // Can't reach the API at all -- deliberately its own state, not folded into "problem".
        setState("UNREACHABLE");
        setDetail("Can't reach the backend");
      }
    }

    check();
    timer.current = setInterval(check, POLL_MS);
    return () => {
      alive = false;
      clearInterval(timer.current);
    };
  }, []);

  const dot = {
    LOADING: "bg-slate-300",
    OK: "bg-emerald-500",
    PROBLEM: "bg-amber-500",
    UNREACHABLE: "bg-red-500",
  }[state];

  return (
    <NavLink
      to="/system"
      title={`${detail || "System status"} · Discovery: ${
        discoveryOn === null ? "checking…" : discoveryOn ? "ON" : "OFF"
      }`}
      aria-label={`System status: ${detail || "checking"}. Discovery: ${
        discoveryOn === null ? "checking" : discoveryOn ? "ON" : "OFF"
      }.`}
      className="group flex items-center rounded-full transition-colors hover:bg-slate-100"
    >
      {/* One unified chip, not two floating pieces -- a shared pill with an internal
         divider reads as a single designed "status" widget instead of bare dots sitting
         next to an unrelated badge. */}
      <span className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 py-1 pl-2.5 pr-1 transition-colors group-hover:border-slate-300 group-hover:bg-white">
        {/* Two dots, same meaning, staggered pulse -- the second starts its animation half
           a cycle behind the first (animationDelay), so they blink alternately rather than
           together. Static dots (LOADING) skip the animation entirely -- nothing to
           alternate while state is still unknown. */}
        <span className="flex items-center gap-1">
          {[0, 1].map((i) => (
            <span key={i} className="relative flex h-2 w-2">
              {state !== "LOADING" && (
                <span
                  className={`absolute inline-flex h-full w-full animate-ping rounded-full ${dot} opacity-60`}
                  style={{ animationDelay: `${i * 0.6}s` }}
                />
              )}
              <span className={`relative inline-flex h-2 w-2 rounded-full ${dot} shadow-sm`} />
            </span>
          ))}
        </span>

        {/* Divider, not a gap -- makes clear the badge belongs to this same chip rather
           than being a second, unrelated element that happens to sit nearby. */}
        {discoveryOn !== null && <span className="h-3.5 w-px shrink-0 bg-slate-200" />}

        {/* Labelled, not another bare dot -- a color alone forces the operator to remember
           what it means; the word does not. */}
        {discoveryOn !== null && (
          <span
            className={`rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-tight ring-1 ring-inset ${
              discoveryOn
                ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
                : "bg-slate-100 text-slate-500 ring-slate-200"
            }`}
          >
            Discovery {discoveryOn ? "ON" : "OFF"}
          </span>
        )}
      </span>
    </NavLink>
  );
}
