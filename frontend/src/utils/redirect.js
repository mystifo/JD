/**
 * Only same-origin absolute paths are accepted for `?next=` redirects.
 * Mirrors `common.validators.safe_redirect_path` on the server.
 */
export function safeRedirect(value, fallback = "/app") {
  if (!value || typeof value !== "string") return fallback;
  if (!value.startsWith("/") || value.startsWith("//")) return fallback;
  if (value.includes("://") || value.startsWith("/\\")) return fallback;
  return value;
}
