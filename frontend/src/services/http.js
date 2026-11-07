import axios from "axios";

export class ApiError extends Error {
  constructor({ status, code, message, fields, requestId }) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.fields = fields ?? {};
    this.requestId = requestId;
    this.isAuthError = status === 401;
  }
}

const DEFAULT_MESSAGES = {
  0: "We couldn't reach HerSpace. Please try again.",
  400: "Some fields need attention.",
  401: "Sign in to continue.",
  403: "You don't have access to that.",
  404: "We couldn't find that.",
  409: "That conflicts with something else. Refresh and try again.",
  410: "That link is no longer valid.",
  423: "Too many attempts. Please wait a moment.",
  429: "Too many attempts. Please wait a moment and try again.",
  500: "Something went wrong. Please try again.",
};

function defaultMessage(status) {
  return DEFAULT_MESSAGES[status] ?? DEFAULT_MESSAGES[500];
}

export function normaliseError(error) {
  if (error?.response) {
    const { status, data, headers } = error.response;
    const body = data?.error ?? {};
    return new ApiError({
      status,
      code: body.code ?? "server_error",
      message: body.message ?? defaultMessage(status),
      fields: body.fields,
      requestId: body.request_id ?? headers?.["x-request-id"],
    });
  }
  const online = typeof navigator === "undefined" || navigator.onLine !== false;
  return new ApiError({
    status: 0,
    code: online ? "network_error" : "offline",
    message: online
      ? "We couldn't reach HerSpace. Please try again."
      : "You're offline. Changes aren't saved.",
  });
}

function readCookie(name) {
  if (typeof document === "undefined") return null;
  return (
    document.cookie
      .split("; ")
      .find((row) => row.startsWith(`${name}=`))
      ?.split("=")
      .slice(1)
      .join("=") ?? null
  );
}

function isUnsafe(method) {
  return !["get", "head", "options", "trace"].includes(String(method ?? "get").toLowerCase());
}

function requestId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `req-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api/v1",
  withCredentials: true,
  timeout: 20_000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (isUnsafe(config.method)) {
    const token = readCookie("csrftoken");
    if (token) config.headers["X-CSRFToken"] = decodeURIComponent(token);
  }
  config.headers["X-Request-ID"] = requestId();
  return config;
});

let unauthorizedHandler = null;

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler;
  return () => {
    if (unauthorizedHandler === handler) unauthorizedHandler = null;
  };
}

const NO_SESSION_PATHS = ["/auth/login/", "/auth/session/", "/auth/csrf/"];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const normalized = normaliseError(error);
    const config = error.config ?? {};
    const url = String(config.url ?? "");

    // A stale CSRF cookie is recoverable: fetch a fresh token and retry once.
    if (
      normalized.status === 403 &&
      normalized.code === "permission_denied" &&
      isUnsafe(config.method) &&
      !config.__csrfRetried &&
      !url.includes("/auth/csrf/")
    ) {
      config.__csrfRetried = true;
      await api.get("/auth/csrf/");
      return api(config);
    }

    if (
      normalized.status === 401 &&
      unauthorizedHandler &&
      !NO_SESSION_PATHS.some((path) => url.includes(path))
    ) {
      unauthorizedHandler(normalized);
    }

    return Promise.reject(normalized);
  },
);

export async function ensureCsrf() {
  try {
    await api.get("/auth/csrf/");
  } catch {
    // The app can still render; the first unsafe request retries once.
  }
}

export default api;
