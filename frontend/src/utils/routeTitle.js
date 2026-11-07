const ROUTES = [
  ["/app/settings/delete", "Delete your account"],
  ["/app/settings/security", "Security"],
  ["/app/settings/privacy", "Privacy"],
  ["/app/settings/notifications", "Notifications"],
  ["/app/settings/data", "Your data"],
  ["/app/settings/profile", "Profile"],
  ["/app/settings", "Settings"],
  ["/app/notifications", "Notifications"],
  ["/app/mood", "Mood"],
  ["/app/journal", "Journal"],
  ["/app/selfcare", "Self-care"],
  ["/app/people", "People"],
  ["/app/calm", "Calm Space"],
  ["/app/insights", "Insights"],
  ["/app", "Today"],
  ["/onboarding/profile", "Set up your space"],
  ["/onboarding/wellness", "How this space feels"],
  ["/onboarding/notifications", "When to reach you"],
  ["/onboarding/people", "People you trust"],
  ["/onboarding/privacy", "What stays private"],
  ["/register", "Create your space"],
  ["/login", "Log in"],
  ["/forgot-password", "Forgot password"],
  ["/reset-password", "Choose a new password"],
  ["/verify-email", "Verify your email"],
  ["/confirm-email-change", "Confirm your email"],
  ["/privacy", "Privacy"],
  ["/terms", "Terms"],
  ["/support-resources", "Support resources"],
  ["/invitation", "Invitation"],
  ["/support-response", "Support response"],
  ["/", "Welcome"],
];

export function routeTitle(pathname) {
  const match = ROUTES.find(
    ([path]) => pathname === path || (path !== "/" && pathname.startsWith(`${path}/`)),
  );
  return match ? match[1] : "Page not found";
}
