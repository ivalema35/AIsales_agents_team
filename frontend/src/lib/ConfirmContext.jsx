import { createContext, useCallback, useContext, useRef, useState } from "react";
import ConfirmModal from "../components/ui/ConfirmModal";

// Replaces the browser's native window.confirm() -- which renders as an ugly, obviously
// "this is a website talking to you" OS-chrome popup ("localhost:5173 says...") -- with
// an in-app styled modal that actually looks like part of the CRM. Same blocking-decision
// contract as window.confirm (await it, get a boolean back) so call sites barely change.
const ConfirmContext = createContext(null);

export function ConfirmProvider({ children }) {
  const [request, setRequest] = useState(null);
  const resolver = useRef(null);

  const confirm = useCallback((options) => {
    return new Promise((resolve) => {
      resolver.current = resolve;
      setRequest(typeof options === "string" ? { message: options } : options);
    });
  }, []);

  function settle(result) {
    resolver.current?.(result);
    resolver.current = null;
    setRequest(null);
  }

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {request && (
        <ConfirmModal {...request} onConfirm={() => settle(true)} onCancel={() => settle(false)} />
      )}
    </ConfirmContext.Provider>
  );
}

export function useConfirm() {
  const ctx = useContext(ConfirmContext);
  if (!ctx) throw new Error("useConfirm() must be used inside <ConfirmProvider>");
  return ctx;
}
