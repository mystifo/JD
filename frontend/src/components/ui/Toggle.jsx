import { useId } from "react";

import { cx } from "../../utils/cx";

import styles from "./Toggle.module.css";

export function Toggle({
  label,
  description,
  checked = false,
  onChange,
  disabled = false,
  className,
}) {
  const id = useId();
  const descriptionId = description ? `${id}-description` : undefined;

  return (
    <label className={cx(styles.row, disabled && styles.disabled, className)}>
      <span className={styles.text}>
        <span className={styles.label}>{label}</span>
        {description ? (
          <span id={descriptionId} className={styles.description}>
            {description}
          </span>
        ) : null}
      </span>
      <span className={styles.control}>
        <input
          type="checkbox"
          role="switch"
          className={styles.input}
          checked={checked}
          onChange={(event) => onChange?.(event.target.checked)}
          disabled={disabled}
          aria-describedby={descriptionId}
        />
        <span className={styles.track} aria-hidden="true">
          <span className={styles.thumb} />
        </span>
      </span>
    </label>
  );
}
