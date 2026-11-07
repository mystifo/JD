import { Link } from "react-router-dom";

import { PageHeader } from "../../components/PageHeader";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { useSession } from "../../hooks/useSession";
import { shortDate } from "../../utils/format";

import styles from "./settings.module.css";

export default function SettingsDelete() {
  const { user, deletionScheduledFor } = useSession();

  if (deletionScheduledFor) {
    return (
      <div>
        <PageHeader title="Account deletion" description="Your account is scheduled for deletion." />
        <Card>
          <h2 className={styles.sectionTitle}>Scheduled for {shortDate(deletionScheduledFor, user?.timezone)}</h2>
          <div className={styles.form}>
            <p className="text-muted">
              Your space will be removed after the 7-day grace period. A cancellation link was sent
              to your email; use it before then to keep your account.
            </p>
            <p className="text-muted">
              Until the deletion runs, you can still read this status page. Other parts of HerSpace
              remain closed.
            </p>
            <Button as={Link} to="/support-resources" variant="secondary">
              Support resources
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Delete account" description="Nothing here is permanent without a grace period." />
      <Card>
        <EmptyState
          title="Account deletion arrives with privacy controls"
          body="When it ships, deletion will start a 7-day cancellable grace period and a link will be emailed to you. Nothing is deleted from this screen today."
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
