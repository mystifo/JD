import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";

import { ArrowLeftIcon } from "../components/icons";
import { Button } from "../components/ui/Button";
import { useSession } from "../hooks/useSession";
import { VerificationGate } from "../pages/auth/VerificationGate";

import styles from "./OnboardingLayout.module.css";

const steps = ["profile", "wellness", "notifications", "people", "privacy"];

export function OnboardingLayout() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { user } = useSession();
  const index = Math.max(
    0,
    steps.findIndex((step) => pathname === `/onboarding/${step}`),
  );
  const isLast = index === steps.length - 1;

  if (!user?.emailVerified) {
    return (
      <main id="main" tabIndex={-1} className={styles.page}>
        <div className={styles.shell}>
          <Link to="/" className={styles.brand}>
            HerSpace
          </Link>
          <VerificationGate />
        </div>
      </main>
    );
  }

  return (
    <main id="main" tabIndex={-1} className={styles.page}>
      <div className={styles.shell}>
        <Link to="/" className={styles.brand}>
          HerSpace
        </Link>

        <div className={styles.progress}>
          <p className={styles.stepText}>
            Step {index + 1} of {steps.length}
          </p>
          <ol className={styles.dots} aria-hidden="true">
            {steps.map((step, dotIndex) => (
              <li
                key={step}
                className={dotIndex <= index ? styles.dotActive : styles.dot}
              />
            ))}
          </ol>
        </div>

        <Outlet />

        <div className={styles.nav}>
          {index > 0 ? (
            <Button
              variant="ghost"
              iconLeft={<ArrowLeftIcon width="18" height="18" />}
              onClick={() => navigate(`/onboarding/${steps[index - 1]}`)}
            >
              Back
            </Button>
          ) : (
            <span />
          )}
          {!isLast ? (
            <Button variant="ghost" onClick={() => navigate(`/onboarding/${steps[index + 1]}`)}>
              Skip for now
            </Button>
          ) : null}
        </div>
      </div>
    </main>
  );
}
