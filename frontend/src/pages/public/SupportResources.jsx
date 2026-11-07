import styles from "./public.module.css";

export default function SupportResources() {
  return (
    <article className={styles.page}>
      <h1>Support right now</h1>
      <p className={styles.emergency}>
        If you are in immediate danger, contact your local emergency number now.
      </p>

      <section className={styles.section}>
        <h2>Talk to someone</h2>
        <p>
          These services are independent of HerSpace. Availability and hours can change; check the
          service&apos;s own page before relying on it.
        </p>

        <div className={styles.resources}>
          <div className={styles.resource}>
            <h3>Find a helpline near you</h3>
            <p>An international directory of free, confidential support lines.</p>
            <p>
              <a href="https://findahelpline.com" target="_blank" rel="noreferrer noopener">
                findahelpline.com
              </a>
            </p>
          </div>
          <div className={styles.resource}>
            <h3>United States — 988</h3>
            <p>Suicide &amp; Crisis Lifeline. Call or text 988, any time.</p>
            <p>
              <a href="https://988lifeline.org" target="_blank" rel="noreferrer noopener">
                988lifeline.org
              </a>
            </p>
          </div>
          <div className={styles.resource}>
            <h3>United Kingdom and Ireland — Samaritans</h3>
            <p>Call 116 123, free, any time.</p>
            <p>
              <a href="https://www.samaritans.org" target="_blank" rel="noreferrer noopener">
                samaritans.org
              </a>
            </p>
          </div>
        </div>
      </section>

      <section className={styles.section}>
        <h2>If you are supporting someone</h2>
        <p>
          Listen without fixing. Ask what they need. Keep their privacy, and encourage professional
          help when they want it. HerSpace never shares their content with you unless they choose to.
        </p>
      </section>

      <p className={styles.note}>
        HerSpace is not a crisis service. Local region lists and in-app links arrive in a later
        update.
      </p>
    </article>
  );
}
