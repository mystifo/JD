import { NavLink } from "react-router-dom";

import { cx } from "../../utils/cx";
import { MoreIcon } from "../icons";

import styles from "./BottomNav.module.css";
import { bottomNav } from "./navItems";

export function BottomNav({ onOpenMore }) {
  return (
    <nav className={styles.nav} aria-label="Main">
      <ul className={styles.list}>
        {bottomNav.map((item) => {
          const Icon = item.icon;
          return (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) => cx(styles.link, isActive && styles.active)}
              >
                <Icon width="22" height="22" />
                <span>{item.label}</span>
              </NavLink>
            </li>
          );
        })}
        <li>
          <button
            type="button"
            className={styles.link}
            onClick={onOpenMore}
            aria-haspopup="dialog"
          >
            <MoreIcon width="22" height="22" />
            <span>More</span>
          </button>
        </li>
      </ul>
    </nav>
  );
}
