import { NavLink, useNavigate } from "react-router-dom";

import { useSession } from "../../hooks/useSession";
import { LogOutIcon } from "../icons";
import { Sheet } from "../ui/Sheet";

import styles from "./MoreSheet.module.css";
import { moreNav } from "./navItems";

export function MoreSheet({ open, onClose }) {
  const { signOut } = useSession();
  const navigate = useNavigate();

  async function onLogout() {
    onClose();
    await signOut();
    navigate("/", { replace: true });
  }

  return (
    <Sheet open={open} onClose={onClose} title="More">
      <ul className={styles.list}>
        {moreNav.map((item) => {
          const Icon = item.icon;
          return (
            <li key={item.to}>
              <NavLink to={item.to} className={styles.link} onClick={onClose}>
                <Icon />
                <span>{item.label}</span>
              </NavLink>
            </li>
          );
        })}
        <li>
          <NavLink to="/support-resources" className={styles.link} onClick={onClose}>
            <span className={styles.placeholder} aria-hidden="true" />
            <span>Support resources</span>
          </NavLink>
        </li>
        <li>
          <button type="button" className={styles.link} onClick={onLogout}>
            <LogOutIcon />
            <span>Log out</span>
          </button>
        </li>
      </ul>
    </Sheet>
  );
}
