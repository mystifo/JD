# HerSpace — User Stories and Acceptance Criteria

| Field | Value |
|---|---|
| Document ID | HS-US-001 |
| Version | 1.0 |
| Date | 2026-10-31 |
| Traces to | `requirements.md` (FR/BR/NFR IDs) |
| Consumed by | `api-documentation.md`, `wireframes.md`, `roadmap.md` (test gates) |

**Conventions**
- Every story is owned by exactly one actor and maps to ≥1 FR.
- Acceptance criteria use Given/When/Then and are written so they can become automated tests verbatim.
- `404` in an AC always means "not found for this caller", per BR-03.
- Story IDs match the traceability table in `requirements.md` §10.

---

## Epic A — Authentication and account lifecycle

### US-A1 — Register with consent
**As** a visitor **I want** to create an account with my email and a strong password **so that** my private space is protected.
**Priority** M · **FR** FR-AUTH-01, FR-AUTH-02 · **BR** BR-15

**Acceptance criteria**
1. Given a valid email, a 12+ character password, and both Terms and Privacy checkboxes ticked, when I submit the form, then a user is created, two `ConsentRecord` rows exist for `terms_of_service` and `privacy_policy` with `policy_version` = current, and the response is `201` with no password hash.
2. Given an email that already exists, when I submit, then the response is `409` with code `email_in_use` and no user is created.
3. Given an unchecked required consent, when I submit, then the response is `400` with `fields.consents` and no user is created.
4. Given a password shorter than 12 characters or in the common-password list, when I submit, then the response is `400` with `fields.password` and a human-readable reason.
5. Given a successful registration, when the transaction commits, then exactly one verification email is dispatched **after** commit and contains no personal content beyond a greeting.

### US-A2 — Verify email
**As** a new user **I want** to verify my email **so that** I can use my private space fully.
**Priority** M · **FR** FR-AUTH-03, FR-AUTH-04, FR-AUTH-05

**Acceptance criteria**
1. Given a valid unexpired token, when I open `/verify-email/:token`, then `email_verified_at` is set, the token is marked used, and I am redirected to onboarding (or the dashboard if onboarding is complete).
2. Given an expired token, when I open the link, then I see a recovery screen with a "send a new link" action and the response is `410 token_expired`.
3. Given a token already used, when I open the link, then I see "This link has already been used" and no state changes.
4. Given I request a resend more than 3 times in an hour, then the response is `429 rate_limited`.
5. Given I am unverified and logged in, when I call `GET /api/v1/journal/`, then the response is `403 email_not_verified`.

### US-A3 — Log in
**As** a returning user **I want** to log in **so that** I can reach my space.
**Priority** M · **FR** FR-AUTH-06, FR-AUTH-07, FR-AUTH-12

**Acceptance criteria**
1. Given correct credentials, when I submit, then a session cookie is set (`HttpOnly`, `SameSite=Lax`, `Secure` in prod), the CSRF cookie is readable by JS, and the response is `200` with my profile summary and `email_verified` flag.
2. Given a wrong password, when I submit, then the response is `401 invalid_credentials` with the same body shape and timing class as an unknown email.
3. Given 10 consecutive failures for one account, when I try an 11th time, then the response is `423 account_locked` and `locked_until` is 15 minutes ahead.
4. Given a successful login after failures, then `failed_login_count` resets to 0.
5. Given a session idle for 12 hours, when I make a request, then I am unauthenticated and the SPA routes to `/login?next=`.

### US-A4 — Log out / log out everywhere
**As** a user **I want** to end my sessions **so that** my space is safe on shared devices.
**Priority** M · **FR** FR-AUTH-08

**Acceptance criteria**
1. Given a session, when I `POST /api/v1/auth/logout/`, then the session is destroyed, the cookie is cleared, and a subsequent private request returns `401`.
2. Given multiple sessions, when I log out everywhere, then all other sessions are invalidated and I receive a security notification.

### US-A5 — Request a password reset without leaking accounts
**As** a user who forgot her password **I want** a reset link **so that** I can regain access.
**Priority** M · **FR** FR-AUTH-09, FR-AUTH-10 · **BR** BR-15

**Acceptance criteria**
1. Given any email string, when I submit the reset form, then the response is `202` with the identical message and shape, regardless of account existence.
2. Given an existing account, then exactly one email is sent and its token is stored only as a hash.
3. Given 4 requests in an hour for one email, then the response is `429` but still visually neutral.
4. Given a token older than 60 minutes, when I submit a new password, then the response is `410 token_expired` and the password is unchanged.
5. Given a successful reset, then all sessions are invalidated and a security notification plus audit event are created.

