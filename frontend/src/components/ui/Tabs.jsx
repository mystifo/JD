import { useId, useRef, useState } from "react";

import { cx } from "../../utils/cx";

import styles from "./Tabs.module.css";

export function Tabs({ tabs = [], value, onChange, label }) {
  const baseId = useId();
  const [internal, setInternal] = useState(tabs[0]?.value ?? "");
  const selected = value ?? internal;
  const active = tabs.find((tab) => tab.value === selected) ?? tabs[0];
  const refs = useRef([]);

  if (!tabs.length) return null;

  function select(next) {
    if (value === undefined) setInternal(next);
    onChange?.(next);
  }

  function onKeyDown(event, index) {
    let nextIndex = null;
    if (event.key === "ArrowRight") nextIndex = (index + 1) % tabs.length;
    else if (event.key === "ArrowLeft") nextIndex = (index - 1 + tabs.length) % tabs.length;
    else if (event.key === "Home") nextIndex = 0;
    else if (event.key === "End") nextIndex = tabs.length - 1;
    if (nextIndex === null) return;
    event.preventDefault();
    select(tabs[nextIndex].value);
    refs.current[nextIndex]?.focus();
  }

  return (
    <div className={styles.tabs}>
      <div role="tablist" aria-label={label} className={styles.list}>
        {tabs.map((tab, index) => {
          const isSelected = tab.value === active?.value;
          return (
            <button
              key={tab.value}
              ref={(node) => {
                refs.current[index] = node;
              }}
              type="button"
              role="tab"
              id={`${baseId}-tab-${index}`}
              aria-selected={isSelected}
              aria-controls={`${baseId}-panel-${index}`}
              tabIndex={isSelected ? 0 : -1}
              className={cx(styles.tab, isSelected && styles.selected)}
              onClick={() => select(tab.value)}
              onKeyDown={(event) => onKeyDown(event, index)}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
      {active ? (
        <div
          role="tabpanel"
          id={`${baseId}-panel-${tabs.indexOf(active)}`}
          aria-labelledby={`${baseId}-tab-${tabs.indexOf(active)}`}
          tabIndex={0}
          className={styles.panel}
        >
          {active.panel}
        </div>
      ) : null}
    </div>
  );
}
