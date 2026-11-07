import { useState } from "react";

import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { InlineAlert } from "../../components/ui/InlineAlert";
import { useSession } from "../../hooks/useSession";
import { useToast } from "../../hooks/useToast";
import { authApi } from "../../services/auth";
import { maskEmail } from "../../utils/format";

export function VerificationGate() {
  const { user, refresh } = useSession();
  const { showToast } = useToast();
  const [sending, setSending] = useState(false);
  const [checking, setChecking] = useState(false);
  const [sent, setSent] = useState(false);

  async function resend() {
    setSending(true);
    try {
      const result = await authApi.resendVerification();
      if (result.sent) {
        setSent(true);
        showToast("Verification link sent.");
      } else {
        await refresh();
      }
    } catch {
      showToast("We couldn't send the link. Try again in a minute.", { tone: "error" });
    } finally {
      setSending(false);
    }
  }

  async function checkVerified() {
    setChecking(true);
    try {
      const result = await refresh();
      if (result?.data?.user?.emailVerified) {
        showToast("Email verified. Welcome in.");
      } else {
        showToast("We don't see verification yet. Open the link, then try again.", {
          tone: "info",
        });
      }
    } finally {
      setChecking(false);
    }
  }

  return (
    <Card>
      <h1 style={{ fontSize: "var(--text-h2)", lineHeight: "var(--text-h2-line)" }}>
        Verify your email to continue
      </h1>
      <div className="stack" style={{ marginTop: "var(--space-4)" }}>
        <InlineAlert tone="warning">
          We sent a verification link to <strong>{maskEmail(user?.email)}</strong>. Open it, then
          come back here.
        </InlineAlert>
        <p className="text-muted">
          This keeps your account recoverable and your private modules locked until the address is
          confirmed.
        </p>
        <div className="cluster">
          <Button onClick={checkVerified} loading={checking}>
            I&apos;ve verified my email
          </Button>
          <Button variant="secondary" onClick={resend} loading={sending} disabled={sent}>
            {sent ? "Link sent" : "Resend link"}
          </Button>
        </div>
      </div>
    </Card>
  );
}