### US-A6 — Change password while logged in
**As** a user **I want** to change my password **so that** I can rotate a compromised credential.
**Priority** M · **FR** FR-AUTH-11

**Acceptance criteria**
1. Given the correct current password and a valid new password, when I submit, then the hash changes, all other sessions end, and I stay logged in on the current session.
2. Given a wrong current password, then `400` with `fields.current_password` and no change.
3. Given the new password equals the old one, then `400` with `fields.new_password`.

### US-A7 — Read security notices
**As** a user **I want** to see security-relevant events **so that** I notice unauthorised access.
**Priority** H · **FR** FR-AUTH-13, FR-NOTF-01

**Acceptance criteria**
1. Given a password change, reset, or new-device login, then an in-app notification of category `security_alert` exists without any content from private records.
2. Given a security notification, when I open it, then I see timestamp, event type, and a "this wasn't me" guidance link to reset password and delete account.

### US-A8 — Delete account
**As** a user **I want** to delete my account **so that** my data is gone when I choose to leave.
**Priority** M · **FR** FR-PRIV-05, FR-PRIV-06, FR-PRIV-07 · **BR** BR-16

**Acceptance criteria**
1. Given I confirm with my password and type `DELETE`, when I submit, then an `AccountDeletionRequest` is created with `scheduled_for = now + 7 days`, my account is deactivated, all other sessions end, the requesting session is restricted to cancellation/logout, and a cancellation link is emailed.
2. Given a scheduled deletion, when I try to log in, then I see a "deletion scheduled" screen with the date and instructions to use the emailed cancellation link, and no private endpoint is reachable.
3. Given the grace period has passed, when the purge job runs, then the user row and all cascading personal rows are gone, export files are deleted, and the audit trail retains only pseudonymous events.
4. Given I cancel via the emailed token before the deadline, then the request is `cancelled`, the account is reactivated, and I can log in again.
5. Given an export is `queued` or `processing`, when I request deletion, then `409 export_in_progress`.

---

## Epic P — Profile, preferences, onboarding

### US-P1 — Set up my profile
**As** a new user **I want** to set my name and timezone **so that** dates and greetings are correct.
**Priority** M · **FR** FR-PROF-01

**Acceptance criteria**
1. Given I submit a display name of 1–80 characters and an IANA timezone, then `PATCH /api/v1/profile/` returns `200` and the change is reflected in the header greeting.
2. Given an invalid timezone, then `400` with `fields.timezone` listing the accepted format.
3. Given an empty display name, then `400` with `fields.display_name`.
4. Given a bio longer than 280 characters, then `400` with `fields.bio`.

### US-P2 — Choose how the space looks
**As** a user **I want** to choose light/dark/system and reduced motion **so that** the space feels comfortable.
**Priority** H · **FR** FR-PROF-03 · **NFR-A11Y-05**

**Acceptance criteria**
1. Given I choose `dark`, then the preference is persisted server-side and applied on next load before first paint (no flash of light theme).
2. Given `system`, then the UI follows `prefers-color-scheme` and updates live when the OS changes.
3. Given reduced motion is on, then breathing animation uses a static progress indicator and page transitions are disabled.
4. Given I change theme, then no API request is made per component render (one PATCH per change, debounced).

### US-P3 — Complete onboarding
**As** a new user **I want** a short guided setup **so that** the space is ready without configuration overload.
**Priority** M · **FR** FR-PROF-04, FR-PROF-05

**Acceptance criteria**
1. Given a verified user with no `onboarding_completed_at`, when I open `/app`, then I am redirected to `/onboarding/profile`.
2. Given I complete or skip steps 1–4 and acknowledge the privacy explanation in step 5, then `onboarding_completed_at` is set and I land on the dashboard.
3. Given I skip the trusted-contact step, then the dashboard shows the "Add someone you trust" empty-state card once, dismissible.
4. Given I refresh mid-onboarding, then I resume at the first incomplete step, not step 1.

### US-P4 — Control dashboard suggestions
**As** a user **I want** to dismiss suggestions **so that** the dashboard stays calm.
**Priority** D · **FR** FR-PROF-06

**Acceptance criteria**
1. Given a visible suggestion, when I dismiss it, then its key is stored in preferences and it does not reappear.
2. Given all suggestions dismissed, then the dashboard shows only my data modules and no nagging.

