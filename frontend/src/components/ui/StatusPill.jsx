import { cx } from "../../utils/cx";

import styles from "./StatusPill.module.css";

const LABELS = {
  pending: "Pending",
  active: "Active",
  accepted: "Accepted",
  declined: "Declined",
  expired: "Expired",
  revoked: "Revoked",
  unavailable: "Unavailable",
  sent: "Sent",
  opened: "Opened",
  draft: "Draft",
  scheduled: "Scheduled",
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
  completed: "Completed",
  cancelled: "Cancelled",
  verified: "Verified",
  unverified: "Not verified",
};

const TONES = {
  active: "success",
  accepted: "success",
  ready: "success",
  completed: "success",
  verified: "success",
  pending: "warning",
  processing: "warning",
  scheduled: "warning",
  opened: "warning",
  sent: "warning",
  declined: "danger",
  revoked: "danger",
  failed: "danger",
  expired: "danger",
  unavailable: "danger",
  cancelled: "danger",
  unverified: "danger",
};

export function StatusPill({ status, label, className }) {
  const key = String(status ?? "").toLowerCase();
  const text = label ?? LABELS[key] ?? key ?? "";
  return (
    <span className={cx(styles.pill, styles[TONES[key] ?? "neutral"], className)}>
      <span className={styles.dot} aria-hidden="true" />
      {text}
    </span>
  );
}
