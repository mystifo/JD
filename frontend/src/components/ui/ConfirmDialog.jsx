import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { useFocusTrap } from "../../hooks/useFocusTrap";

import { Button } from "./Button";
import styles from "./ConfirmDialog.module.css";

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  requireText,
  onConfirm,
  onCancel,
  tone = "danger",
}) {
  const titleId = useId();
  const descriptionId = useId();
  const inputId = useId();
  const cancelRef = useRef(null);
  const [text, setText] = useState("");

  const trapRef = useFocusTrap(open, { onEscape: onCancel, initialFocus: cancelRef });

  useEffect(() => {
    if (!open) return undefined;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [open]);

  useEffect(() => {
    if (!open) setText("");
  }, [open]);

  if (!open) return null;

  const textMatches = !requireText || text === requireText;

  return createPortal(
    <div className={styles.overlay}>
      <div
        ref={trapRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descriptionId : undefined}
        className={styles.dialog}
      >
        <h2 id={titleId} className={styles.title}>
          {title}
        </h2>
        {description ? (
          <p id={descriptionId} className={styles.description}>
            {description}
          </p>
        ) : null}
        {requireText ? (
          <div className={styles.confirmField}>
            <label htmlFor={inputId} className={styles.confirmLabel}>
              Type <strong>{requireText}</strong> to confirm
            </label>
            <input
              id={inputId}
              className={styles.input}
              type="text"
              value={text}
              onChange={(event) => setText(event.target.value)}
              autoComplete="off"
            />
          </div>
        ) : null}
        <div className={styles.actions}>
          <Button ref={cancelRef} variant="secondary" onClick={onCancel}>
            {cancelLabel}
          </Button>
          <Button
            variant={tone === "danger" ? "danger" : "primary"}
            onClick={onConfirm}
            disabled={!textMatches}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
