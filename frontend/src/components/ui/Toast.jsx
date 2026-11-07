import { cx } from "../../utils/cx";

import styles from "./Toast.module.css";

export function Toast({ message, tone = "success", onDismiss }) {
  return (
    <div className={styles.region} role="status" aria-live="polite" aria-atomic="true">
      {message ? (
        <div className={cx(styles.toast, styles[tone])}>
          <p className={styles.message}>{message}</p>
          {onDismiss ? (
            <button
              type="button"
              className={styles.close}
              onClick={onDismiss}
              aria-label="Dismiss message"
            >
              ×
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