---

## Epic W — Emotional wellness

### US-W1 — Record a check-in
**As** a user **I want** to record how I feel today **so that** I can understand my emotional patterns over time.
**Priority** M · **FR** FR-WELL-01, FR-WELL-02 · **BR** BR-01

**Acceptance criteria**
1. Given I select 1–12 emotions, set intensity 1–10, and optionally add a note ≤2000 characters and triggers, when I save, then a `MoodEntry` exists for today's local date with all selected emotions linked.
2. Given I already checked in today, when I open the check-in page, then the existing values are pre-filled and saving updates the same record (`200`), not a duplicate.
3. Given I select zero emotions, then `400` with `fields.emotions`.
4. Given intensity 0 or 11, then `400` with `fields.intensity`.
5. Given a note of 2001 characters, then `400` with `fields.note`.
6. Given a saved check-in, then the dashboard card shows "Today's check-in saved" with an edit action, and no streak counter appears anywhere.

### US-W2 — Browse mood history
**As** a user **I want** to browse past check-ins **so that** I can reflect without digging.
**Priority** M · **FR** FR-WELL-03 · **NFR-PERF-04**

**Acceptance criteria**
1. Given 45 check-ins, when I open history, then 20 are shown with a "load more" control and a total count.
2. Given I filter by emotion `anxious` and a date range, then only matching entries are returned and the filter state is in the URL.
3. Given no entries in range, then an empty state explains how to record one and never says "you missed days".
4. Given another user's entry id, then `GET /api/v1/moods/{id}/` returns `404`.

### US-W3 — See my month at a glance
**As** a user **I want** a calendar of my month **so that** I can see rhythm without judgement.
**Priority** H · **FR** FR-WELL-04

**Acceptance criteria**
1. Given a month with data, then each day cell shows intensity via a colour step and up to 3 emotion labels, with an accessible text summary (`aria-label`).
2. Given days without data, then they render as neutral "no check-in" cells, visually quieter than recorded days.
3. Given keyboard use, then arrow keys move between days, Enter opens the day, and focus is always visible.
4. Given a month with no data, then an empty state offers "record today" and does not render an alarming grid.

### US-W4 — Edit or delete a check-in
**As** a user **I want** to correct or remove a check-in **so that** my record stays accurate.
**Priority** M · **FR** FR-WELL-05

**Acceptance criteria**
1. Given my entry, when I `PATCH` intensity and emotions, then the record and its emotion links reflect the change and `updated_at` advances.
2. Given my entry, when I delete and confirm, then it is removed permanently, its join rows cascade, and support requests referencing it show "shared entry no longer available".
3. Given a linked journal entry, deleting the mood entry does not delete the journal entry (`SET_NULL`).

### US-W5 — Manage triggers
**As** a user **I want** my own trigger list **so that** recording is faster and more honest.
**Priority** H · **FR** FR-WELL-06

**Acceptance criteria**
1. Given I add "lack of sleep", then it appears in the check-in trigger picker.
2. Given I add a duplicate name with different case, then `409 duplicate_trigger`.
3. Given I delete a trigger, then historical check-ins keep their other data and the trigger link is removed.

### US-W6 — Weekly and monthly summary
**As** a user **I want** a summary of my week and month **so that** I can notice patterns gently.
**Priority** H · **FR** FR-WELL-07, FR-INSN-01..04 · **BR** BR-12

**Acceptance criteria**
1. Given 5 check-ins in the week, then the summary shows count, average intensity (1 decimal), top 3 emotions with counts, and descriptive statements each citing a count.
2. Given 2 check-ins, then the summary shows "Not enough data yet — a few more check-ins will make this meaningful" and no trend.
3. Given any data, then no statement contains diagnostic, causal, or predictive wording (checked against the banned-phrase list in `security.md` §13).
4. Given a timezone change mid-week, then days are grouped by stored `local_date`, not recomputed.

### US-W7 — Share a check-in deliberately
**As** a user **I want** to attach a check-in to a support request **so that** a trusted person understands quickly.
**Priority** M · **FR** FR-WELL-09, FR-CONN-10 · **BR** BR-05

**Acceptance criteria**
1. Given I attach today's check-in, then a consent record scoped to that request is created in the same transaction.
2. Given I do not attach anything, then no consent record of type `support_request_sharing` is created.
3. Given I later revoke the share, then the mood section of the recipient page shows "This was withdrawn" and no mood values, while any other active share remains visible.

