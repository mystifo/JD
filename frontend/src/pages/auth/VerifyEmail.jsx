import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { InlineAlert } from "../../components/ui/InlineAlert";
import { useSession } from "../../hooks/useSession";
import { useToast } from "../../hooks/useToast";
import { authApi } from "../../services/auth";

import styles from "./auth.module.css";

const failureMessages = {
  token_expired: "This verification link has expired.",
  token_used: "This verification link has already been used.",
  token_invalid: "This verification link isn't valid.",
};

export default function VerifyEmail() {
  const { token } = useParams();
  const navigate = useNavigate();
  const { signIn, user } = useSession();
  const { showToast } = useToast();
  const [state, setState] = useState("verifying");
  const [errorCode, setErrorCode] = useState("");
  const [destination, setDestination] = useState("/login?verified=1");
  const [resending, setResending] = useState(false);
  const [sent, setSent] = useState(false);
  const flowRef = useRef(null);
  const timerRef = useRef(null);

  const runVerification = useCallback(async () => {
    if (!token) {
      const error = new Error("This verification link isn't valid.");
      error.code = "token_invalid";
      throw error;
    }
    await authApi.verifyEmail(token);
    let target = "/login?verified=1";
    try {
      const session = await authApi.getSession();
      signIn(session);
      if (session.deletionScheduledFor) target = "/app/settings/delete";
      else if (session.onboardingRequired) target = "/onboarding/profile";
      else target = "/app";
    } catch {
      // Verification is public; an anonymous visitor logs in afterwards.
    }
    return { destination: target };
  }, [signIn, token]);

  useEffect(() => {
    if (!flowRef.current) flowRef.current = runVerification();
    let active = true;

    flowRef.current
      .then((result) => {
        if (!active) return;
        setDestination(result.destination);
        setState("success");
        timerRef.current = window.setTimeout(() => {
          navigate(result.destination, { replace: true });
        }, 1200);
      })
      .catch((error) => {
        if (!active) return;
        setErrorCode(error.code ?? "token_invalid");
        setState("failure");
      });

    return () => {
      active = false;
      if (timerRef.current) window.clearTimeout(timerRef.current);
    };
  }, [navigate, runVerification]);

  function continueNow() {
    if (timerRef.current) window.clearTimeout(timerRef.current);
    navigate(destination, { replace: true });
  }

  async function resend() {
    setResending(true);
    try {
      await authApi.resendVerification();
      setSent(true);
      showToast("Verification link sent.");
    } catch {
      showToast("We couldn't send the link. Try again in a minute.", { tone: "error" });
    } finally {
      setResending(false);
    }
  }

  return (
    <div className={styles.page}>
      <section className={styles.card} aria-labelledby="verify-title">
        <h1 id="verify-title" className={styles.title}>
          {state === "verifying" ? "Verifying your email" : null}
          {state === "success" ? "Your email is verified" : null}
          {state === "failure" ? "We couldn't verify this link" : null}
        </h1>

        {state === "verifying" ? (
          <p className={styles.lede} role="status">
            One moment while we check the link.
          </p>
        ) : null}

        {state === "success" ? (
          <div className={styles.tokenState}>
            <InlineAlert tone="success">
              Your space is unlocked. Taking you there now.
            </InlineAlert>
            <Button onClick={continueNow}>Continue</Button>
          </div>
        ) : null}

        {state === "failure" ? (
          <div className={styles.tokenState}>
            <InlineAlert tone="error">
              {failureMessages[errorCode] ?? "This verification link isn't valid."}
            </InlineAlert>
            {user && !user.emailVerified ? (
              <Button onClick={resend} loading={resending} disabled={sent} variant="secondary">
                {sent ? "Link sent" : "Send a new link"}
              </Button>
            ) : (
              <p className={styles.lede}>
                Log in and use the resend link on the verification banner.
              </p>
            )}
            <Button as={Link} to="/login" variant="ghost">
              Back to log in
            </Button>
          </div>
        ) : null}
      </section>
    </div>
  );
}
