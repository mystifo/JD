import api from "./http";

function normaliseProfile(data) {
  return {
    id: data.id,
    displayName: data.display_name ?? "",
    pronouns: data.pronouns ?? "",
    bio: data.bio ?? "",
    dateOfBirth: data.date_of_birth ?? null,
    timezone: data.timezone ?? "UTC",
    locale: data.locale ?? "en",
    email: data.email,
    emailVerified: Boolean(data.email_verified),
    onboardingCompletedAt: data.onboarding_completed_at ?? null,
    createdAt: data.created_at,
  };
}

function normalisePreferences(data) {
  return {
    theme: data.theme ?? "system",
    reducedMotion: Boolean(data.reduced_motion),
    weekStartsOn: data.week_starts_on ?? 1,
    timeFormat: data.time_format ?? "24",
    dateFormat: data.date_format ?? "d MMM yyyy",
    checkinReminderEnabled: Boolean(data.checkin_reminder_enabled),
    checkinReminderTime: data.checkin_reminder_time ?? null,
    routineRemindersEnabled: Boolean(data.routine_reminders_enabled),
    hydrationRemindersEnabled: Boolean(data.hydration_reminders_enabled),
    inAppNotificationsEnabled: Boolean(data.in_app_notifications_enabled),
    emailNotificationsEnabled: Boolean(data.email_notifications_enabled),
    supportNotificationsEnabled: Boolean(data.support_notifications_enabled),
    quietHoursStart: data.quiet_hours_start ?? null,
    quietHoursEnd: data.quiet_hours_end ?? null,
    calmDefaultDurationSeconds: data.calm_default_duration_seconds ?? 300,
    calmSoundEnabled: Boolean(data.calm_sound_enabled),
    dismissedSuggestions: data.dismissed_suggestions ?? [],
  };
}

const PROFILE_FIELD_MAP = {
  displayName: "display_name",
  pronouns: "pronouns",
  bio: "bio",
  dateOfBirth: "date_of_birth",
  timezone: "timezone",
  locale: "locale",
};

const PREFERENCE_FIELD_MAP = {
  theme: "theme",
  reducedMotion: "reduced_motion",
  weekStartsOn: "week_starts_on",
  timeFormat: "time_format",
  dateFormat: "date_format",
  checkinReminderEnabled: "checkin_reminder_enabled",
  checkinReminderTime: "checkin_reminder_time",
  routineRemindersEnabled: "routine_reminders_enabled",
  hydrationRemindersEnabled: "hydration_reminders_enabled",
  inAppNotificationsEnabled: "in_app_notifications_enabled",
  emailNotificationsEnabled: "email_notifications_enabled",
  supportNotificationsEnabled: "support_notifications_enabled",
  quietHoursStart: "quiet_hours_start",
  quietHoursEnd: "quiet_hours_end",
  calmDefaultDurationSeconds: "calm_default_duration_seconds",
  calmSoundEnabled: "calm_sound_enabled",
  dismissedSuggestions: "dismissed_suggestions",
};

function payloadFor(fields, map) {
  const payload = {};
  for (const [camel, snake] of Object.entries(map)) {
    if (Object.prototype.hasOwnProperty.call(fields, camel)) {
      payload[snake] = fields[camel];
    }
  }
  return payload;
}

export const profileApi = {
  async getProfile() {
    const { data } = await api.get("/profile/");
    return normaliseProfile(data);
  },

  async updateProfile(fields) {
    const { data } = await api.patch("/profile/", payloadFor(fields, PROFILE_FIELD_MAP));
    return normaliseProfile(data);
  },

  async getPreferences() {
    const { data } = await api.get("/preferences/");
    return normalisePreferences(data);
  },

  async updatePreferences(fields) {
    const { data } = await api.patch(
      "/preferences/",
      payloadFor(fields, PREFERENCE_FIELD_MAP),
    );
    return normalisePreferences(data);
  },

  async completeOnboarding(privacyAcknowledged) {
    const { data } = await api.post("/onboarding/complete/", {
      privacy_acknowledged: privacyAcknowledged,
    });
    return { onboardingCompletedAt: data.onboarding_completed_at };
  },
};
