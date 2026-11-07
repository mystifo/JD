import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { InlineAlert } from "../../components/ui/InlineAlert";
import { TextField } from "../../components/ui/TextField";
import { authApi } from "../../services/auth";
import { passwordChecks, registerSchema } from "../../services/schemas";
import { cx } from "../../utils/cx";
import { maskEmail } from "../../utils/format";
import { applyFieldErrors } from "../../utils/formErrors";
import { detectTimezone } from "../../utils/timezones";

import styles from "./auth.module.css";
import shared from "./authShared.module.css";

const checklist = [
  ["length", "At least 12 characters"],
  ["notCommon", "Not a common password"],
  ["notNumeric", "Not only numbers"],
  ["notSimilar", "Not based on your email"],
];

export default function Register() {
  const [submittedEmail, setSubmittedEmail] = useState(null);
  const [formError, setFormError] = useState("");
  const {
    register,
    handleSubmit,
    watch,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      password: "",
      acceptTerms: false,
      acceptPrivacy: false,
    },
  });

  const email = watch("email");
  const password = watch("password");
  const checks = passwordChecks(password, email);

  async function onSubmit(values) {
    setFormError("");
    try {
      const result = await authApi.register({
        email: values.email,
        password: values.password,
        acceptTerms: values.acceptTerms,
        acceptPrivacy: values.acceptPrivacy,
        timezone: detectTimezone(),
      });
      setSubmittedEmail(result.email);
    } catch (error) {
      const extras = applyFieldErrors(error, setError, {});
      if (error.code === "email_in_use") {
        setError("email", {
          type: "server",
          message: "An account with this email already exists. Log in instead.",
        });
      } else if (error.code === "rate_limited") {
        setFormError("Too many attempts. Please try again later.");
      } else if (extras.length) {
        setFormError(extras[0]);
      } else if (!Object.keys(error.fields ?? {}).length) {
        setFormError(error.message);
      }
    }
  }

  if (submittedEmail) {
    return (
      <div className={styles.page}>
        <section className={styles.card} aria-labelledby="check-inbox-title">
          <h1 id="check-inbox-title" className={styles.title}>
            Check your inbox
          </h1>
          <p className={styles.lede}>
            We sent a verification link to <strong>{maskEmail(submittedEmail)}</strong>.
          </p>
          <div className={styles.tokenState}>
            <p>
              Open the link, then log in to finish setting up your space. If it doesn&apos;t
              arrive in a few minutes, check your spam folder.
            </p>
            <Button as={Link} to={`/login?email=${encodeURIComponent(submittedEmail)}`}>
              Go to log in
            </Button>
            <p className={styles.lede}>
              You can resend the link from the verification banner after logging in.
            </p>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <section className={cx(styles.card, styles.splitCard)} aria-labelledby="register-title">
        <div className={styles.formPane}>
          <h1 id="register-title" className={styles.title}>
            Create your space
          </h1>
          <p className={styles.lede}>A private place to notice how you feel.</p>

          <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
            {formError ? <InlineAlert tone="error">{formError}</InlineAlert> : null}

            <TextField
              label="Email"
              type="email"
              autoComplete="email"
              required
              error={errors.email?.message}
              {...register("email")}
            />

            <div>
              <TextField
                label="Password"
                type="password"
                autoComplete="new-password"
                required
                hint="A short phrase you'll remember works well."
                error={errors.password?.message}
                {...register("password")}
              />
              <ul className={styles.checklist} aria-label="Password requirements">
                {checklist.map(([key, text]) => (
                  <li key={key} className={checks[key] ? styles.met : undefined}>
                    <span className={styles.mark} aria-hidden="true">
                      {checks[key] ? "✓" : ""}
                    </span>
                    <span>
                      {text}
                      <span className="visually-hidden">
                        {checks[key] ? " — met" : " — not met yet"}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <label className={styles.checkboxRow} htmlFor="accept-terms">
                <input
                  id="accept-terms"
                  type="checkbox"
                  aria-invalid={errors.acceptTerms ? "true" : undefined}
                  aria-describedby={errors.acceptTerms ? "accept-terms-error" : undefined}
                  {...register("acceptTerms")}
                />
                <span>
                  I agree to the{" "}
                  <a href="/terms" target="_blank" rel="noreferrer">
                    Terms of Service
                  </a>{" "}
                  (v1.0)
                </span>
              </label>
              {errors.acceptTerms ? (
                <p id="accept-terms-error" className={styles.fieldError} role="alert">
                  {errors.acceptTerms.message}
                </p>
              ) : null}
            </div>

            <div>
              <label className={styles.checkboxRow} htmlFor="accept-privacy">
                <input
                  id="accept-privacy"
                  type="checkbox"
                  aria-invalid={errors.acceptPrivacy ? "true" : undefined}
                  aria-describedby={errors.acceptPrivacy ? "accept-privacy-error" : undefined}
                  {...register("acceptPrivacy")}
                />
                <span>
                  I have read the{" "}
                  <a href="/privacy" target="_blank" rel="noreferrer">
                    Privacy Policy
                  </a>{" "}
                  (v1.0)
                </span>
              </label>
              {errors.acceptPrivacy ? (
                <p id="accept-privacy-error" className={styles.fieldError} role="alert">
                  {errors.acceptPrivacy.message}
                </p>
              ) : null}
            </div>

            <div className={styles.actions}>
              <Button type="submit" loading={isSubmitting} fullWidth>
                Create account
              </Button>
            </div>
          </form>

          <p className={shared.switchLine}>
            Already have one? <Link to="/login">Log in</Link>
          </p>
        </div>

        <aside className={styles.quietPane} aria-label="How HerSpace handles your information">
          <h2>Nothing is shared by default.</h2>
          <p>Your journal and moods are yours. No feeds, no stranger matching, no AI companion.</p>
          <p>You choose what to share, one request at a time.</p>
        </aside>
      </section>
    </div>
  );
}
