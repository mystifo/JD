import { useEffect } from "react";

/**
 * Warn before a full-page unload when a form has unsaved changes.
 *
 * In-app route blocking is wired with React Router's data-router blocker when
 * the journal editor lands (M5); M3 screens only need the browser warning.
 */
export function useUnsavedChanges(enabled, message = "You have unsaved changes.") {
  useEffect(() => {
    if (!enabled) return undefined;

    function onBeforeUnload(event) {
      event.preventDefault();
      event.returnValue = message;
      return message;
    }

    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [enabled, message]);
}
