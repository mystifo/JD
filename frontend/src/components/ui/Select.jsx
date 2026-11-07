import { forwardRef, useId } from "react";

import { cx } from "../../utils/cx";

import styles from "./Field.module.css";

export const Select = forwardRef(function Select(
  { id, label, hint, error, required = false, options = [], placeholder, className, ...rest },
  ref,
) {
  const generated = useId();
  const inputId = id ?? `field-${generated}`;
  const hintId = `${inputId}-hint`;
  const errorId = `${inputId}-error`;
  const describedBy = [hint ? hintId : null, error ? errorId : null].filter(Boolean).join(" ");

  return (
    <div className={cx(styles.field, className)}>
      <label htmlFor={inputId} className={styles.label}>
        {label}
        {required ? (
          <span className={styles.required} aria-hidden="true">
            *
          </span>
        ) : null}
      </label>
      <select
        ref={ref}
        id={inputId}
        className={cx(styles.input, styles.select, error && styles.invalid)}
        aria-invalid={error ? "true" : undefined}
        aria-describedby={describedBy || undefined}
        required={required}
        {...rest}
      >
        {placeholder ? <option value="">{placeholder}</option> : null}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
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
