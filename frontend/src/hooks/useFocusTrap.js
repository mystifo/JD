import { useEffect, useRef } from "react";

const FOCUSABLE = [
  "a[href]",
  "button:not([disabled])",
  "textarea:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

function focusableInside(node) {
  return Array.from(node.querySelectorAll(FOCUSABLE)).filter(
    (element) => element.getAttribute("aria-hidden") !== "true",
  );
}

/**
 * Keep keyboard focus inside `ref` while `active`. Restores focus to the
 * trigger when the trap closes.
 */
export function useFocusTrap(active, { onEscape, initialFocus } = {}) {
  const ref = useRef(null);
  const escapeRef = useRef(onEscape);
  const initialRef = useRef(initialFocus);

  useEffect(() => {
    escapeRef.current = onEscape;
    initialRef.current = initialFocus;
  }, [onEscape, initialFocus]);

  useEffect(() => {
    if (!active) return undefined;
    const node = ref.current;
    if (!node) return undefined;

    const previous = document.activeElement;
    const target = initialRef.current?.current ?? focusableInside(node)[0] ?? node;
    target.focus?.();

    function onKeyDown(event) {
      if (event.key === "Escape") {
        escapeRef.current?.();
        return;
      }
      if (event.key !== "Tab") return;
      const focusable = focusableInside(node);
      if (focusable.length === 0) {
        event.preventDefault();
        node.focus?.();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown, true);
    return () => {
      document.removeEventListener("keydown", onKeyDown, true);
      if (previous && typeof previous.focus === "function") previous.focus();
    };
  }, [active]);

  return ref;
}
