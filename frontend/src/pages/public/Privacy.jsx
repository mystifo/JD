import styles from "./public.module.css";

export default function Privacy() {
  return (
    <article className={styles.page}>
      <h1>Privacy</h1>
      <p className={styles.meta}>Version 1.0 · Effective 31 October 2026</p>

      <section className={styles.section}>
        <h2>The short version</h2>
        <p>
          HerSpace is a private space for how you actually feel. It has no feeds, no strangers, no
          advertising, and no AI companion. Your journal and moods are yours.
        </p>
      </section>

      <section className={styles.section}>
        <h2>What we store</h2>
        <ul>
          <li>Account details you provide: email, display name, timezone, and optional profile fields.</li>
          <li>Content you choose to add: mood check-ins, journal entries, routines, and calm sessions.</li>
          <li>People you choose to add and the support requests you send.</li>
          <li>Consent records, security events, and audit entries needed to keep the service safe.</li>
        </ul>
      </section>

      <section className={styles.section}>
        <h2>What we never do</h2>
        <ul>
          <li>No private content in logs, notifications, or emails.</li>
          <li>No sharing with anyone unless you choose a snapshot to share in a support request.</li>
          <li>No sale of personal data and no third-party analytics SDKs.</li>
          <li>No diagnosis, and no replacement for professional care.</li>
        </ul>
      </section>

      <section className={styles.section}>
        <h2>Sharing and consent</h2>
        <p>
          A support request shares only the items you tick, once, as an immutable snapshot. You can
          withdraw a share; the other person sees that it was withdrawn, not its content. Email
          notification choices are recorded as consent and can be changed at any time.
        </p>
      </section>

      <section className={styles.section}>
        <h2>Retention</h2>
        <ul>
          <li>Journal entries are hard-deleted when you delete them.</li>
          <li>Audit records are kept for 180 days, or 90 days after account deletion.</li>
          <li>Account deletion has a 7-day cancellable grace period.</li>
          <li>Export files are available for 7 days, then removed.</li>
        </ul>
      </section>

      <section className={styles.section}>
        <h2>Your controls</h2>
        <p>
          You can export or delete everything from Settings when those controls ship. You can also
          review and withdraw consent. If you have a question, contact the person who operates this
          HerSpace instance.
        </p>
      </section>
    </article>
  );
}
