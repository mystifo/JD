import { useSyncExternalStore } from "react";

function subscribe(query, callback) {
  if (typeof window === "undefined" || !window.matchMedia) return () => {};
  const media = window.matchMedia(query);
  media.addEventListener("change", callback);
  return () => media.removeEventListener("change", callback);
}

export function useMediaQuery(query) {
  const getSnapshot = () => {
    if (typeof window === "undefined" || !window.matchMedia) return false;
    return window.matchMedia(query).matches;
  };

  return useSyncExternalStore(
    (callback) => subscribe(query, callback),
    getSnapshot,
    () => false,
  );
}