---

## Epic C — Human connection

### US-C1 — Add a trusted contact
**As** a user **I want** to add someone I trust **so that** I have a real person to reach.
**Priority** M · **FR** FR-CONN-01, FR-CONN-02

**Acceptance criteria**
1. Given a name and at least one of email/phone, when I save, then the contact exists with status `draft` and appears in My People.
2. Given neither email nor phone, then I can still save a `draft` but the invite action is disabled with an explanation.
3. Given an email already used by another contact of mine, then `409 duplicate_contact` with a link to the existing contact.
4. Given a phone in an invalid format, then `400` with `fields.phone`.

### US-C2 — Invite a contact
**As** a user **I want** to invite someone **so that** they know I've chosen them and can agree.
**Priority** M · **FR** FR-CONN-03, FR-CONN-04 · **BR** BR-15

**Acceptance criteria**
1. Given a contact with an email and channel `email`, when I send, then a `ContactInvitation` with a hashed token is created, status becomes `invited`, and the email is dispatched after commit.
2. Given channel `whatsapp`, then no server-side message is sent; I get a prefilled deep link and a copyable message, and status becomes `invited` only after I confirm "I sent it".
3. Given channel `manual_link`, then I receive a link valid for 7 days with a copy button.
4. Given a second invite within 60 minutes, then `429 invite_throttled`.
5. Given the link, then the public page shows only my display name, the relationship label, and the invitation text — never any mood or journal data.

### US-C3 — Respond to an invitation
**As** an invited person **I want** to accept or decline **so that** my consent is explicit.
**Priority** M · **FR** FR-CONN-05, FR-CONN-06

**Acceptance criteria**
1. Given a valid token, when I open the page, then I see who invited me, what being a trusted contact means, and Accept / Decline.
2. Given I accept, then status is `active`, `responded_at` is set, a consent record with `consent_type='contact_invitation'` and `scope_id` = contact id exists, and the Owner gets an in-app notification.
3. Given I decline, then status is `declined`, the Owner is notified without pressure copy, and the token cannot be reused.
4. Given an expired token, then `410 token_expired` with no state change.
5. Given I respond twice, then the second attempt returns `409 already_responded`.

### US-C4 — Manage invitations
**As** a user **I want** to resend or revoke an invitation **so that** I stay in control.
**Priority** H · **FR** FR-CONN-07

**Acceptance criteria**
1. Given a `sent` invitation older than 60 minutes, when I resend, then a new token replaces the old one and the old link returns `410`.
2. Given I revoke, then status is `revoked`, the link returns `410`, and the contact returns to `draft`.
3. Given invitations list, then each row shows channel, sent date, expiry, and status truthfully.

### US-C5 — Organise my people
**As** a user **I want** favourites and clean records **so that** the right person is easy to find in a hard moment.
**Priority** M · **FR** FR-CONN-08 · **BR** BR-19

**Acceptance criteria**
1. Given I favourite a contact, then it sorts first in the support-request picker.
2. Given I delete a contact with support history, then history remains with the name snapshot and the detail page shows "contact removed".
3. Given a contact is `declined` or `revoked`, then the support-request picker excludes them and explains why.
4. Given a contact is `invited` but not `active`, then the picker allows sending with a clear "they haven't responded to your invitation yet" warning.

### US-C6 — Ask for support
**As** a user having a hard moment **I want** to ask one trusted person for a specific kind of support **so that** I don't have to explain everything from scratch.
**Priority** M · **FR** FR-CONN-09..FR-CONN-11 · **BR** BR-04, BR-07

**Acceptance criteria**
1. Given I pick an active contact and support type `listen` and send, then a `SupportRequest` is `pending`, `sent_at` is set, a response token is created, and delivery is attempted on the chosen channel.
2. Given the request page, then it shows "Waiting for a response" with the exact sent time and expiry time, and never "on the way" or "will respond".
3. Given I select a journal entry to share, then I must tick a per-item consent checkbox and the API rejects the request without `consent_confirmed` (`400 consent_required`).
4. Given I select a mood entry not owned by me, then `400 fields.shared_mood_entry`.
5. Given the request is created, then a notification and audit event exist, and the journal/mood text is absent from both.

### US-C7 — Respond to a support request
**As** a trusted contact **I want** to accept or decline quickly **so that** the person knows where I stand.
**Priority** M · **FR** FR-CONN-14 · **BR** BR-08

