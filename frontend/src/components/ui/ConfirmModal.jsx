import { useEffect } from "react";
import { AlertTriangle } from "lucide-react";

// Every real send in this app (real email, real WhatsApp, flipping an autonomous-send
// switch) confirms first -- this is that confirmation's actual UI, styled to match the
// CRM instead of the browser's own native "this site says" chrome.
export default function ConfirmModal({
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  danger = true,
  onConfirm,
  onCancel,
}) {
  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") onCancel();
      if (e.key === "Enter") onConfirm();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onConfirm, onCancel]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/40 p-4"
      onClick={onCancel}
    >
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-modal-title"
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-sm rounded-lg border border-line bg-parchment-raised p-5 shadow-xl"
      >
        <div className="flex items-start gap-3">
          <div
            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
              danger ? "bg-alert-100 text-alert-600" : "bg-parchment-raised-2 text-ink-700"
            }`}
          >
            <AlertTriangle size={18} />
          </div>
          <div className="min-w-0 pt-0.5">
            <h3 id="confirm-modal-title" className="font-display text-sm font-semibold text-ink-900">
              {title || "Are you sure?"}
            </h3>
            <p className="mt-1 text-sm leading-relaxed text-ink-700">{message}</p>
          </div>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="rounded-md px-3 py-1.5 text-xs font-medium text-ink-700 transition-colors hover:bg-parchment-raised-2"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            autoFocus
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              danger
                ? "bg-alert-600 text-white hover:opacity-90"
                : "bg-ink-900 text-parchment-raised hover:opacity-90"
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
