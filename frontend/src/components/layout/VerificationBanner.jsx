import { useState } from "react";

import { useSession } from "../../hooks/useSession";
import { useToast } from "../../hooks/useToast";
import { authApi } from "../../services/auth";
import { Button } from "../ui/Button";
import { InlineAlert } from "../ui/InlineAlert";

export function VerificationBanner() {
  const { user, refresh } = useSession();
  const { showToast } = useToast();
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  if (!user || user.emailVerified) return null;

  async function resend() {
    setSending(true);
    try {
      const result = await authApi.resendVerification();
      if (result.sent) {
        setSent(true);
        showToast("Verification link sent.");
      } else {
        // Already verified in another tab: pick up the fresh session.
        await refresh();
      }
    } catch {
      showToast("We couldn't send the link. Try again in a minute.", { tone: "error" });
    } finally {
      setSending(false);
    }
  }

  return (
    <InlineAlert
      tone="warning"
      title="Verify your email to unlock your space"
      action={
        <Button size="sm" variant="secondary" onClick={resend} loading={sending} disabled={sent}>
          {sent ? "Link sent" : "Resend link"}
        </Button>
      }
    >
      Check your inbox for the link we sent to <strong>{user.email}</strong>.
    </InlineAlert>
  );
}
