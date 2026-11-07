import "@fontsource/inter/400.css";
import "@fontsource/inter/600.css";
import "@fontsource/manrope/500.css";
import "@fontsource/manrope/600.css";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { SessionProvider } from "./context/SessionContext";
import { ThemeProvider } from "./context/ThemeContext";
import { ToastProvider } from "./context/ToastContext";
import { ensureCsrf } from "./services/http";
import "./styles/tokens.css";
import "./styles/reset.css";
import "./styles/global.css";
import "./styles/utilities.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 5 * 60_000,
      retry: (count, error) => count < 2 && !error?.isAuthError && error?.status !== 404,
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
    },
    mutations: { retry: 0 },
  },
});

async function boot() {
  // The CSRF cookie must exist before the first unsafe request. This never
  // blocks rendering if the API is briefly unavailable: the HTTP client
  // refreshes and retries once.
  await ensureCsrf();

  const root = createRoot(document.getElementById("root"));
  root.render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <SessionProvider>
          <ToastProvider>
            <ThemeProvider>
              <BrowserRouter>
                <ErrorBoundary>
                  <App />
                </ErrorBoundary>
              </BrowserRouter>
            </ThemeProvider>
          </ToastProvider>
        </SessionProvider>
      </QueryClientProvider>
    </StrictMode>,
  );
}

boot();
