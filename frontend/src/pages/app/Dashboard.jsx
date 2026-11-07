import { formatInTimeZone } from "date-fns-tz";
import { Link } from "react-router-dom";

import { LockIcon } from "../../components/icons";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { useSession } from "../../hooks/useSession";
import { greetingFor, longDate } from "../../utils/format";


import styles from "./Dashboard.module.css";

function DashboardCard({ title, children, action }) {
  return (
    <Card className={styles.card}>
      <h2 className={styles.cardTitle}>{title}</h2>
      <p className={styles.cardBody}>{children}</p>
      {action ? <div className={styles.cardAction}>{action}</div> : null}
    </Card>
  );
}

export default function Dashboard() {
  const { user } = useSession();
  const now = new Date();
  const greeting = greetingFor(now, user?.timezone);
  const date = longDate(now, user?.timezone);

  let timezone = "UTC";
  try {
    timezone = formatInTimeZone(now, user?.timezone || "UTC", "zzz");
  } catch {
    timezone = "UTC";
  }

  if (!user?.emailVerified) {
    return (
      <div>
        <header className={styles.header}>
          <div>
            <h1 className={styles.greeting}>
              {greeting}, {user?.displayName}
            </h1>
            <p className={styles.date}>{date}</p>
          </div>
        </header>
        <Card className={styles.locked}>
          <span className={styles.lockIcon} aria-hidden="true">
            <LockIcon width="28" height="28" />
          </span>
          <h2 className={styles.cardTitle}>Your private modules are locked</h2>
          <p className={styles.cardBody}>
            Verify your email to unlock check-ins, your journal, routines, and insights. The banner
            above can send a new link.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <header className={styles.header}>
        <div>
          <h1 className={styles.greeting}>
            {greeting}, {user?.displayName}
          </h1>
          <p className={styles.date}>
            {date} · {timezone}
          </p>
        </div>
      </header>

      <div className={styles.grid}>
        <DashboardCard title="How are you feeling today?">
          Mood check-ins arrive in the next update. When they do, you&apos;ll be able to notice how
          you feel without turning it into a score.
        </DashboardCard>

        <DashboardCard
          title="I need someone"
          action={
            <Button as={Link} to="/app/people" variant="secondary" size="sm">
              Open People
            </Button>
          }
        >
          Add people you trust and ask for support when you need it. Nothing is shared unless you
          choose it.
        </DashboardCard>

        <DashboardCard
          title="Today's routines"
          action={
            <Button as={Link} to="/app/selfcare" variant="secondary" size="sm">
              Open self-care
            </Button>
          }
        >
          Build a gentle routine and keep it at your own pace. Nothing is a streak here.
        </DashboardCard>

        <DashboardCard
          title="This week"
          action={
            <Button as={Link} to="/app/insights" variant="secondary" size="sm">
              See insights
            </Button>
          }
        >
          Your check-ins and entries will appear here. Counts are always “in the last 7 days”, never
          “days in a row”.
        </DashboardCard>

        <DashboardCard
          title="Your journal is private here"
          action={
            <Button as={Link} to="/app/journal" variant="secondary" size="sm">
              Open journal
            </Button>
          }
        >
          Journal entries arrive soon. Lists show titles, never content previews, and nothing is
          shared automatically.
        </DashboardCard>
      </div>
    </div>
  );
}
