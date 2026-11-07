import { Link } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { useSession } from "../../hooks/useSession";

import styles from "./Welcome.module.css";

export default function Welcome() {
  const { status } = useSession();
  const authenticated = status === "authenticated";

  return (
    <div className={styles.wrap}>
      <section className={styles.hero}>
        <p className={styles.eyebrow}>Private by design</p>
        <h1 className={styles.title}>A private space for how you actually feel.</h1>
        <p className={styles.lede}>
          Check in with yourself. Write what&apos;s true. Reach the people who know you.
        </p>

        <div className={styles.actions}>
          {authenticated ? (
            <Button as={Link} to="/app" size="lg">
              Open your space
            </Button>
          ) : (
            <>
              <Button as={Link} to="/register" size="lg">
                Create your space
              </Button>
              <Button as={Link} to="/login" size="lg" variant="secondary">
                I already have one
              </Button>
            </>
          )}
        </div>

        <p className={styles.promise}>no feeds, no strangers, no AI companion</p>
      </section>
    </div>
  );
}
