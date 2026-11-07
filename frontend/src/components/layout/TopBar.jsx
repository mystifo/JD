import { useRef } from "react";
import { NavLink, useNavigate } from "react-router-dom";

import { useSession } from "../../hooks/useSession";
import { LogOutIcon } from "../icons";
import { BellIcon } from "../icons";
import { Avatar } from "../ui/Avatar";

import styles from "./TopBar.module.css";

export function TopBar() {
  const { user, signOut } = useSession();
  const navigate = useNavigate();
  const menuRef = useRef(null);

  function closeMenu() {
    if (menuRef.current) menuRef.current.open = false;
  }

  async function onLogout() {
    closeMenu();
    await signOut();
    navigate("/", { replace: true });
  }

  return (
    <header className={styles.topbar}>
      <NavLink to="/app" className={styles.brand} onClick={closeMenu}>
        <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
          <rect width="32" height="32" rx="9" fill="var(--accent)" />
          <path
            d="M16 9c-3.2 0-5.5 2.2-5.5 5.4 0 4 4.1 6.9 5.5 8.6 1.4-1.7 5.5-4.6 5.5-8.6C21.5 11.2 19.2 9 16 9Z"
            fill="var(--accent-contrast)"
          />
        </svg>
        <span className={styles.brandName}>HerSpace</span>
      </NavLink>

      <div className={styles.actions}>
        <NavLink to="/app/notifications" className={styles.iconButton} aria-label="Notifications">
          <BellIcon />
        </NavLink>

        <details className={styles.menu} ref={menuRef}>
          <summary className={styles.summary}>
            <Avatar name={user?.displayName} size="sm" />
            <span className="visually-hidden">Account menu</span>
          </summary>
          <div className={styles.dropdown}>
            <p className={styles.account}>
              <span className={styles.accountName}>{user?.displayName}</span>
              <span className={styles.accountEmail}>{user?.email}</span>
            </p>
            <NavLink to="/app/settings/profile" className={styles.menuLink} onClick={closeMenu}>
              Profile
            </NavLink>
            <NavLink to="/app/settings" className={styles.menuLink} onClick={closeMenu}>
              Settings
            </NavLink>
            <button type="button" className={styles.menuLink} onClick={onLogout}>
              <LogOutIcon width="18" height="18" />
              Log out
            </button>
          </div>
        </details>
      </div>
    </header>
  );
}
