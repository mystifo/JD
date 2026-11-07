import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { InlineAlert } from "../../components/ui/InlineAlert";
import { useSession } from "../../hooks/useSession";
import { profileApi } from "../../services/profile";
import { onboardingPrivacySchema } from "../../services/schemas";

import styles from "./onboarding.module.css";

const promises = [
  "Your journal and moods are yours. Nothing is shared automatically.",
  "A support request shares only what you tick, once, and you can withdraw it.",
  "You can export or delete everything from Settings.",
  "HerSpace doesn't diagnose anything and isn't a replacement for care.",
];

export default function OnboardingPrivacy() {
  const navigate = useNavigate();
  const { refresh } = useSession();
  const [formError, setFormError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(onboardingPrivacySchema),
    defaultValues: { acknowledged: false },
  });

  async function onSubmit() {
    setFormError("");
    try {
      await profileApi.completeOnboarding(true);
      await refresh();
      navigate("/app", { replace: true });
    } catch (error) {
      setFormError(error.message ?? "We couldn't finish onboarding.");
    }
  }

  return (
    <Card className={styles.card}>
      <h1 className={styles.title}>What stays private</h1>
      <ul className={styles.list}>
        {promises.map((text) => (
          <li key={text}>
            <span className={styles.bullet} aria-hidden="true" />
            <span>{text}</span>
          </li>
        ))}
      </ul>

      <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
        {formError ? <InlineAlert tone="error">{formError}</InlineAlert> : null}

        <div>
          <label htmlFor="privacy-acknowledged" className="cluster">
            <input
              id="privacy-acknowledged"
              type="checkbox"
              aria-invalid={errors.acknowledged ? "true" : undefined}
              aria-describedby={errors.acknowledged ? "privacy-acknowledged-error" : undefined}
              {...register("acknowledged")}
            />
            <span>I understand</span>
          </label>
          {errors.acknowledged ? (
            <p
              id="privacy-acknowledged-error"
              style={{ color: "var(--danger)", fontSize: "var(--text-small)" }}
              role="alert"
            >
              {errors.acknowledged.message}
            </p>
          ) : null}
        </div>

        <div className={styles.actions}>
          <Button type="submit" loading={isSubmitting} fullWidth>
            Enter my space
          </Button>
        </div>
      </form>
    </Card>
  );
}
