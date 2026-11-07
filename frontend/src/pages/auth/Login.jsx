import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { InlineAlert } from "../../components/ui/InlineAlert";
import { TextField } from "../../components/ui/TextField";
import { useSession } from "../../hooks/useSession";
import { authApi } from "../../services/auth";
import { loginSchema } from "../../services/schemas";
import { applyFieldErrors } from "../../utils/formErrors";
import { safeRedirect } from "../../utils/redirect";

import styles from "./auth.module.css";
import shared from "./authShared.module.css";

function formatCountdown(seconds) {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${minutes}:${String(rest).padStart(2, "0")}`;
}

export default function Login() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { signIn } = useSession();
  const [formError, setFormError] = useState("");
  const [lockSeconds, setLockSeconds] = useState(0);
  const next = params.get("next");
  const verified = params.get("verified") === "1";

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: params.get("email") ?? "",
      password: "",
    },
  });

  useEffect(() => {
    if (lockSeconds <= 0) return undefined;
    const timer = window.setTimeout(() => setLockSeconds((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearTimeout(timer);
  }, [lockSeconds]);

  async function onSubmit(values) {
    setFormError("");
    setLockSeconds(0);
    try {
      const session = await authApi.login(values);
      signIn(session);
      if (session.deletionScheduledFor) {
        navigate("/app/settings/delete", { replace: true });
      } else if (session.onboardingRequired) {
        navigate("/onboarding/profile", { replace: true });
      } else {
        navigate(safeRedirect(next, "/app"), { replace: true });
      }
    } catch (error) {
      if (error.code === "account_locked" || error.status === 423) {
        setLockSeconds(Number(error.fields?.retry_after_seconds ?? 60));
        setFormError(error.message);
        return;
      }
      if (error.code === "deletion_pending") {
        setFormError(error.message);
        return;
      }
      const extras = applyFieldErrors(error, setError, {});
      if (error.status === 401) {
        setFormError("That email and password don't match.");
      } else if (extras.length) {
        setFormError(extras[0]);
      } else if (!Object.keys(error.fields ?? {}).length) {
        setFormError(error.message);
      }
    }
  }

  return (
    <div className={styles.page}>
      <section className={styles.card} aria-labelledby="login-title">
        <h1 id="login-title" className={styles.title}>
          Welcome back
        </h1>
        <p className={styles.lede}>Your space is where you left it.</p>

        {verified ? (
          <InlineAlert tone="success" title="Email verified" className={shared.formError}>
            Log in to continue setting up your space.
          </InlineAlert>
        ) : null}

        <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
          {formError ? (
            <InlineAlert tone="error" title={lockSeconds > 0 ? "Too many attempts" : undefined}>
              {lockSeconds > 0
                ? `${formError} Try again in ${formatCountdown(lockSeconds)}.`
                : formError}
            </InlineAlert>
          ) : null}

          <TextField
            label="Email"
            type="email"
            autoComplete="email"
            required
            error={errors.email?.message}
            {...register("email")}
          />
          <TextField
            label="Password"
            type="password"
            autoComplete="current-password"
            required
            error={errors.password?.message}
            {...register("password")}
          />

          <div className={styles.links}>
            <Link to="/forgot-password">Forgot password?</Link>
          </div>

          <div className={styles.actions}>
            <Button type="submit" loading={isSubmitting} disabled={lockSeconds > 0} fullWidth>
              Log in
            </Button>
          </div>
        </form>

        <p className={shared.switchLine}>
          New here? <Link to="/register">Create your space</Link>
        </p>
      </section>
    </div>
  );
}
