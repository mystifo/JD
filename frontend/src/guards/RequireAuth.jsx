import { Navigate, Outlet, useLocation } from "react-router-dom";

import { FullPageSkeleton } from "../components/FullPageSkeleton";
import { Button } from "../components/ui/Button";
import { InlineAlert } from "../components/ui/InlineAlert";
import { useSession } from "../hooks/useSession";

import styles from "./RequireAuth.module.css";

export function RequireAuth() {
  const { status, onboardingRequired, deletionScheduledFor, error, refresh } = useSession();
  const location = useLocation();

  if (status === "loading") return <FullPageSkeleton />;

  if (status === "error") {
    return (
      <main id="main" tabIndex={-1} className={styles.page}>
        <InlineAlert
          tone="error"
          title="We couldn't load your space"
          action={<Button onClick={() => refresh()}>Try again</Button>}
        >
          {error?.message ?? "Check your connection and try again."}
        </InlineAlert>
      </main>
    );
  }

  if (status === "anonymous") {
    const next = `${location.pathname}${location.search}`;
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace />;
  }

  const onDeleteStatus = location.pathname === "/app/settings/delete";
  if (deletionScheduledFor && !onDeleteStatus) {
    return <Navigate to="/app/settings/delete" replace />;
  }

  const inOnboarding = location.pathname.startsWith("/onboarding");
  if (onboardingRequired && !inOnboarding) {
    return <Navigate to="/onboarding/profile" replace />;
  }
  if (!onboardingRequired && inOnboarding) {
    return <Navigate to="/app" replace />;
  }

  return <Outlet />;
}
