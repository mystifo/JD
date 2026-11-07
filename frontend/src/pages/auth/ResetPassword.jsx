import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { InlineAlert } from "../../components/ui/InlineAlert";
import { TextField } from "../../components/ui/TextField";
import { authApi } from "../../services/auth";
import { passwordChecks, resetPasswordSchema } from "../../services/schemas";
import { applyFieldErrors } from "../../utils/formErrors";

import styles from "./auth.module.css";
import shared from "./authShared.module.css";

const checklist = [
  ["length", "At least 12 characters"],
  ["notCommon", "Not a common password"],
  ["notNumeric", "Not only numbers"],
];

const failureMessages = {
  token_expired: "This link has expired. Request a new one.",
  token_used: "This link has already been used. Request a new one.",
  token_invalid: "This link isn't valid. Request a new one.",
};

export default function ResetPassword() {
  const { token } = useParams();
  const [tokenProblem, setTokenProblem] = useState(token ? "" : "token_invalid");
  const [success, setSuccess] = useState(false);
  const [formError, setFormError] = useState("");
  const {
    register,
    handleSubmit,
    watch,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { newPassword: "", confirmPassword: "" },
  });

  const newPassword = watch("newPassword");
  const checks = passwordChecks(newPassword);

  async function onSubmit(values) {
    setFormError("");
    try {
      await authApi.confirmPasswordReset({ token, newPassword: values.newPassword });
      setSuccess(true);
    } catch (error) {
      if (["token_expired", "token_used", "token_invalid"].includes(error.code)) {
        setTokenProblem(error.code);
        return;
      }
      const extras = applyFieldErrors(error, setError, {
        new_password: "newPassword",
        token: "newPassword",
      });
      if (extras.length) setFormError(extras[0]);
      else if (!Object.keys(error.fields ?? {}).length) setFormError(error.message);
    }
  }

  if (tokenProblem) {
    return (
      <div className={styles.page}>
        <section className={styles.card} aria-labelledby="reset-expired-title">
          <h1 id="reset-expired-title" className={styles.title}>
            This link can&apos;t be used
          </h1>
          <p className={styles.lede}>{failureMessages[tokenProblem] ?? failureMessages.token_invalid}</p>
          <div className={styles.tokenState}>
            <Button as={Link} to="/forgot-password">
              Request a new link
            </Button>
          </div>
        </section>
      </div>
    );
  }

  if (success) {
    return (
      <div className={styles.page}>
        <section className={styles.card} aria-labelledby="reset-done-title">
          <h1 id="reset-done-title" className={styles.title}>
            Password changed
          </h1>
          <p className={styles.lede}>Every other session has been signed out.</p>
          <div className={styles.tokenState}>
            <Button as={Link} to="/login">
              Log in with your new password
            </Button>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <section className={styles.card} aria-labelledby="reset-title">
        <h1 id="reset-title" className={styles.title}>
          Choose a new password
        </h1>
        <p className={styles.lede}>Choose something you don&apos;t use anywhere else.</p>

        <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
          {formError ? <InlineAlert tone="error">{formError}</InlineAlert> : null}
          <div>
            <TextField
              label="New password"
              type="password"
              autoComplete="new-password"
              required
              error={errors.newPassword?.message}
              {...register("newPassword")}
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
          <TextField
            label="Confirm new password"
            type="password"
            autoComplete="new-password"
            required
            error={errors.confirmPassword?.message}
            {...register("confirmPassword")}
          />
          <div className={styles.actions}>
            <Button type="submit" loading={isSubmitting} fullWidth>
              Save new password
            </Button>
          </div>
        </form>

        <p className={shared.switchLine}>
          <Link to="/login">Back to log in</Link>
        </p>
      </section>
    </div>
  );
}
