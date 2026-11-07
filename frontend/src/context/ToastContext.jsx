import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Toast } from "../components/ui/Toast";
import { ToastContext } from "../hooks/useToast";

const REGION_IDLE = 4000;

export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null);
  const timer = useRef(null);

  const dismiss = useCallback(() => {
    if (timer.current) {
      window.clearTimeout(timer.current);
      timer.current = null;
    }
    setToast(null);
  }, []);

  const showToast = useCallback(
    (message, options = {}) => {
      if (timer.current) window.clearTimeout(timer.current);
      setToast({
        message,
        tone: options.tone ?? "success",
        duration: options.duration ?? REGION_IDLE,
      });
      timer.current = window.setTimeout(() => {
        setToast(null);
        timer.current = null;
      }, options.duration ?? REGION_IDLE);
    },
    [],
  );

  useEffect(() => {
    return () => {
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, []);

  const value = useMemo(() => ({ showToast, dismiss }), [showToast, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <Toast
        message={toast?.message ?? ""}
        tone={toast?.tone ?? "success"}
        onDismiss={toast ? dismiss : undefined}
      />
    </ToastContext.Provider>
  );
}