**Acceptance criteria**
1. Given a valid unexpired token, then the page shows the support type, the optional message, and any explicitly shared snapshot — nothing else.
2. Given I accept, then status is `accepted`, `responded_at` is set, `response_verified=false`, and the Owner is notified in-app and by email (if enabled).
3. Given I decline, then status is `declined` with an optional note ≤500 characters.
4. Given an expired token, then `410 token_expired` and the page offers nothing to submit.
5. Given a share was revoked, then the snapshot area shows "This was withdrawn by the sender".

### US-C8 — See what happened
**As** a user **I want** to see request status and history **so that** I am not left guessing.
**Priority** M · **FR** FR-CONN-15

**Acceptance criteria**
1. Given requests exist, then history lists contact snapshot name, type, status, sent time, and response time.
2. Given `accepted`, then the response note is visible with a "via link" badge when `response_verified=false`.
3. Given `pending`, then the detail page offers "cancel request" and "send to someone else" (creating a new request, not mutating the old one).
4. Given another user's request id, then `404`.

### US-C9 — Handle silence honestly
**As** a user whose request expired or was declined **I want** alternatives **so that** I am not left with nothing.
**Priority** M · **FR** FR-CONN-16, FR-CONN-12 · **BR** BR-09

**Acceptance criteria**
1. Given a request expires, then it becomes `expired`, a notification is created, and the detail page shows: "No response yet. You can reach someone else, or use these support resources."
2. Given the alternatives block, then it lists other active/favourite contacts (if any) and 2–3 external resources from the support-resource table.
3. Given no other contacts, then only the resources block is shown with no implication of failure.

### US-C10 — Withdraw a share
**As** a user **I want** to withdraw shared content **so that** my privacy is not permanent.
**Priority** H · **FR** FR-CONN-17 · **BR** BR-05

**Acceptance criteria**
1. Given an accepted request with a shared journal snapshot, when I revoke, then the consent record is revoked once no shares remain, the snapshot is deleted, and the recipient page shows a withdrawal notice.
2. Given revocation, then the request status is unchanged and an audit event is recorded.
3. Given the recipient already viewed it, then the UI states plainly that earlier viewing cannot be undone.

---

## Epic J — Private journal

### US-J1 — Write an entry
**As** a user **I want** to write privately **so that** I can process what I feel.
**Priority** M · **FR** FR-JRNL-01, FR-JRNL-06

**Acceptance criteria**
1. Given a title, content, category, and date, when I save, then an entry is created with server-computed `word_count` and appears at the top of my journal list.
2. Given an empty title or empty content, then `400` with the corresponding field.
3. Given content of 20,001 characters, then `400` with `fields.content` and a character counter shown in the UI.
4. Given autosave every 20 seconds while dirty, then a draft is not created until I explicitly save; the UI warns on navigation away with unsaved changes.

### US-J2 — Read and organise
**As** a user **I want** to browse and filter entries **so that** I can find a memory.
**Priority** M · **FR** FR-JRNL-02, FR-JRNL-03

**Acceptance criteria**
1. Given 30 entries, then the list shows 20 with title, date, category, tags, and word count, but no content preview by default (privacy on shared screens).
2. Given a filter by category `gratitude`, then only gratitude entries are returned and the page heading reflects it.
3. Given another user's entry id, then `404` for GET, PATCH, and DELETE.

### US-J3 — Edit an entry
**As** a user **I want** to refine an entry **so that** it stays true to me.
**Priority** M · **FR** FR-JRNL-01

**Acceptance criteria**
1. Given my entry, when I save edits, then `updated_at` advances, `word_count` recomputes, and the list reflects the new title.
2. Given a concurrent edit from another tab, then the second save with a stale `updated_at` returns `409 edit_conflict` and the UI offers to reload.
3. Given edits to an entry already shared in a request, then the recipient's snapshot does not change.

### US-J4 — Delete an entry
**As** a user **I want** to delete an entry **so that** it no longer exists.
**Priority** M · **FR** FR-JRNL-08

**Acceptance criteria**
1. Given my entry, when I type `DELETE` and confirm, then it is removed, tag links cascade, and support-request references become "no longer available".
2. Given I cancel the dialog, then nothing is sent to the server.
3. Given a deleted id, then `GET` returns `404`.

### US-J5 — Search my journal
**As** a user **I want** to search my writing **so that** I can revisit a thought.
**Priority** M · **FR** FR-JRNL-04 · **NFR-PERF-05**

