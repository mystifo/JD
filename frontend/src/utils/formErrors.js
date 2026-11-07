const NON_FIELD_KEYS = new Set(["consents", "non_field_errors", "detail", "token"]);

export function fieldErrorMessage(value) {
  if (Array.isArray(value)) return fieldErrorMessage(value[0]);
  if (value && typeof value === "object") {
    return fieldErrorMessage(Object.values(value)[0]);
  }
  return value ? String(value) : "";
}

/**
 * Map DRF `fields` back onto react-hook-form fields. Returns messages that do
 * not belong to a visible field so the page can show them in one alert.
 */
export function applyFieldErrors(error, setError, mapping = {}) {
  const extras = [];
  const fields = error?.fields ?? {};

  for (const [apiField, value] of Object.entries(fields)) {
    const target = mapping[apiField];
    if (!target || NON_FIELD_KEYS.has(apiField)) {
      const message = fieldErrorMessage(value);
      if (message) extras.push(message);
      continue;
    }
    setError(target, { type: "server", message: fieldErrorMessage(value) });
  }

  return extras;
}
