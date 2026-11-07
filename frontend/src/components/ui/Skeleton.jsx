import { cx } from "../../utils/cx";

import styles from "./Skeleton.module.css";

function SkeletonBlock({ width, height, className }) {
  return (
    <span
      className={cx(styles.block, className)}
      style={{ width: width ?? "100%", height: height ?? "1rem" }}
      aria-hidden="true"
    />
  );
}

export function Skeleton({ variant = "text", lines = 1, width, height, className }) {
  if (variant === "circle") {
    const size = height ?? width ?? "2.5rem";
    return (
      <span
        className={cx(styles.block, styles.circle, className)}
        style={{ width: size, height: size }}
        aria-hidden="true"
      />
    );
  }

  if (variant === "card") {
    return <SkeletonBlock width={width ?? "100%"} height={height ?? "8rem"} className={className} />;
  }

  if (variant === "title") {
    return (
      <SkeletonBlock width={width ?? "40%"} height={height ?? "1.5rem"} className={className} />
    );
  }

  return (
    <span className={cx(styles.stack, className)} aria-hidden="true">
      {Array.from({ length: lines }).map((_, index) => (
        <SkeletonBlock
          key={index}
          width={index === lines - 1 && lines > 1 ? "70%" : (width ?? "100%")}
          height={height ?? "0.875rem"}
        />
      ))}
    </span>
  );
}
