import { useNavigate } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { InlineAlert } from "../../components/ui/InlineAlert";

import styles from "./onboarding.module.css";

export default function OnboardingPeople() {
  const navigate = useNavigate();

  return (
    <Card className={styles.card}>
      <h1 className={styles.title}>Is there someone you trust?</h1>
      <p className={styles.lede}>Adding someone is optional. You can do this any time.</p>

      <div className={styles.form}>
        <InlineAlert tone="info" title="Trusted contacts are coming soon">
          People and invitations arrive in a later update. For now, continue to the last step.
          Nothing is sent when you finish onboarding.
        </InlineAlert>

        <div className={styles.actions}>
          <Button onClick={() => navigate("/onboarding/privacy")} fullWidth>
            Continue
          </Button>
        </div>
      </div>
    </Card>
  );
}
