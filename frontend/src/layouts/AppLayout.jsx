import { Outlet } from "react-router-dom";

import { ErrorBoundary } from "../components/ErrorBoundary";
import { AppShell } from "../components/layout/AppShell";
import { VerificationBanner } from "../components/layout/VerificationBanner";

import styles from "./AppLayout.module.css";

export function AppLayout() {
  return (
    <AppShell>
      <div className={styles.content}>
        <VerificationBanner />
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </div>
    </AppShell>
  );
}
