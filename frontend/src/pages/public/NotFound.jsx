import { Link } from "react-router-dom";

import styles from "./public.module.css";

export default function NotFound() {
  return (
    <article className={styles.page}>
      <h1>This page isn&apos;t here</h1>
      <p className={styles.meta}>
        It may have been removed, or the link may be old.
      </p>
      <section className={styles.section}>
        <p>
          Try <Link to="/app">Today</Link>, <Link to="/app/journal">Journal</Link>, or{" "}
          <Link to="/support-resources">Support resources</Link>.
        </p>
      </section>
    </article>
  );
}
