import { Link, NavLink, Outlet } from "react-router-dom";

import { ErrorBoundary } from "../components/ErrorBoundary";
import { useSession } from "../hooks/useSession";

import styles from "./PublicLayout.module.css";

export function PublicLayout() {
  const { status } = useSession();
  const authenticated = status === "authenticated";

  return (
    <div className={styles.page}>
      <a className={styles.skipLink} href="#main">
        Skip to content
      </a>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <Link to="/" className={styles.brand}>
            <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
              <rect width="32" height="32" rx="9" fill="var(--accent)" />
              <path
                d="M16 9c-3.2 0-5.5 2.2-5.5 5.4 0 4 4.1 6.9 5.5 8.6 1.4-1.7 5.5-4.6 5.5-8.6C21.5 11.2 19.2 9 16 9Z"
                fill="var(--accent-contrast)"
              />
            </svg>
            <span>HerSpace</span>
          </Link>
          <nav aria-label="Account">
            {authenticated ? (
              <NavLink to="/app" className={styles.navLink}>
                Open HerSpace
              </NavLink>
            ) : (
              <NavLink to="/login" className={styles.navLink}>
                Log in
              </NavLink>
            )}
          </nav>
        </div>
      </header>

      <main id="main" tabIndex={-1} className={styles.main}>
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </main>

      <footer className={styles.footer}>
        <nav aria-label="HerSpace information">
          <ul className={styles.footerLinks}>
            <li>
              <Link to="/privacy">Privacy</Link>
            </li>
            <li>
              <Link to="/terms">Terms</Link>
            </li>
            <li>
              <Link to="/support-resources">Support resources</Link>
            </li>
          </ul>
        </nav>
        <p className={styles.footerNote}>No feeds, no strangers, no AI companion.</p>
      </footer>
    </div>
  );
}
