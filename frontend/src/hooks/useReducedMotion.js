import { useTheme } from "./useTheme";

/** Effective motion preference: the operating system setting or the account setting. */
export function useReducedMotion() {
  const { reducedMotion } = useTheme();
  return reducedMotion;
}
