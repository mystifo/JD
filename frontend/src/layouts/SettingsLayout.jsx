import { NavLink, Outlet } from "react-router-dom";

import { cx } from "../utils/cx";

import styles from "./SettingsLayout.module.css";

const links = [
  { to: "/app/settings/profile", label: "Profile" },
  { to: "/app/settings/security", label: "Security" },
  { to: "/app/settings/privacy", label: "Privacy" },
  { to: "/app/settings/notifications", label: "Notifications" },
  { to: "/app/settings/data", label: "Your data" },
  { to: "/app/settings/delete", label: "Delete account", danger: true },
];

export function SettingsLayout() {
  return (
    <div className={styles.layout}>
      <nav aria-label="Settings" className={styles.nav}>
        <ul className={styles.list}>
          {links.map((link) => (
            <li key={link.to}>
              <NavLink
                to={link.to}
                className={({ isActive }) =>
                  cx(styles.link, isActive && styles.active, link.danger && styles.danger)
                }
              >
                {link.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <div className={styles.panel}>
        <Outlet />
      </div>
    </div>
  );
}
