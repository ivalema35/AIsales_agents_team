import { useEffect } from "react";
import { AlertTriangle, CheckCircle2, Info, X } from "lucide-react";

const VARIANT = {
  error: { icon: AlertTriangle, chip: "bg-red-50 text-red-600", ring: "ring-red-100", text: "text-slate-800" },
  success: { icon: CheckCircle2, chip: "bg-emerald-50 text-emerald-600", ring: "ring-emerald-100", text: "text-slate-800" },
  info: { icon: Info, chip: "bg-slate-100 text-slate-500", ring: "ring-slate-100", text: "text-slate-800" },
};

// One toast. Auto-dismisses UNLESS it carries an action button -- a toast offering "Force
// send anyway" that vanishes on its own timer before the operator can click it would defeat
// the entire point of offering the action.
function ToastItem({ toast, onDismiss }) {
  const { icon: Icon, chip, ring, text } = VARIANT[toast.variant] || VARIANT.info;

  useEffect(() => {
    if (toast.action) return; // has an action -> stays until dismissed or acted on
    const t = setTimeout(() => onDismiss(toast.id), toast.duration ?? 5000);
    return () => clearTimeout(t);
  }, [toast, onDismiss]);

  return (
    <div
      role="alert"
      className={`animate-toast-in pointer-events-auto flex w-full max-w-md items-start gap-3 rounded-xl bg-white p-3.5 shadow-lg ring-1 ring-inset ${ring}`}
    >
      {/* Icon in its own colored chip, matching ConfirmModal's language, rather than a bare
         colored icon floating in a tinted box -- reads as one consistent "alert" visual
         idiom across the app instead of toast and modal each inventing their own. */}
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${chip}`}>
        <Icon size={16} />
      </div>
      <div className="min-w-0 flex-1 pt-0.5">
        <p className={`text-xs leading-relaxed ${text}`}>{toast.message}</p>
        {toast.action && (
          <button
            onClick={() => {
              toast.action.onClick();
              onDismiss(toast.id);
            }}
            className="mt-2 rounded-md bg-slate-800 px-2.5 py-1 text-[11px] font-semibold text-white shadow-sm transition-colors hover:bg-slate-900"
          >
            {toast.action.label}
          </button>
        )}
      </div>
      <button
        onClick={() => onDismiss(toast.id)}
        className="shrink-0 rounded p-0.5 text-slate-300 transition-colors hover:bg-slate-100 hover:text-slate-500"
        aria-label="Dismiss"
      >
        <X size={13} />
      </button>
    </div>
  );
}

// Top-center, newest at the bottom of the stack (so a second toast doesn't cover the first
// one's action button before it's been seen) -- top rather than bottom-right because that's
// directly in the operator's eyeline right under the nav, not off in a corner easy to miss
// entirely on a tall page.
export default function ToastStack({ toasts, onDismiss }) {
  if (!toasts.length) return null;
  return (
    <div className="pointer-events-none fixed left-1/2 top-4 z-50 flex w-full max-w-md -translate-x-1/2 flex-col gap-2 px-4">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </div>
  );
}
