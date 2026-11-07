import { formatInTimeZone, toZonedTime } from "date-fns-tz";

export function maskEmail(value) {
  const email = String(value ?? "");
  const at = email.indexOf("@");
  if (at <= 0) return email;
  const local = email.slice(0, at);
  const domain = email.slice(at);
  return `${local.slice(0, 1)}***${domain}`;
}

export function greetingFor(now, timezone) {
  let hour = now.getHours();
  try {
    hour = toZonedTime(now, timezone || "UTC").getHours();
  } catch {
    hour = now.getHours();
  }
  if (hour < 5) return "Hello";
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export function longDate(now, timezone) {
  try {
    return formatInTimeZone(now, timezone || "UTC", "EEE, d MMMM");
  } catch {
    return formatInTimeZone(now, "UTC", "EEE, d MMMM");
  }
}

export function shortDate(value, timezone) {
  if (!value) return "";
  try {
    return formatInTimeZone(new Date(value), timezone || "UTC", "d MMM yyyy");
  } catch {
    return "";
  }
}

export function minutesLabel(seconds) {
  const minutes = Math.max(1, Math.ceil(Number(seconds || 0) / 60));
  return minutes === 1 ? "1 minute" : `${minutes} minutes`;
}
