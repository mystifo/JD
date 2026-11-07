import { forwardRef, useId } from "react";

import { cx } from "../../utils/cx";

import styles from "./Field.module.css";

export const TextField = forwardRef(function TextField(
  {
    id,
    label,
    hint,
    error,
    required = false,
    maxLength,
    showCounter = false,
    value,
    className,
    ...rest
  },
  ref,
) {
  const generated = useId();
  const inputId = id ?? `field-${generated}`;
  const hintId = `${inputId}-hint`;
  const errorId = `${inputId}-error`;
  const counterId = `${inputId}-counter`;
  const describedBy = [hint ? hintId : null, error ? errorId : null, showCounter && maxLength ? counterId : null]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={cx(styles.field, className)}>
      <div className={styles.labelRow}>
        <label htmlFor={inputId} className={styles.label}>
          {label}
          {required ? (
            <span className={styles.required} aria-hidden="true">
              *
            </span>
          ) : null}
        </label>
        {showCounter && maxLength ? (
          <span id={counterId} className={styles.counter}>
            {String(value ?? "").length}/{maxLength}
          </span>
        ) : null}
      </div>
      <input
        ref={ref}
        id={inputId}
        className={cx(styles.input, error && styles.invalid)}
        aria-invalid={error ? "true" : undefined}
        aria-describedby={describedBy || undefined}
        required={required}
        maxLength={maxLength}
        value={value}
        {...rest}
      />
      {hint ? (
        <p id={hintId} className={styles.hint}>
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={errorId} className={styles.error} role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
});