**Acceptance criteria**
1. Given the term "birthday" in two entries, when I search, then both are returned with highlighted match context, ordered by entry date descending.
2. Given a search with no results, then an empty state suggests removing filters, not "nothing here".
3. Given 5,000 entries, then p95 search ≤ 400 ms with the trigram index (verified by seeded benchmark test).
4. Given search input with `%` or `_`, then the query is treated literally and no error occurs.

### US-J6 — Use prompts and gratitude
**As** a user **I want** prompts and a gratitude view **so that** blank pages feel less heavy.
**Priority** H · **FR** FR-JRNL-05

**Acceptance criteria**
1. Given the prompts page, then prompts are grouped by category and "use this prompt" opens the editor with the prompt attached.
2. Given the gratitude page, then it filters category `gratitude` and offers a one-field quick add (title auto-filled with the date).
3. Given a prompt is deactivated by staff, then it disappears from the picker but remains on existing entries.

### US-J7 — Keep journal content out of everywhere else
**As** a user **I want** my writing to stay only where I put it **so that** I can be honest.
**Priority** M · **FR** FR-JRNL-07 · **BR** BR-10

**Acceptance criteria**
1. Given any API request containing journal text, then application logs, access logs, and error payloads contain no substring of that text (automated test with a sentinel string).
2. Given a support request that shares a journal entry, then the notification body contains only the contact name and support type.
3. Given an export, then journal content is present in the archive only, not in the notification or email.

---

## Epic S — Self-care routines

### US-S1 — Create a routine
**As** a user **I want** a routine that fits my real life **so that** self-care is not a rulebook.
**Priority** M · **FR** FR-SELF-01, FR-SELF-02

**Acceptance criteria**
1. Given a name, time of day, weekdays, and 1+ items, then the routine is created and shown in today's checklist when scheduled for today.
2. Given no weekdays selected, then `400 fields.days_of_week`.
3. Given 0 items, then the routine saves as a draft (`is_active=false`) and the UI explains why it isn't in today's list.
4. Given reminder enabled without a time, then `400 fields.reminder_time`.

### US-S2 — Edit and reorder
**As** a user **I want** to reorder and rename items **so that** the routine matches my morning.
**Priority** M · **FR** FR-SELF-01, FR-SELF-02

**Acceptance criteria**
1. Given a drag/keyboard reorder, then `sort_order` is persisted contiguously (0..n-1) in one transaction.
2. Given I deactivate a routine, then it leaves today's checklist but its history remains.
3. Given I delete a routine, then its completions cascade and the UI warns that history will be lost.

### US-S3 — Complete today's checklist
**As** a user **I want** to tick items off **so that** I can see what I did, not what I missed.
**Priority** M · **FR** FR-SELF-03, FR-SELF-07

**Acceptance criteria**
1. Given today's routine, when I tick an item, then a `RoutineDayCompletion` for today plus a `RoutineItemCompletion` exist and the progress ring updates optimistically with rollback on failure.
2. Given all items ticked, then the day is marked complete and a gentle confirmation appears ("Done for today") with no confetti or streak count.
3. Given a routine not scheduled today, then it appears under "Not scheduled today" and cannot be completed for today.
4. Given I untick, then the item completion is removed; if none remain, the day completion is removed.

### US-S4 — Review completion history
**As** a user **I want** to see how often I did a routine **so that** I can adjust it.
**Priority** H · **FR** FR-SELF-04

**Acceptance criteria**
1. Given a date range, then the history shows per-day completion state, items completed / total, and a period count.
2. Given a missed scheduled day, then it renders as "no entry", never as a red failure.
3. Given another user's routine id, then `404`.

### US-S5 — Undo a completion
**As** a user **I want** to undo an accidental tick **so that** my record is accurate.
**Priority** H · **FR** FR-SELF-06

**Acceptance criteria**
1. Given a completion for today or a past date, when I undo, then the day completion is deleted and the checklist reflects it.
2. Given the completion belongs to another user, then `404`.

### US-S6 — Optional reminders
**As** a user **I want** gentle reminders **so that** I remember without being pushed.
**Priority** H · **FR** FR-SELF-08 · **NFR-UX-01**

**Acceptance criteria**
1. Given reminders off (default), then no reminder notification is ever created.
2. Given a reminder time inside quiet hours, then it is suppressed and the UI says so when configuring.
3. Given a reminder fires, then the copy is invitational ("Your evening routine is here if you want it") and there is no "you missed" variant.

---

## Epic CALM — Calm Space

