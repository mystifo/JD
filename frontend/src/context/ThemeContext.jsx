import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useMediaQuery } from "../hooks/useMediaQuery";
import { useSession } from "../hooks/useSession";
import { useToast } from "../hooks/useToast";
import { profileApi } from "../services/profile";
import { qk } from "../services/queryKeys";

export const ThemeContext = createContext(null);

const STORAGE_THEME = "hs-theme";
const STORAGE_MOTION = "hs-reduced-motion";
const SAVE_DELAY = 400;

function readStoredTheme() {
  try {
    const stored = localStorage.getItem(STORAGE_THEME);
    return ["system", "light", "dark"].includes(stored) ? stored : "system";
  } catch {
    return "system";
  }
}

function persist(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Storage can be unavailable (private mode); the in-memory value still works.
  }
}

export function ThemeProvider({ children }) {
  const { preferences, status } = useSession();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const systemDark = useMediaQuery("(prefers-color-scheme: dark)");
  const systemReduced = useMediaQuery("(prefers-reduced-motion: reduce)");

  const [theme, setThemeState] = useState(readStoredTheme);
  const [motionPreference, setMotionPreference] = useState(false);
  const themeTimer = useRef(null);
  const motionTimer = useRef(null);

  const serverTheme = preferences?.theme ?? "system";
  const serverMotion = Boolean(preferences?.reducedMotion);

  useEffect(() => {
    setThemeState(serverTheme);
    persist(STORAGE_THEME, serverTheme);
  }, [serverTheme]);

  useEffect(() => {
    setMotionPreference(serverMotion);
    persist(STORAGE_MOTION, String(serverMotion));
  }, [serverMotion]);

  const resolvedTheme = theme === "system" ? (systemDark ? "dark" : "light") : theme;

  useEffect(() => {
    document.documentElement.dataset.theme = resolvedTheme;
    document.documentElement.style.colorScheme = resolvedTheme;
  }, [resolvedTheme]);

  const reducedMotion = motionPreference || systemReduced;

  useEffect(() => {
    document.documentElement.dataset.reducedMotion = String(reducedMotion);
  }, [reducedMotion]);

  const writeSessionPreference = useCallback(
    (field, value) => {
      queryClient.setQueryData(qk.session, (current) => {
        if (!current || current.status !== "authenticated") return current;
        return {
          ...current,
          preferences: { ...current.preferences, [field]: value },
        };
      });
    },
    [queryClient],
  );

  const saveTheme = useCallback(
    (next) => {
      if (themeTimer.current) window.clearTimeout(themeTimer.current);
      themeTimer.current = window.setTimeout(async () => {
        try {
          const saved = await profileApi.updatePreferences({ theme: next });
          writeSessionPreference("theme", saved.theme);
        } catch {
          const fallback = preferences?.theme ?? "system";
          setThemeState(fallback);
          persist(STORAGE_THEME, fallback);
          showToast("We couldn't save your theme preference.", { tone: "error" });
        }
      }, SAVE_DELAY);
    },
    [preferences?.theme, showToast, writeSessionPreference],
  );

  const saveMotion = useCallback(
    (next) => {
      if (motionTimer.current) window.clearTimeout(motionTimer.current);
      motionTimer.current = window.setTimeout(async () => {
        try {
          const saved = await profileApi.updatePreferences({ reducedMotion: next });
          writeSessionPreference("reducedMotion", saved.reducedMotion);
        } catch {
          setMotionPreference(serverMotion);
          persist(STORAGE_MOTION, String(serverMotion));
          showToast("We couldn't save your motion preference.", { tone: "error" });
        }
      }, SAVE_DELAY);
    },
    [serverMotion, showToast, writeSessionPreference],
  );

  const setTheme = useCallback(
    (next) => {
      if (!["system", "light", "dark"].includes(next)) return;
      setThemeState(next);
      persist(STORAGE_THEME, next);
      if (status === "authenticated") saveTheme(next);
    },
    [saveTheme, status],
  );

  const setReducedMotion = useCallback(
    (next) => {
      setMotionPreference(Boolean(next));
      persist(STORAGE_MOTION, String(Boolean(next)));
      if (status === "authenticated") saveMotion(Boolean(next));
    },
    [saveMotion, status],
  );

  useEffect(() => {
    return () => {
      if (themeTimer.current) window.clearTimeout(themeTimer.current);
      if (motionTimer.current) window.clearTimeout(motionTimer.current);
    };
  }, []);

  const value = useMemo(
    () => ({
      theme,
      resolvedTheme,
      reducedMotion,
      reducedMotionPreference: motionPreference,
      setTheme,
      setReducedMotion,
    }),
    [theme, resolvedTheme, reducedMotion, motionPreference, setTheme, setReducedMotion],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
