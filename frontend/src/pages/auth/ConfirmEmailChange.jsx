import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { InlineAlert } from "../../components/ui/InlineAlert";
import { useSession } from "../../hooks/useSession";
import { authApi } from "../../services/auth";

import styles from "./auth.module.css";

const failureMessages = {
  token_expired: "This link has expired.",
  token_used: "This link has already been used.",
  token_invalid: "This link isn't valid.",
  email_in_use: "That address was claimed by another account in the meantime.",
};

export default function ConfirmEmailChange() {
  const { token } = useParams();
  const { status, signIn, refresh } = useSession();
  const [state, setState] = useState("confirming");
  const [errorCode, setErrorCode] = useState("");
  const [email, setEmail] = useState("");
  const flowRef = useRef(null);

  const runConfirmation = useCallback(async () => {
    if (!token) {
      const error = new Error("This link isn't valid.");
      error.code = "token_invalid";
      throw error;
    }
    const result = await authApi.confirmEmailChange(token);
    try {
      const session = await authApi.getSession();
      signIn(session);
    } catch {
      await refresh();
    }
    return result;
  }, [refresh, signIn, token]);

  useEffect(() => {
    if (!flowRef.current) flowRef.current = runConfirmation();
    let active = true;

    flowRef.current
      .then((result) => {
        if (!active) return;
        setEmail(result.email);
        setState("success");
      })
      .catch((error) => {
        if (!active) return;
        setErrorCode(error.code ?? "token_invalid");
        setState("failure");
      });

    return () => {
      active = false;
    };
  }, [runConfirmation]);

  const authenticated = status === "authenticated";

  return (
    <div className={styles.page}>
      <section className={styles.card} aria-labelledby="confirm-email-title">
        <h1 id="confirm-email-title" className={styles.title}>
          {state === "confirming" ? "Confirming your new email" : null}
          {state === "success" ? "Your email is updated" : null}
          {state === "failure" ? "We couldn't update your email" : null}
        </h1>

        {state === "confirming" ? (
          <p className={styles.lede} role="status">
            One moment while we check the link.
          </p>
        ) : null}

        {state === "success" ? (
          <div className={styles.tokenState}>
            <InlineAlert tone="success">
              Your account now uses <strong>{email}</strong> for sign-in and security notices.
            </InlineAlert>
            <Button as={Link} to={authenticated ? "/app/settings/profile" : "/login"}>
              {authenticated ? "Go to settings" : "Log in"}
            </Button>
          </div>
        ) : null}

        {state === "failure" ? (
          <div className={styles.tokenState}>
            <InlineAlert tone="error">
              {failureMessages[errorCode] ?? "This link isn't valid."}
            </InlineAlert>
            <p className={styles.lede}>
              The address on your account has not changed. Request a new link from Settings.
            </p>
            <Button
              as={Link}
              to={authenticated ? "/app/settings/profile" : "/login"}
              variant="secondary"
            >
              {authenticated ? "Open Settings" : "Back to log in"}
            </Button>
          </div>
        ) : null}
      </section>
    </div>
  );
}
