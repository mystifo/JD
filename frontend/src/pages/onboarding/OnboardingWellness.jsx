import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { ChipGroup } from "../../components/ui/ChipGroup";
import { InlineAlert } from "../../components/ui/InlineAlert";
import { Select } from "../../components/ui/Select";
import { Skeleton } from "../../components/ui/Skeleton";
import { TextField } from "../../components/ui/TextField";
import { Toggle } from "../../components/ui/Toggle";
import { profileApi } from "../../services/profile";
import { qk } from "../../services/queryKeys";

import styles from "./onboarding.module.css";

const weekOptions = [
  { value: 1, label: "Monday" },
  { value: 0, label: "Sunday" },
];

const calmOptions = [
  { value: 60, label: "1 minute" },
  { value: 180, label: "3 minutes" },
  { value: 300, label: "5 minutes" },
  { value: 600, label: "10 minutes" },
  { value: 900, label: "15 minutes" },
  { value: 1200, label: "20 minutes" },
];

export default function OnboardingWellness() {
  const navigate = useNavigate();
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const [values, setValues] = useState({
    weekStartsOn: 1,
    checkinReminderEnabled: false,
    checkinReminderTime: "20:00",
    calmDefaultDurationSeconds: 300,
  });

  const preferencesQuery = useQuery({
    queryKey: qk.preferences,
    queryFn: profileApi.getPreferences,
  });

  useEffect(() => {
    if (!preferencesQuery.data) return;
    setValues({
      weekStartsOn: preferencesQuery.data.weekStartsOn,
      checkinReminderEnabled: preferencesQuery.data.checkinReminderEnabled,
      checkinReminderTime: preferencesQuery.data.checkinReminderTime ?? "20:00",
      calmDefaultDurationSeconds: preferencesQuery.data.calmDefaultDurationSeconds,
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
        weekStartsOn: values.weekStartsOn,
        checkinReminderEnabled: values.checkinReminderEnabled,
        checkinReminderTime: values.checkinReminderEnabled ? values.checkinReminderTime : null,
        calmDefaultDurationSeconds: Number(values.calmDefaultDurationSeconds),
      });
      navigate("/onboarding/notifications");
    } catch (error) {
      setFormError(error.message ?? "We couldn't save that.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card className={styles.card}>
      <h1 className={styles.title}>How would you like this space to feel?</h1>
      <p className={styles.lede}>Gentle defaults. Nothing here is a streak or a target.</p>

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

          <ChipGroup
            label="Week starts on"
            options={weekOptions}
            value={values.weekStartsOn}
            onChange={(value) => update("weekStartsOn", Number(value))}
          />

          <div>
            <Toggle
              label="Daily check-in reminder"
              description="A quiet nudge to notice how you feel."
              checked={values.checkinReminderEnabled}
              onChange={(checked) => update("checkinReminderEnabled", checked)}
            />
            {values.checkinReminderEnabled ? (
              <TextField
                label="Reminder time"
                type="time"
                value={values.checkinReminderTime}
                onChange={(event) => update("checkinReminderTime", event.target.value)}
              />
            ) : null}
          </div>

          <Select
            label="Calm Space default length"
            options={calmOptions}
            value={values.calmDefaultDurationSeconds}
            onChange={(event) => update("calmDefaultDurationSeconds", event.target.value)}
          />

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
