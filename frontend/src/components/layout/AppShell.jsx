import { useState } from "react";

import styles from "./AppShell.module.css";
import { BottomNav } from "./BottomNav";
import { MoreSheet } from "./MoreSheet";
import { SidebarNav } from "./SidebarNav";
import { TopBar } from "./TopBar";

export function AppShell({ children }) {
  const [moreOpen, setMoreOpen] = useState(false);

  return (
    <div className={styles.shell}>
      <a className={styles.skipLink} href="#main">
        Skip to content
      </a>
      <TopBar />
      <SidebarNav />
      <main id="main" tabIndex={-1} className={styles.main}>
        {children}
      </main>
      <BottomNav onOpenMore={() => setMoreOpen(true)} />
      <MoreSheet open={moreOpen} onClose={() => setMoreOpen(false)} />
    </div>
  );
}