### US-CALM1 — Breathe with guidance
**As** a user **I want** a paced breathing exercise **so that** my body can settle.
**Priority** D · **FR** FR-CALM-01, FR-CALM-06

**Acceptance criteria**
1. Given I start box breathing, then the pacer shows inhale/hold/exhale/hold with a visible countdown, and a pause control.
2. Given reduced motion, then the pacer is a static bar with numeric countdown and no scaling animation.
3. Given I finish the configured cycles, then the session is saved with duration and completion state.

### US-CALM2 — Ground myself
**As** a user **I want** the 5-4-3-2-1 exercise **so that** I can return to the present.
**Priority** D · **FR** FR-CALM-02

**Acceptance criteria**
1. Given I start, then steps advance one at a time with Back/Next and a progress indicator.
2. Given I leave mid-exercise, then I am asked whether to save a partial session or discard it.

### US-CALM3 — Meditate with a timer
**As** a user **I want** a simple timer **so that** I can sit for a chosen duration.
**Priority** D · **FR** FR-CALM-03

**Acceptance criteria**
1. Given a duration of 1–60 minutes, then the timer counts down accurately (drift < 1 s/minute), with pause/resume and an optional soft chime.
2. Given the tab is backgrounded, then elapsed time is computed from timestamps, not intervals.

### US-CALM4 — Read affirmations
**As** a user **I want** calm, non-prescriptive affirmations **so that** I can reframe gently.
**Priority** D · **FR** FR-CALM-04, FR-CALM-07

**Acceptance criteria**
1. Given the affirmations page, then I can browse by category and favourite items, and favourites persist.
2. Given any affirmation, then it contains no medical claim and no "you must" phrasing.
3. Given the page, then a support-resources link is always visible.

---

## Epic I — Insights

### US-I1 — Weekly report
**As** a user **I want** a weekly view **so that** I can see the week without judgement.
**Priority** D · **FR** FR-INSN-01..FR-INSN-04

**Acceptance criteria**
1. Given ≥3 check-ins, then the report shows count, average intensity, top emotions with counts, journal entries written, routine completions, and calm minutes.
2. Given <3 check-ins, then "Not enough data yet" and no chart trend line.
3. Given the report, then each sentence includes or links to the number that produced it.

### US-I2 — Monthly report
**As** a user **I want** a monthly view **so that** I can see change over a longer period.
**Priority** D · **FR** FR-INSN-01, FR-INSN-02

**Acceptance criteria**
1. Given two consecutive months, then the report compares counts descriptively ("you recorded 12 check-ins this month, 8 last month") without causal claims.
2. Given a month with no data, then the empty state is neutral and offers to record today.

### US-I3 — Activity overview
**As** a user **I want** one place for my activity **so that** I understand what I actually use.
**Priority** D · **FR** FR-INSN-05

**Acceptance criteria**
1. Given a 30-day range, then I see counts for check-ins, journal entries, routine completions, calm sessions, and support requests, each linking to its module.
2. Given the data, then charts have table equivalents for screen readers.

---

## Epic N — Notifications

### US-N1 — Read notifications
**As** a user **I want** an inbox **so that** I see responses and security events.
**Priority** M · **FR** FR-NOTF-01, FR-NOTF-03

**Acceptance criteria**
1. Given unread notifications, then the nav shows a count badge with accessible label.
2. Given I open a notification, then it is marked read and links to the relevant page.
3. Given another user's notification id, then `404`.

### US-N2 — No private content in notifications
**As** a user **I want** notifications to stay discreet **so that** a lock-screen preview is safe.
**Priority** M · **FR** FR-NOTF-02 · **BR** BR-10

**Acceptance criteria**
1. Given any notification, then its title/body contains no journal text, mood note, support message, or response note (automated sentinel test).
2. Given an email notification, then the email body follows the same rule.

### US-N3 — Control notifications
**As** a user **I want** to choose channels and quiet hours **so that** the space doesn't intrude.
**Priority** H · **FR** FR-NOTF-04

**Acceptance criteria**
1. Given email notifications off, then no notification email is sent except security alerts and account-deletion notices (transactional, documented exception).
2. Given quiet hours 22:00–07:00, then non-security notifications are suppressed and delivered in-app only.
3. Given a timezone change, then quiet hours are interpreted in the new timezone.

---

## Epic PR — Privacy, export, deletion

### US-PR1 — See my consents
**As** a user **I want** to see what I agreed to **so that** I trust the space.
**Priority** M · **FR** FR-PRIV-01

