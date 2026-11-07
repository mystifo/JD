import { Link } from "react-router-dom";

import { PageHeader } from "../../components/PageHeader";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";

const pages = {
  security: {
    title: "Security",
    body: "Password changes, active sessions, and email updates will live here. Until then, use the sign-in and reset flows.",
  },
  privacy: {
    title: "Privacy",
    body: "Consent history and sharing controls will live here. Support shares stay revocable from the request that created them.",
  },
  notifications: {
    title: "Notifications",
    body: "Reminder times, quiet hours, and notification categories will live here. Your onboarding choices are already saved.",
  },
  data: {
    title: "Your data",
    body: "Export and download controls will live here. You will always be able to take your content with you.",
  },
};

export function SettingsPlaceholder({ page }) {
  const content = pages[page];
  return (
    <div>
      <PageHeader title={content.title} description="A quieter account control panel." />
      <Card>
        <EmptyState
          title={`${content.title} is on its way`}
          body={content.body}
          action={
            <Button as={Link} to="/app/settings/profile" variant="secondary">
              Back to Profile
            </Button>
          }
        />
      </Card>
    </div>
  );
}
