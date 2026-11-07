import { cx } from "../../utils/cx";

import styles from "./InlineAlert.module.css";

const SYMBOLS = {
  info: "i",
  success: "✓",
  warning: "!",
  error: "!",
};

export function InlineAlert({ tone = "info", title, children, action, className }) {
  return (
    <div
      className={cx(styles.alert, styles[tone], className)}
      role={tone === "error" ? "alert" : "status"}
    >
      <span className={styles.symbol} aria-hidden="true">
        {SYMBOLS[tone] ?? SYMBOLS.info}
      </span>
      <div className={styles.content}>
        {title ? <p className={styles.title}>{title}</p> : null}
        {children ? <div className={styles.body}>{children}</div> : null}
        {action ? <div className={styles.action}>{action}</div> : null}
      </div>
    </div>
  );
}
