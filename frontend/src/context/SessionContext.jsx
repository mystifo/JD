import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useEffect, useMemo } from "react";

import { authApi } from "../services/auth";
import { setUnauthorizedHandler } from "../services/http";
import { qk } from "../services/queryKeys";

export const SessionContext = createContext(null);

const ANONYMOUS = {
  status: "anonymous",
  user: null,
  onboardingRequired: false,
  deletionScheduledFor: null,
  preferences: { theme: "system", reducedMotion: false },
  error: null,
};

async function loadSession() {
  try {
    const session = await authApi.getSession();
    return { status: "authenticated", ...session, error: null };
  } catch (error) {
    if (error?.status === 401) return ANONYMOUS;
    throw error;
  }
}

export function SessionProvider({ children }) {
  const queryClient = useQueryClient();
  const sessionQuery = useQuery({
    queryKey: qk.session,
    queryFn: loadSession,
    retry: false,
    staleTime: 5 * 60_000,
    refetchOnWindowFocus: false,
  });

  const signIn = useCallback(
    (session) => {
      queryClient.setQueryData(qk.session, {
        status: "authenticated",
        ...session,
        error: null,
      });
    },
    [queryClient],
  );

  const signOut = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      // Privacy: never leave another account's cached content behind.
      queryClient.clear();
      queryClient.setQueryData(qk.session, ANONYMOUS);
    }
  }, [queryClient]);

  const refresh = useCallback(() => sessionQuery.refetch(), [sessionQuery]);

  useEffect(() => {
    return setUnauthorizedHandler(() => {
      queryClient.clear();
      queryClient.setQueryData(qk.session, ANONYMOUS);
    });
  }, [queryClient]);

  const status = sessionQuery.isPending
    ? "loading"
    : sessionQuery.isError
      ? "error"
      : sessionQuery.data.status;

  const value = useMemo(
    () => ({
      status,
      user: sessionQuery.data?.user ?? null,
      onboardingRequired: sessionQuery.data?.onboardingRequired ?? false,
      deletionScheduledFor: sessionQuery.data?.deletionScheduledFor ?? null,
      preferences: sessionQuery.data?.preferences ?? {
        theme: "system",
        reducedMotion: false,
      },
      error: sessionQuery.error ?? null,
      signIn,
      signOut,
      refresh,
    }),
    [status, sessionQuery.data, sessionQuery.error, signIn, signOut, refresh],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}
