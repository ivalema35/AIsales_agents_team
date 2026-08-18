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
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      onClick={onCancel}
    >
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-modal-title"
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-sm rounded-lg bg-white p-5 shadow-xl"
      >
        <div className="flex items-start gap-3">
          <div
            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
              danger ? "bg-red-50 text-red-600" : "bg-slate-100 text-slate-600"
            }`}
          >
            <AlertTriangle size={18} />
          </div>
          <div className="min-w-0 pt-0.5">
            <h3 id="confirm-modal-title" className="text-sm font-semibold text-slate-900">
              {title || "Are you sure?"}
            </h3>
            <p className="mt-1 text-sm leading-relaxed text-slate-600">{message}</p>
          </div>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="rounded-md px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            autoFocus
            className={`rounded-md px-3 py-1.5 text-xs font-medium text-white transition-colors ${
              danger ? "bg-red-600 hover:bg-red-700" : "bg-slate-800 hover:bg-slate-900"
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
