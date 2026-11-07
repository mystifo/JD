import styles from "./FullPageSkeleton.module.css";
import { Skeleton } from "./ui/Skeleton";

export function FullPageSkeleton({ label = "Loading your space" }) {
  return (
    <main id="main" tabIndex={-1} className={styles.page} aria-busy="true">
      <p className="visually-hidden" role="status">
        {label}
      </p>
      <div className={styles.inner} aria-hidden="true">
        <Skeleton variant="title" width="12rem" />
        <Skeleton variant="card" height="10rem" />
        <Skeleton variant="card" height="7rem" />
        <Skeleton lines={2} />
      </div>
    </main>
  );
}
