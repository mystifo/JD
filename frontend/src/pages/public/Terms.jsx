import styles from "./public.module.css";

export default function Terms() {
  return (
    <article className={styles.page}>
      <h1>Terms of Service</h1>
      <p className={styles.meta}>Version 1.0 · Effective 31 October 2026</p>

      <section className={styles.section}>
        <h2>Using HerSpace</h2>
        <p>
          HerSpace is a personal wellbeing space for adults and teenagers aged 13 or older. You are
          responsible for the content you add and for keeping your sign-in details private.
        </p>
      </section>

      <section className={styles.section}>
        <h2>Not a medical service</h2>
        <p>
          HerSpace does not diagnose, treat, or monitor a health condition. It is not a crisis
          service and is not a replacement for professional care. If you are in immediate danger,
          contact your local emergency number.
        </p>
      </section>

      <section className={styles.section}>
        <h2>Your content</h2>
        <p>
          You keep ownership of what you write. You grant HerSpace only the permission needed to
          store, display, export, and delete it on your instruction. Nothing is shared automatically.
        </p>
      </section>

      <section className={styles.section}>
        <h2>Support requests</h2>
        <p>
          Support requests are sent to people you choose. Their responses are personal and are not
          verified by HerSpace. A request expires automatically, and you can withdraw a share.
        </p>
      </section>

      <section className={styles.section}>
        <h2>Account deletion</h2>
        <p>
          When account deletion ships, it will start a 7-day cancellable grace period. After that,
          your content and account are removed, subject to the short audit retention described in the
          Privacy Policy.
        </p>
      </section>

      <section className={styles.section}>
        <h2>Changes</h2>
        <p>
          If these terms change in a way that affects your choices, HerSpace will ask you to review
          the new version before continuing.
        </p>
      </section>
    </article>
  );
}
