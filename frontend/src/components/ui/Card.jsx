import { cx } from "../../utils/cx";

import styles from "./Card.module.css";

export function Card({ as: Component = "div", tone = "default", className, children, ...rest }) {
  return (
    <Component className={cx(styles.card, styles[tone], className)} {...rest}>
      {children}
    </Component>
  );
}
