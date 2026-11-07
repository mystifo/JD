const FALLBACK_ZONES = [
  "UTC",
  "Europe/London",
  "Europe/Berlin",
  "Europe/Paris",
  "Europe/Madrid",
  "Europe/Rome",
  "Europe/Amsterdam",
  "Europe/Stockholm",
  "Europe/Warsaw",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "America/Toronto",
  "America/Sao_Paulo",
  "Asia/Dubai",
  "Asia/Kolkata",
  "Asia/Singapore",
  "Asia/Tokyo",
  "Australia/Sydney",
  "Pacific/Auckland",
];

export function detectTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

export function timezoneOptions() {
  const options = new Set([detectTimezone(), ...FALLBACK_ZONES]);
  if (typeof Intl.supportedValuesOf === "function") {
    try {
      for (const zone of Intl.supportedValuesOf("timeZone")) options.add(zone);
    } catch {
      // Older engines: the fallback list still covers common zones.
    }
  }
  return Array.from(options).sort((a, b) => a.localeCompare(b));
}
