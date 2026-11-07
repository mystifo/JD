import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { InlineAlert } from "../../components/ui/InlineAlert";
import { TextField } from "../../components/ui/TextField";
import { authApi } from "../../services/auth";
import { forgotPasswordSchema } from "../../services/schemas";
import { applyFieldErrors } from "../../utils/formErrors";

import styles from "./auth.module.css";
import shared from "./authShared.module.css";

export default function ForgotPassword() {
  const [submitted, setSubmitted] = useState(false);
  const [formError, setFormError] = useState("");
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: "" },
  });

  async function onSubmit(values) {
    setFormError("");
    try {
      await authApi.requestPasswordReset(values.email);
      setSubmitted(true);
    } catch (error) {
      const extras = applyFieldErrors(error, setError, {});
      if (error.status === 429) {
        setFormError("Too many attempts. Please try again later.");
      } else if (extras.length) {
        setFormError(extras[0]);
      } else {
        setFormError(error.message);
      }
    }
  }

  if (submitted) {
    return (
      <div className={styles.page}>
        <section className={styles.card} aria-labelledby="reset-sent-title">
          <h1 id="reset-sent-title" className={styles.title}>
            Check your inbox
          </h1>
          <p className={styles.lede}>
            If that address has an account, a reset link is on its way.
          </p>
          <div className={styles.tokenState}>
            <p>The link expires in 60 minutes and can be used once.</p>
            <Button as={Link} to="/login" variant="secondary">
              Back to log in
            </Button>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <section className={styles.card} aria-labelledby="forgot-title">
        <h1 id="forgot-title" className={styles.title}>
          Forgot your password?
        </h1>
        <p className={styles.lede}>
          Enter your email and we&apos;ll send a link to choose a new one.
        </p>

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
          <div className={styles.actions}>
            <Button type="submit" loading={isSubmitting} fullWidth>
              Send a reset link
            </Button>
          </div>
        </form>

        <p className={shared.switchLine}>
          Remembered it? <Link to="/login">Back to log in</Link>
        </p>
      </section>
    </div>
  );
}
