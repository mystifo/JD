import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { PageHeader } from "../../components/PageHeader";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { ChipGroup } from "../../components/ui/ChipGroup";
import { InlineAlert } from "../../components/ui/InlineAlert";
import { Skeleton } from "../../components/ui/Skeleton";
import { TextArea } from "../../components/ui/TextArea";
import { TextField } from "../../components/ui/TextField";
import { Toggle } from "../../components/ui/Toggle";
import { useSession } from "../../hooks/useSession";
import { useTheme } from "../../hooks/useTheme";
import { useToast } from "../../hooks/useToast";
import { profileApi } from "../../services/profile";
import { qk } from "../../services/queryKeys";
import { profileFormSchema } from "../../services/schemas";
import { applyFieldErrors } from "../../utils/formErrors";
import { detectTimezone, timezoneOptions } from "../../utils/timezones";

import styles from "./settings.module.css";

const themeOptions = [
  { value: "system", label: "System" },
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
];

export default function SettingsProfile() {
  const { user, refresh } = useSession();
  const theme = useTheme();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [formError, setFormError] = useState("");
  const profileQuery = useQuery({ queryKey: qk.profile, queryFn: profileApi.getProfile });
  const preferencesQuery = useQuery({
    queryKey: qk.preferences,
    queryFn: profileApi.getPreferences,
  });

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(profileFormSchema),
    defaultValues: {
      displayName: user?.displayName ?? "",
      pronouns: "",
      bio: "",
      timezone: user?.timezone ?? detectTimezone(),
    },
  });

  const bio = watch("bio");
  const zones = timezoneOptions();

  useEffect(() => {
    if (!profileQuery.data) return;
    reset({
      displayName: profileQuery.data.displayName ?? "",
      pronouns: profileQuery.data.pronouns ?? "",
      bio: profileQuery.data.bio ?? "",
      timezone: profileQuery.data.timezone ?? detectTimezone(),
    });
  }, [profileQuery.data, reset]);

  if (!user?.emailVerified) {
    return (
      <div>
        <PageHeader title="Profile" />
        <InlineAlert tone="warning" title="Verify your email to edit your profile">
          Use the banner above to send a new verification link.
        </InlineAlert>
      </div>
    );
  }

  async function onSubmit(values) {
    setFormError("");
    try {
      const saved = await profileApi.updateProfile({
        displayName: values.displayName,
        pronouns: values.pronouns.trim() || null,
        bio: values.bio.trim() || null,
        timezone: values.timezone,
      });
      queryClient.setQueryData(qk.profile, saved);
      await refresh();
      showToast("Profile saved.");
    } catch (error) {
      const extras = applyFieldErrors(error, setError, {
        display_name: "displayName",
        pronouns: "pronouns",
        bio: "bio",
        timezone: "timezone",
      });
      if (error.code === "invalid_timezone") {
        setError("timezone", { type: "server", message: "Choose a valid time zone." });
      } else if (extras.length) {
        setFormError(extras[0]);
      } else if (!Object.keys(error.fields ?? {}).length) {
        setFormError(error.message);
      }
    }
  }

  return (
    <div>
      <PageHeader title="Profile" description="How you appear to yourself in this space." />

      <div className={styles.stack}>
        <Card>
          <h2 className={styles.sectionTitle}>About you</h2>

          {profileQuery.isPending ? (
            <div aria-busy="true">
              <Skeleton lines={3} />
            </div>
          ) : null}

          {profileQuery.isError ? (
            <InlineAlert
              tone="error"
              title="We couldn't load your profile"
              action={
                <Button size="sm" onClick={() => profileQuery.refetch()}>
                  Try again
                </Button>
              }
            >
              {profileQuery.error?.message}
            </InlineAlert>
          ) : null}

          {profileQuery.data ? (
            <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
              {formError ? <InlineAlert tone="error">{formError}</InlineAlert> : null}

              <TextField
                label="Display name"
                required
                error={errors.displayName?.message}
                {...register("displayName")}
              />
              <TextField
                label="Pronouns (optional)"
                error={errors.pronouns?.message}
                {...register("pronouns")}
              />
              <TextArea
                label="A line about you (optional)"
                maxLength={280}
                showCounter
                value={bio ?? ""}
                error={errors.bio?.message}
                {...register("bio")}
              />
              <div>
                <TextField
                  label="Time zone"
                  list="settings-timezone-options"
                  hint={`Your browser suggests ${detectTimezone()}.`}
                  required
                  error={errors.timezone?.message}
                  {...register("timezone")}
                />
                <datalist id="settings-timezone-options">
                  {zones.map((zone) => (
                    <option key={zone} value={zone} />
                  ))}
                </datalist>
              </div>

              <TextField label="Email" value={profileQuery.data.email} readOnly disabled />
              <p className={styles.hint}>
                Email changes are confirmed from Settings in a later update.
              </p>

              <div>
                <Button type="submit" loading={isSubmitting}>
                  Save profile
                </Button>
              </div>
            </form>
          ) : null}
        </Card>

        <Card>
          <h2 className={styles.sectionTitle}>Appearance</h2>
          <p className={styles.hint}>
            Theme applies immediately and is saved to your account. Your browser preference is used
            before the first paint, so there is no flash.
          </p>

          {preferencesQuery.isPending ? <Skeleton lines={2} /> : null}
          {preferencesQuery.isError ? (
            <InlineAlert tone="error">We couldn&apos;t load your appearance preferences.</InlineAlert>
          ) : null}

          {preferencesQuery.data ? (
            <div className={styles.appearance}>
              <ChipGroup
                label="Theme"
                options={themeOptions}
                value={theme.theme}
                onChange={theme.setTheme}
              />
              <Toggle
                label="Reduce motion"
                description="Calm transitions and static versions of animated tools."
                checked={theme.reducedMotionPreference}
                onChange={theme.setReducedMotion}
              />
            </div>
          ) : null}
        </Card>
      </div>
    </div>
  );
}
