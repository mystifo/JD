import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { InlineAlert } from "../../components/ui/InlineAlert";
import { Skeleton } from "../../components/ui/Skeleton";
import { TextField } from "../../components/ui/TextField";
import { Toggle } from "../../components/ui/Toggle";
import { profileApi } from "../../services/profile";
import { qk } from "../../services/queryKeys";

import styles from "./onboarding.module.css";

export default function OnboardingNotifications() {
  const navigate = useNavigate();
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const [values, setValues] = useState({
    inAppNotificationsEnabled: true,
    emailNotificationsEnabled: true,
    supportNotificationsEnabled: true,
    quietHoursEnabled: false,
    quietHoursStart: "22:00",
    quietHoursEnd: "07:00",
  });

  const preferencesQuery = useQuery({
    queryKey: qk.preferences,
    queryFn: profileApi.getPreferences,
  });

  useEffect(() => {
    if (!preferencesQuery.data) return;
    const start = preferencesQuery.data.quietHoursStart;
    const end = preferencesQuery.data.quietHoursEnd;
    setValues({
      inAppNotificationsEnabled: preferencesQuery.data.inAppNotificationsEnabled,
      emailNotificationsEnabled: preferencesQuery.data.emailNotificationsEnabled,
      supportNotificationsEnabled: preferencesQuery.data.supportNotificationsEnabled,
      quietHoursEnabled: Boolean(start && end),
      quietHoursStart: start ?? "22:00",
      quietHoursEnd: end ?? "07:00",
    });
  }, [preferencesQuery.data]);

  function update(field, value) {
    setValues((current) => ({ ...current, [field]: value }));
  }

  async function onSubmit(event) {
    event.preventDefault();
    setFormError("");
    setSaving(true);
    try {
      await profileApi.updatePreferences({
        inAppNotificationsEnabled: values.inAppNotificationsEnabled,
        emailNotificationsEnabled: values.emailNotificationsEnabled,
        supportNotificationsEnabled: values.supportNotificationsEnabled,
        quietHoursStart: values.quietHoursEnabled ? values.quietHoursStart : null,
        quietHoursEnd: values.quietHoursEnabled ? values.quietHoursEnd : null,
      });
      navigate("/onboarding/people");
    } catch (error) {
      setFormError(error.message ?? "We couldn't save that.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card className={styles.card}>
      <h1 className={styles.title}>When should we reach you?</h1>
      <p className={styles.lede}>Nothing non-urgent will arrive during quiet hours.</p>

      {preferencesQuery.isPending ? (
        <div className={styles.form} aria-busy="true">
          <Skeleton lines={4} />
        </div>
      ) : null}

      {preferencesQuery.isError ? (
        <InlineAlert
          tone="error"
          title="We couldn't load your preferences"
          action={
            <Button size="sm" onClick={() => preferencesQuery.refetch()}>
              Try again
            </Button>
          }
        >
          {preferencesQuery.error?.message}
        </InlineAlert>
      ) : null}

      {preferencesQuery.data ? (
        <form className={styles.form} onSubmit={onSubmit}>
          {formError ? <InlineAlert tone="error">{formError}</InlineAlert> : null}

          <Toggle
            label="In-app notifications"
            checked={values.inAppNotificationsEnabled}
            onChange={(checked) => update("inAppNotificationsEnabled", checked)}
          />
          <Toggle
            label="Email notifications"
            description="Security notices are always sent, whatever this is set to."
            checked={values.emailNotificationsEnabled}
            onChange={(checked) => update("emailNotificationsEnabled", checked)}
          />
          <Toggle
            label="Support request updates"
            description="Let you know when someone responds."
            checked={values.supportNotificationsEnabled}
            onChange={(checked) => update("supportNotificationsEnabled", checked)}
          />
          <Toggle
            label="Quiet hours"
            description="Nothing non-urgent will arrive during these hours."
            checked={values.quietHoursEnabled}
            onChange={(checked) => update("quietHoursEnabled", checked)}
          />

          {values.quietHoursEnabled ? (
            <div className={styles.rangeRow}>
              <TextField
                label="From"
                type="time"
                value={values.quietHoursStart}
                onChange={(event) => update("quietHoursStart", event.target.value)}
              />
              <TextField
                label="To"
                type="time"
                value={values.quietHoursEnd}
                onChange={(event) => update("quietHoursEnd", event.target.value)}
              />
            </div>
          ) : null}

          <div className={styles.actions}>
            <Button type="submit" loading={saving} fullWidth>
              Continue
            </Button>
          </div>
        </form>
      ) : null}
    </Card>
  );
}