**Acceptance criteria**
1. Given consent history, then each row shows type, policy version, granted/revoked timestamps, and scope when applicable.
2. Given no record for a type, then it shows "Not granted" rather than assuming consent.

### US-PR2 — Revoke optional consents
**As** a user **I want** to withdraw optional permissions **so that** I control sharing.
**Priority** M · **FR** FR-PRIV-02

**Acceptance criteria**
1. Given email notifications granted, when I revoke, then a new `ConsentRecord` with `granted=false` and `revoked_at` exists and email delivery stops.
2. Given a required policy consent, then the revoke control is disabled with an explanation that account deletion is the path.
3. Given an active request-scoped share consent, when I revoke it, then every active share under that request is withdrawn per US-C10.

### US-PR3 — Export my data
**As** a user **I want** a complete copy **so that** my data isn't locked in.
**Priority** H · **FR** FR-PRIV-03, FR-PRIV-04 · **BR** BR-17

**Acceptance criteria**
1. Given I request an export, then a `DataExportRequest` is `queued`, the response is `202`, and I cannot create a second concurrent request (`409 export_in_progress`).
2. Given the build completes, then status is `ready`, an in-app notification exists, and the UI offers a one-time download whose token expires in 5 minutes.
3. Given the archive, then it contains `manifest.json`, `account.json`, `profile.json`, `preferences.json`, `moods.json`, `moods.csv`, `journal.json` + `journal.md`, `selfcare.json`, `calm.json`, `connections.json`, `support_requests.json`, `notifications.json`, `consents.json`, and `README.txt`.
4. Given the archive, then it contains no password hash, token hash, or another user's data.
5. Given 7 days after completion, then the file is deleted and status is `expired`.

### US-PR4 — Download securely
**As** a user **I want** a private download **so that** nobody else can fetch my archive.
**Priority** H · **FR** FR-PRIV-03 · **NFR-SEC-05**

**Acceptance criteria**
1. Given an authenticated owner session and a download token, when the token is used once, then the file streams with `Content-Disposition: attachment` and the token is invalidated.
2. Given a reused or expired token, then `409 token_used` or `410 token_expired`.
3. Given another user's export id with my session, then `404`.

### US-PR5 — Read privacy information
**As** a user **I want** plain-language privacy information **so that** I know how my data is handled.
**Priority** M · **FR** FR-PRIV-08

**Acceptance criteria**
1. Given `/privacy`, then it lists what is collected, why, retention, who can see it, and how to export/delete — matching `security.md` §10.
2. Given the policy version changes, then users see a non-blocking notice and consent is re-requested at next login.

### US-PR6 — Find real support
**As** a user in distress **I want** real support resources **so that** I am not alone with the app.
**Priority** M · **FR** FR-PRIV-08, FR-CONN-16 · **NFR-UX-05**

**Acceptance criteria**
1. Given `/support-resources`, then resources are grouped by region with phone, SMS, chat, and website where available, plus a "if you are in immediate danger" note.
2. Given any resource, then it opens in a new tab with `rel="noopener noreferrer"`.
3. Given the resource list is empty for my region, then a global fallback is shown and the page states the limitation.

---

## Epic SET — Settings

### US-SET1 — Reach settings quickly
**As** a user **I want** settings within reach **so that** I can change things without hunting.
**Priority** H · **FR** FR-SET-01

**Acceptance criteria**
1. Given any app page on desktop, then Settings is in the sidebar and reachable in one click.
2. Given mobile, then Settings is in the "More" sheet, reachable in ≤2 taps.
3. Given a settings subsection, then the URL is stable and deep-linkable.

### US-SET2 — Understand what each section controls
**As** a user **I want** clear sections **so that** I know where to look.
**Priority** M · **FR** FR-SET-02

**Acceptance criteria**
1. Given settings, then sections are Profile, Security, Privacy & consent, Notifications, Trusted people, Data & export, Delete account — in that order.
2. Given a section, then it states the consequence of its actions in one sentence.

### US-SET3 — Confirm destructive actions
**As** a user **I want** friction before irreversible actions **so that** I don't lose my space by accident.
**Priority** M · **FR** FR-SET-03

**Acceptance criteria**
1. Given delete account, journal delete, routine delete, or export request, then a confirmation dialog names the exact object and consequence.
2. Given account deletion, then re-authentication (password) is required and the button stays disabled until the typed phrase matches.
3. Given the dialog is open, then focus is trapped and Escape cancels without side effects.
