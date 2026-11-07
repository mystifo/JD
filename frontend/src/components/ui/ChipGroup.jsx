import { useId, useRef, useState } from "react";

import { cx } from "../../utils/cx";

import styles from "./ChipGroup.module.css";

function normaliseOptions(options) {
  return options.map((option) =>
    typeof option === "string" ? { value: option, label: option } : option,
  );
}

function toSelectedArray(value, multiple) {
  if (multiple) return Array.isArray(value) ? value : value === "" || value == null ? [] : [value];
  return value === "" || value == null ? [] : [value];
}

export function ChipGroup({
  label,
  options = [],
  value,
  onChange,
  multiple = false,
  max,
  hint,
  className,
}) {
  const groupId = useId();
  const hintId = hint ? `${groupId}-hint` : undefined;
  const items = normaliseOptions(options);
  const selected = toSelectedArray(value, multiple);
  const atMax = typeof max === "number" && selected.length >= max;
  const refs = useRef([]);
  const [focusIndex, setFocusIndex] = useState(0);

  const isEnabled = (index) => {
    const option = items[index];
    if (!option) return false;
    return selected.includes(option.value) || !atMax;
  };

  const firstEnabled = () => {
    const found = items.findIndex((_, index) => isEnabled(index));
    return found === -1 ? 0 : found;
  };

  const tabStop = isEnabled(focusIndex) ? focusIndex : firstEnabled();

  function moveFocus(index, direction) {
    if (!items.length) return;
    let next = index;
    for (let step = 0; step < items.length; step += 1) {
      next = (next + direction + items.length) % items.length;
      if (isEnabled(next)) {
        setFocusIndex(next);
        refs.current[next]?.focus();
        return;
      }
    }
  }

  function onKeyDown(event) {
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault();
      moveFocus(tabStop, 1);
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault();
      moveFocus(tabStop, -1);
    } else if (event.key === "Home") {
      event.preventDefault();
      const index = firstEnabled();
      setFocusIndex(index);
      refs.current[index]?.focus();
    } else if (event.key === "End") {
      event.preventDefault();
      let index = items.length - 1;
      while (index > 0 && !isEnabled(index)) index -= 1;
      setFocusIndex(index);
      refs.current[index]?.focus();
    }
  }

  function toggle(option) {
    if (multiple) {
      if (selected.includes(option.value)) {
        onChange?.(selected.filter((item) => item !== option.value));
      } else if (!atMax) {
        onChange?.([...selected, option.value]);
      }
      return;
    }
    onChange?.(selected.includes(option.value) ? "" : option.value);
  }

  return (
    <fieldset className={cx(styles.group, className)} aria-describedby={hintId}>
      <legend className={styles.legend}>{label}</legend>
      <div className={styles.options}>
        {items.map((option, index) => {
          const isOn = selected.includes(option.value);
          const enabled = isOn || !atMax;
          return (
            <button
              key={option.value}
              ref={(node) => {
                refs.current[index] = node;
              }}
              type="button"
              className={cx(styles.chip, isOn && styles.on)}
              aria-pressed={isOn}
              disabled={!enabled}
              tabIndex={enabled && index === tabStop ? 0 : -1}
              onFocus={() => setFocusIndex(index)}
              onKeyDown={onKeyDown}
              onClick={() => toggle(option)}
            >
              {option.label}
            </button>
          );
        })}
      </div>
      {hint ? (
        <p id={hintId} className={styles.hint}>
          {hint}
        </p>
      ) : null}
      {multiple && typeof max === "number" ? (
        <p className={styles.counter} aria-live="polite">
          {selected.length} of {max} selected
        </p>
      ) : null}
    </fieldset>
  );
}
