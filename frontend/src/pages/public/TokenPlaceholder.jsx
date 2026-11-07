import { Link } from "react-router-dom";

import styles from "./public.module.css";

export default function TokenPlaceholder() {
  return (
    <article className={styles.page}>
      <h1>This link isn&apos;t active yet</h1>
      <p className={styles.meta}>Invitations and support responses arrive in a later update.</p>
      <section className={styles.section}>
        <p>
          If someone sent you this link, ask them to send it again once the feature is available.
          Nothing has been shared with you or by you.
        </p>
        <p>
          <Link to="/">Back to HerSpace</Link>
        </p>
      </section>
    </article>
  );
}
