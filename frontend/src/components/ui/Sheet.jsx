import { useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";

import { useFocusTrap } from "../../hooks/useFocusTrap";
import { cx } from "../../utils/cx";

import styles from "./Sheet.module.css";

export function Sheet({ open, onClose, title, children, footer, className }) {
  const titleId = useId();
  const closeRef = useRef(null);
  const trapRef = useFocusTrap(open, { onEscape: onClose, initialFocus: closeRef });

  useEffect(() => {
    if (!open) return undefined;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [open]);

  if (!open) return null;

  return createPortal(
    <div className={styles.overlay}>
      <div
        ref={trapRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className={cx(styles.sheet, className)}
      >
        <span className={styles.handle} aria-hidden="true" />
        <div className={styles.header}>
          <h2 id={titleId} className={styles.title}>
            {title}
          </h2>
          <button
            ref={closeRef}
            type="button"
            className={styles.close}
            onClick={onClose}
            aria-label="Close"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
              <path
                d="M6 6l12 12M18 6L6 18"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>
        <div className={styles.body}>{children}</div>
        {footer ? <div className={styles.footer}>{footer}</div> : null}
      </div>
    </div>,
    document.body,
  );
}
