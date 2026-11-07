import { forwardRef } from "react";

import { cx } from "../../utils/cx";

import styles from "./Button.module.css";

export const Button = forwardRef(function Button(
  {
    as: Component = "button",
    variant = "primary",
    size = "md",
    loading = false,
    disabled = false,
    iconLeft,
    iconRight,
    fullWidth = false,
    className,
    children,
    type = "button",
    ...rest
  },
  ref,
) {
  const isButton = Component === "button";
  return (
    <Component
      ref={ref}
      {...(isButton ? { type, disabled: disabled || loading } : {})}
      aria-disabled={!isButton && (disabled || loading) ? "true" : undefined}
      className={cx(
        styles.button,
        styles[variant],
        styles[size],
        fullWidth && styles.fullWidth,
        className,
      )}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <span className={styles.spinner} aria-hidden="true" /> : null}
      {iconLeft ? (
        <span className={styles.icon} aria-hidden="true">
          {iconLeft}
        </span>
      ) : null}
      <span>{children}</span>
      {iconRight ? (
        <span className={styles.icon} aria-hidden="true">
          {iconRight}
        </span>
      ) : null}
    </Component>
  );
});
