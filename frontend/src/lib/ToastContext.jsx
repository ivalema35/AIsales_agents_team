import { createContext, useCallback, useContext, useState } from "react";
import ToastStack from "../components/ui/Toast";

// Replaces permanent inline error banners (a red box that sits on the page forever until
// the next action happens to clear it) with a transient notification -- same information,
// but it doesn't become part of the page's furniture. Supports an optional action button so
// a toast can offer a real next step (e.g. "Force send anyway"), not just report a failure.
const ToastContext = createContext(null);

let nextId = 1;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((cur) => cur.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback((message, opts = {}) => {
    const id = nextId++;
    setToasts((cur) => [...cur, { id, message, variant: opts.variant || "info", ...opts }]);
    return id;
  }, []);

  toast.error = (message, opts) => toast(message, { ...opts, variant: "error" });
  toast.success = (message, opts) => toast(message, { ...opts, variant: "success" });

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <ToastStack toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast() must be used inside <ToastProvider>");
  return ctx;
}
