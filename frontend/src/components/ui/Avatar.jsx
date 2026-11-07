import { cx } from "../../utils/cx";

import styles from "./Avatar.module.css";

function initialsFor(name) {
  const parts = String(name ?? "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!parts.length) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

export function Avatar({ name, size = "md", label, className }) {
  return (
    <span
      className={cx(styles.avatar, styles[size], className)}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : "true"}
    >
      {initialsFor(name)}
    </span>
  );
}
