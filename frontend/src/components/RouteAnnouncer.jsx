import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";

import { routeTitle } from "../utils/routeTitle";

import styles from "./RouteAnnouncer.module.css";

export function RouteAnnouncer() {
  const { pathname } = useLocation();
  const [announcement, setAnnouncement] = useState("");
  const first = useRef(true);

  useEffect(() => {
    const title = routeTitle(pathname);
    document.title = `${title} · HerSpace`;
    setAnnouncement(title);

    if (first.current) {
      first.current = false;
      return;
    }

    const main = document.getElementById("main");
    main?.focus?.({ preventScroll: true });
    window.scrollTo(0, 0);
  }, [pathname]);

  return (
    <div className={styles.region} aria-live="polite" aria-atomic="true">
      {announcement}
    </div>
  );
}
