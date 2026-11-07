import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { FullPageSkeleton } from "./components/FullPageSkeleton";
import { RouteAnnouncer } from "./components/RouteAnnouncer";
import { RequireAuth } from "./guards/RequireAuth";
import { AppLayout } from "./layouts/AppLayout";
import { OnboardingLayout } from "./layouts/OnboardingLayout";
import { PublicLayout } from "./layouts/PublicLayout";
import { SettingsLayout } from "./layouts/SettingsLayout";

const Welcome = lazy(() => import("./pages/auth/Welcome"));
const Register = lazy(() => import("./pages/auth/Register"));
const Login = lazy(() => import("./pages/auth/Login"));
const ForgotPassword = lazy(() => import("./pages/auth/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/auth/ResetPassword"));
const VerifyEmail = lazy(() => import("./pages/auth/VerifyEmail"));
const ConfirmEmailChange = lazy(() => import("./pages/auth/ConfirmEmailChange"));

const OnboardingProfile = lazy(() => import("./pages/onboarding/OnboardingProfile"));
const OnboardingWellness = lazy(() => import("./pages/onboarding/OnboardingWellness"));
const OnboardingNotifications = lazy(
  () => import("./pages/onboarding/OnboardingNotifications"),
);
const OnboardingPeople = lazy(() => import("./pages/onboarding/OnboardingPeople"));
const OnboardingPrivacy = lazy(() => import("./pages/onboarding/OnboardingPrivacy"));

const Dashboard = lazy(() => import("./pages/app/Dashboard"));
const ComingSoon = lazy(() => import("./pages/app/ComingSoon"));
const SettingsProfile = lazy(() => import("./pages/settings/SettingsProfile"));
const SettingsPlaceholder = lazy(() => import("./pages/settings/SettingsPlaceholder"));
const SettingsDelete = lazy(() => import("./pages/settings/SettingsDelete"));

const Privacy = lazy(() => import("./pages/public/Privacy"));
const Terms = lazy(() => import("./pages/public/Terms"));
const SupportResources = lazy(() => import("./pages/public/SupportResources"));
const NotFound = lazy(() => import("./pages/public/NotFound"));
const TokenPlaceholder = lazy(() => import("./pages/public/TokenPlaceholder"));

export default function App() {
  return (
    <>
      <RouteAnnouncer />
      <Suspense fallback={<FullPageSkeleton />}>
        <Routes>
          <Route element={<PublicLayout />}>
            <Route index element={<Welcome />} />
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password/:token" element={<ResetPassword />} />
            <Route path="/verify-email/:token" element={<VerifyEmail />} />
            <Route path="/confirm-email-change/:token" element={<ConfirmEmailChange />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="/support-resources" element={<SupportResources />} />
            <Route path="/invitation/:token" element={<TokenPlaceholder />} />
            <Route path="/support-response/:token" element={<TokenPlaceholder />} />
          </Route>

          <Route element={<RequireAuth />}>
            <Route path="/onboarding/:step" element={<OnboardingLayout />}>
              <Route path="profile" element={<OnboardingProfile />} />
              <Route path="wellness" element={<OnboardingWellness />} />
              <Route path="notifications" element={<OnboardingNotifications />} />
              <Route path="people" element={<OnboardingPeople />} />
              <Route path="privacy" element={<OnboardingPrivacy />} />
            </Route>

            <Route path="/app" element={<AppLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="notifications" element={<ComingSoon />} />

              <Route path="mood" element={<ComingSoon />} />
              <Route path="people" element={<ComingSoon />} />
              <Route path="support" element={<ComingSoon />} />
              <Route path="journal" element={<ComingSoon />} />
              <Route path="selfcare" element={<ComingSoon />} />
              <Route path="calm" element={<ComingSoon />} />
              <Route path="insights" element={<ComingSoon />} />

              <Route path="settings" element={<SettingsLayout />}>
                <Route index element={<Navigate to="profile" replace />} />
                <Route path="profile" element={<SettingsProfile />} />
                <Route path="security" element={<SettingsPlaceholder page="security" />} />
                <Route path="privacy" element={<SettingsPlaceholder page="privacy" />} />
                <Route
                  path="notifications"
                  element={<SettingsPlaceholder page="notifications" />}
                />
                <Route path="data" element={<SettingsPlaceholder page="data" />} />
                <Route path="delete" element={<SettingsDelete />} />
              </Route>

              <Route path="*" element={<NotFound />} />
            </Route>
          </Route>

          <Route path="*" element={<PublicLayout />}>
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </Suspense>
    </>
  );
}
