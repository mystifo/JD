import { NavLink } from "react-router-dom";

import { cx } from "../../utils/cx";

import { primaryNav, settingsNav } from "./navItems";
import styles from "./SidebarNav.module.css";

function NavItem({ item }) {
  const Icon = item.icon;
  return (
    <li>
      <NavLink
        to={item.to}
        end={item.end}
        title={item.label}
        className={({ isActive }) => cx(styles.link, isActive && styles.active)}
      >
        <span className={styles.icon}>
          <Icon />
        </span>
        <span className={styles.label}>{item.label}</span>
      </NavLink>
    </li>
  );
}

export function SidebarNav() {
  return (
    <nav className={styles.sidebar} aria-label="Main">
      <ul className={styles.list}>
        {primaryNav.map((item) => (
          <NavItem key={item.to} item={item} />
        ))}
      </ul>
      <div className={styles.bottom}>
        <ul className={styles.list}>
          <NavItem item={settingsNav} />
        </ul>
      </div>
    </nav>
  );
}
