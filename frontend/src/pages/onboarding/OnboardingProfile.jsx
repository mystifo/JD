import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { InlineAlert } from "../../components/ui/InlineAlert";
import { Skeleton } from "../../components/ui/Skeleton";
import { TextArea } from "../../components/ui/TextArea";
import { TextField } from "../../components/ui/TextField";
import { useSession } from "../../hooks/useSession";
import { profileApi } from "../../services/profile";
import { qk } from "../../services/queryKeys";
import { profileFormSchema } from "../../services/schemas";
import { applyFieldErrors } from "../../utils/formErrors";
import { detectTimezone, timezoneOptions } from "../../utils/timezones";

import styles from "./onboarding.module.css";

export default function OnboardingProfile() {
  const navigate = useNavigate();
  const { user } = useSession();
  const [formError, setFormError] = useState("");
  const profileQuery = useQuery({ queryKey: qk.profile, queryFn: profileApi.getProfile });
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
  const timezone = watch("timezone");
  const zones = timezoneOptions();

  useEffect(() => {
    if (!profileQuery.data) return;
    reset({
      displayName: profileQuery.data.displayName || user?.displayName || "",
      pronouns: profileQuery.data.pronouns ?? "",
      bio: profileQuery.data.bio ?? "",
      timezone: profileQuery.data.timezone || user?.timezone || detectTimezone(),
    });
  }, [profileQuery.data, reset, user?.displayName, user?.timezone]);

  async function onSubmit(values) {
    setFormError("");
    try {
      await profileApi.updateProfile({
        displayName: values.displayName,
        pronouns: values.pronouns.trim() || null,
        bio: values.bio.trim() || null,
        timezone: values.timezone,
      });
      navigate("/onboarding/wellness");
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
    <Card className={styles.card}>
      <h1 className={styles.title}>Let&apos;s set up your space</h1>
      <p className={styles.lede}>You can change any of this later in Settings.</p>

      {profileQuery.isPending ? (
        <div className={styles.form} aria-busy="true">
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
            label="What should we call you?"
            autoComplete="nickname"
            required
            error={errors.displayName?.message}
            {...register("displayName")}
          />

          <div>
            <TextField
              label="Time zone"
              list="timezone-options"
              hint={
                timezone === detectTimezone()
                  ? "Detected from your browser. Change it if that's wrong."
                  : `Your browser suggests ${detectTimezone()}.`
              }
              required
              error={errors.timezone?.message}
              {...register("timezone")}
            />
            <datalist id="timezone-options">
              {zones.map((zone) => (
                <option key={zone} value={zone} />
              ))}
            </datalist>
          </div>

          <TextField
            label="Pronouns (optional)"
            autoComplete="off"
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

          <div className={styles.actions}>
            <Button type="submit" loading={isSubmitting} fullWidth>
              Continue
            </Button>
          </div>
        </form>
      ) : null}
    </Card>
  );
}
