import api from "./http";

/**
 * Turn the API's snake_case UserSession into the camelCase shape used by the
 * React tree. Presentation preferences are not private content; everything
 * else stays in memory only.
 */
export function normaliseSession(data) {
  return {
    user: {
      id: data.user?.id ?? null,
      email: data.user?.email ?? "",
      displayName: data.user?.display_name ?? "",
      emailVerified: Boolean(data.user?.email_verified),
      timezone: data.user?.timezone ?? "UTC",
    },
    onboardingRequired: Boolean(data.onboarding_required),
    deletionScheduledFor: data.deletion_scheduled_for ?? null,
    preferences: {
      theme: data.preferences?.theme ?? "system",
      reducedMotion: Boolean(data.preferences?.reduced_motion),
    },
  };
}

export const authApi = {
  async register({ email, password, acceptTerms, acceptPrivacy, timezone, displayName }) {
    const { data } = await api.post("/auth/register/", {
      email,
      password,
      accept_terms: acceptTerms,
      accept_privacy: acceptPrivacy,
      timezone,
      ...(displayName ? { display_name: displayName } : {}),
    });
    return {
      id: data.id,
      email: data.email,
      emailVerified: Boolean(data.email_verified),
      onboardingRequired: Boolean(data.onboarding_required),
    };
  },

  async login({ email, password }) {
    const { data } = await api.post("/auth/login/", { email, password });
    return normaliseSession(data);
  },

  async logout() {
    await api.post("/auth/logout/");
  },

  async logoutAll() {
    await api.post("/auth/logout-all/");
  },

  async getSession() {
    const { data } = await api.get("/auth/session/");
    return normaliseSession(data);
  },

  async verifyEmail(token) {
    const { data } = await api.post("/auth/verify-email/", { token });
    return { emailVerified: Boolean(data.email_verified) };
  },

  async resendVerification() {
    const { data } = await api.post("/auth/verify-email/resend/");
    return { sent: Boolean(data.sent) };
  },

  async requestPasswordReset(email) {
    const { data } = await api.post("/auth/password-reset/", { email });
    return { message: data.message };
  },

  async confirmPasswordReset({ token, newPassword }) {
    const { data } = await api.post("/auth/password-reset/confirm/", {
      token,
      new_password: newPassword,
    });
    return { passwordChanged: Boolean(data.password_changed) };
  },

  async changePassword({ currentPassword, newPassword }) {
    const { data } = await api.post("/auth/password-change/", {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return { passwordChanged: Boolean(data.password_changed) };
  },

  async requestEmailChange({ newEmail, currentPassword }) {
    const { data } = await api.post("/auth/email-change/", {
      new_email: newEmail,
      current_password: currentPassword,
    });
    return { pending: Boolean(data.pending), newEmail: data.new_email };
  },

  async confirmEmailChange(token) {
    const { data } = await api.post("/auth/email-change/confirm/", { token });
    return { email: data.email, emailVerified: Boolean(data.email_verified) };
  },
};
