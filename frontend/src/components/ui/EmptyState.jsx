import { cx } from "../../utils/cx";

import styles from "./EmptyState.module.css";

export function EmptyState({ title, body, action, icon, className }) {
  return (
    <div className={cx(styles.empty, className)}>
      {icon ? (
        <span className={styles.icon} aria-hidden="true">
          {icon}
        </span>
      ) : null}
      <h2 className={styles.title}>{title}</h2>
      {body ? <p className={styles.body}>{body}</p> : null}
      {action ? <div className={styles.action}>{action}</div> : null}
    </div>
  );
}
