# HerSpace — Software Requirements Specification (SRS)

| Field | Value |
|---|---|
| Document ID | HS-SRS-001 |
| Version | 1.0 (baseline) |
| Status | Approved for implementation planning |
| Date | 2026-10-31 |
| Owner | Product / Engineering |
| Supersedes | — |
| Related documents | `user-stories.md`, `workflows.md`, `database-design.md`, `api-documentation.md`, `wireframes.md`, `frontend-architecture.md`, `backend-architecture.md`, `security.md`, `roadmap.md` |

---

## 1. Purpose and scope

### 1.1 Purpose
This document is the single source of truth for **what** HerSpace must do. It defines functional requirements (FR), business rules (BR), and non-functional requirements (NFR). Every other blueprint document traces back to an ID defined here.

### 1.2 Product scope
HerSpace is a **private, single-tenant-by-design, human-centered emotional wellness website**. It provides:

1. Daily emotional check-ins and mood history.
2. A private journal.
3. A trusted-people list with structured support requests delivered over existing channels (email link / SMS / WhatsApp deep link / copyable message).
4. Pressure-free self-care routines.
5. Calm Space exercises (breathing, grounding, meditation timer, affirmations).
6. Data-derived emotional insights with no medical claims.
7. Strong privacy, consent, export, and deletion controls.

### 1.3 Explicit non-goals
| ID | Non-goal |
|---|---|
| NG-01 | No AI companion, chatbot, generated emotional advice, or simulated relationship. |
| NG-02 | No public social network, feed, follower graph, discovery, or stranger matching. |
| NG-03 | No medical diagnosis, treatment, therapy delivery, or clinical scoring. |
| NG-04 | No Android or native mobile app in this release. |
| NG-05 | No real-time in-app chat in this release (schema-reserved only, see `database-design.md` §12). |
| NG-06 | No general-purpose productivity, calendar, finance, or file-storage features. |
| NG-07 | No advertising, third-party analytics, or data sale. |
| NG-08 | No guaranteed availability or response promise for any trusted contact. |
| NG-09 | No mood/journal content in application logs, error trackers, or email bodies. |
| NG-10 | No multi-user social graph; multi-user readiness is limited to per-user ownership scoping (see §9). |

### 1.4 Success criteria (release gate)
| ID | Criterion |
|---|---|
| SC-01 | A new user can register, verify email, complete onboarding, and record a mood check-in without assistance. |
| SC-02 | Journal entries are inaccessible to any other authenticated user, verified by automated authorization tests (HTTP 404, not 403, for non-owned IDs). |
| SC-03 | A support request can be created, delivered, responded to via token link, and its status reflected truthfully. |
| SC-04 | Account export produces a complete machine-readable archive; account deletion removes all personal content within the grace period. |
| SC-05 | Zero high-severity findings in the security review checklist in `security.md` §14. |
| SC-06 | WCAG 2.2 AA automated + manual keyboard pass on all MVP pages. |

---

## 2. Actors and roles

| Actor | Description | Authentication |
|---|---|---|
| **Owner** (primary user) | The single person whose private space this is. Owns all records. | Session-authenticated |
| **Invited contact** | A real person the Owner adds. May have no HerSpace account. | Possesses a single-use, expiring token link |
| **Linked contact** (future) | A contact who later registers a HerSpace account and is explicitly linked. | Session-authenticated (not in this release) |
| **Staff / content admin** | Maintains reference content (emotions, prompts, calm activities, support resources). | Django admin, staff-only, no access to user content by default |
| **System jobs** | Scheduled maintenance (token expiry, export build, deletion purge, reminder dispatch). | Internal, no HTTP surface |

**Roles are not user-selectable.** There is exactly one application role for end users (`owner`). Authorization is therefore **object-ownership based**, not role based, except for `is_staff`.

---

## 3. Glossary

| Term | Definition |
|---|---|
| **Check-in** | One mood record per user per local calendar date. |
| **Local date** | The calendar date in the user's profile timezone at the moment of writing. Stored explicitly; never recomputed on timezone change. |
| **Intensity** | Integer 1–10 self-reported strength of an emotion. Not a clinical score. |
| **Trusted contact** | A person the Owner records and optionally invites. |
| **Invitation** | A tokenized request asking a person to confirm they are willing to be a trusted contact. |
| **Support request** | A structured, expiring request for a specific kind of human support, sent to one trusted contact. |
| **Share** | An explicit, per-request, revocable grant of one mood entry or one journal entry to one recipient. |
| **Consent record** | Append-only proof of a granted/revoked permission, with policy version and scope. |
| **Insight** | A descriptive statement computed only from the Owner's stored data, with no causal or medical claim. |
| **Reference data** | Seeded, non-user-owned content (emotions, prompts, calm activities, support resources). |

---

## 4. Functional requirements

Priority: **M** = MVP (critical), **H** = high, **D** = medium/deferred within website scope, **F** = future.

### 4.1 Authentication and account lifecycle (`FR-AUTH`)

| ID | Requirement | Pri | Notes |
|---|---|---|---|
| FR-AUTH-01 | A visitor can register with email + password + explicit acceptance of Terms and Privacy Policy. | M | Consent records created in the same transaction as the user. |
| FR-AUTH-02 | Passwords are hashed with Argon2id; plaintext is never stored or logged. | M | Minimum 12 characters + Django validators. |
| FR-AUTH-03 | Registration sends a verification email containing a single-use token valid for 24 hours. | M | Token stored only as SHA-256 hash. |
| FR-AUTH-04 | Unverified users can log in but are routed to a verification gate; private data endpoints return `403 email_not_verified`. | M | Prevents enumeration and silent loss of access. |
| FR-AUTH-05 | A user can request a new verification email, throttled to 3 per hour. | M | |
| FR-AUTH-06 | A user can log in with email + password and receives a session cookie. | M | Same-origin SPA; CSRF enforced. |
| FR-AUTH-07 | Login is throttled and locks the account for 15 minutes after 10 consecutive failures. | M | Counter reset on success. |
| FR-AUTH-08 | A user can log out (session destroyed) and log out of all sessions. | M | |
| FR-AUTH-09 | A user can request a password reset; the response is identical whether or not the email exists. | M | Anti-enumeration. |
| FR-AUTH-10 | Reset tokens are single-use, expire in 60 minutes, and are invalidated by any password change. | M | |
| FR-AUTH-11 | A logged-in user can change their password by supplying the current password. | M | All other sessions invalidated. |
| FR-AUTH-12 | Sessions expire after 12 hours of inactivity and are rotated on privilege change. | M | |
| FR-AUTH-13 | Security-relevant events (login, failure, lockout, password change, email change) create audit events. | M | No private content in metadata. |

### 4.2 Profile, preferences, onboarding (`FR-PROF`)

| ID | Requirement | Pri | Notes |
|---|---|---|---|
| FR-PROF-01 | A user can view and edit display name, pronouns (optional), bio (optional, ≤280 chars), date of birth (optional, ≥13 years old), and timezone. | M | Timezone validated against IANA database; DOB never required. |
| FR-PROF-02 | Email address change requires current password and re-verification; the old address is notified. | H | |
| FR-PROF-03 | A user can set theme (system/light/dark), reduced motion, week start day, and 12/24-hour time. | H | Stored server-side; applied before first paint. |
| FR-PROF-04 | Onboarding is a 5-step flow: profile → wellness preferences → notification preferences → optional trusted contact → privacy/consent explanation. | M | Every step skippable except privacy acknowledgement. |
| FR-PROF-05 | Onboarding completion is recorded with a timestamp; the app redirects incomplete users to the first unfinished step. | M | |
| FR-PROF-06 | A user can permanently dismiss or re-enable each gentle dashboard suggestion. | D | Suggestion keys stored in preferences. |

### 4.3 Emotional wellness (`FR-WELL`)

| ID | Requirement | Pri | Notes |
|---|---|---|---|
| FR-WELL-01 | A user can record one check-in per local date with 1–12 emotions, intensity 1–10, optional note (≤2000 chars), and optional triggers. | M | Uniqueness `(user, local_date)`. |
| FR-WELL-02 | Re-submitting the same date edits the existing check-in rather than creating a duplicate. | M | `PATCH` on the entry, or `POST` with upsert semantics documented in API §6.2. |
| FR-WELL-03 | A user can view mood history as a reverse-chronological list with filters (date range, emotion, intensity range). | M | Paginated 20/page. |
| FR-WELL-04 | A user can view a month calendar showing per-day intensity and emotion colour, with keyboard navigation. | H | Days without data are visually distinct, never shown as "missed". |
| FR-WELL-05 | A user can open, edit, and delete a check-in. Deletion requires confirmation and is permanent. | M | |
| FR-WELL-06 | A user can maintain a personal trigger list (add, rename, delete) used when recording check-ins. | H | Deleting a trigger removes its links, not the check-ins. |
| FR-WELL-07 | A user can view weekly and monthly summaries: average intensity, emotion frequency, check-in count, and neutral descriptive statements. | H | Minimum-data threshold per BR-12. |
| FR-WELL-08 | The system never labels a mood as disordered, abnormal, or diagnosable. | M | Copy review gate. |
| FR-WELL-09 | Mood data is never shared automatically; sharing requires a per-request consent record. | M | BR-05. |

### 4.4 Human connection (`FR-CONN`)

| ID | Requirement | Pri | Notes |
|---|---|---|---|
| FR-CONN-01 | A user can add a trusted contact with name, relationship, email and/or phone, preferred channel, and private note. | M | At least one of email/phone required to invite. |
| FR-CONN-02 | Contact status is one of `draft`, `invited`, `active`, `declined`, `revoked`, `unavailable`; UI must display it truthfully. | M | |
| FR-CONN-03 | A user can send an invitation over email, SMS, WhatsApp deep link, or copy a manual link. | M | No message is sent without explicit user action. |
| FR-CONN-04 | Invitation tokens are single-use, hashed at rest, and expire after 7 days. | M | |
| FR-CONN-05 | The invited person can accept or decline on a public page without creating an account. | M | Response is recorded as unverified (BR-08). |
| FR-CONN-06 | Accepting creates a consent record scoped to the contact and sets status `active`; declining sets `declined`. | M | Transactional. |
| FR-CONN-07 | A user can resend (max 1 per 60 minutes) or revoke an invitation. | H | |
| FR-CONN-08 | A user can mark a contact as favourite, edit, and delete a contact. | M | Deleting preserves support-request history via snapshot fields. |
| FR-CONN-09 | A user can create a support request for exactly one contact, choosing one of six support types, with an optional message (≤1000 chars). | M | |
| FR-CONN-10 | A support request can share at most one mood entry and one journal entry, each requiring explicit confirmation at send time; one request-scoped consent record covers the active shares. | M | BR-05, BR-06. |
| FR-CONN-11 | A support request is `pending` until a response is recorded; `pending` must never be rendered as accepted or as "help is coming". | M | BR-07. |
| FR-CONN-12 | Requests expire after 72 hours and transition to `expired`; the sender is notified in-app. | M | |
| FR-CONN-13 | A user can cancel a pending request. | M | |
| FR-CONN-14 | The recipient can accept or decline via the token link and may add a short response note (≤500 chars). | M | |
| FR-CONN-15 | The user can view request history and status; response notes are shown as received. | M | |
| FR-CONN-16 | When a request expires or is declined, the UI offers another trusted contact plus external support resources — never a promise of availability. | M | BR-09. |
| FR-CONN-17 | The user can revoke a share at any time; the recipient link then shows only the revocation notice. | H | |
| FR-CONN-18 | All support-request mutations are audited. | M | |

### 4.5 Private journal (`FR-JRNL`)

| ID | Requirement | Pri | Notes |
|---|---|---|---|
| FR-JRNL-01 | A user can create, read, update, and delete journal entries with title (≤160), content (≤20,000 chars), category, and entry date. | M | |
| FR-JRNL-02 | A user can attach tags (≤10 per entry) and optionally link one check-in and one writing prompt. | H | |
| FR-JRNL-03 | Journal entries are private by default; no endpoint returns another user's entry under any parameter combination. | M | Object-level authorization + queryset scoping. |
| FR-JRNL-04 | A user can search entries by free text (title + content), category, tag, and date range. | M | Trigram index; results paginated. |
| FR-JRNL-05 | A user can use the gratitude view (category = `gratitude`) and browse writing prompts by category. | H | |
| FR-JRNL-06 | Word count is computed server-side and displayed in lists. | D | |
| FR-JRNL-07 | Journal content is excluded from logs, error payloads, notification bodies, and analytics. | M | BR-10. |
| FR-JRNL-08 | Deleting an entry is immediate and irreversible, with a typed confirmation in the UI. | M | Rationale in `docs/decisions.md` ADR-005. |
| FR-JRNL-09 | A journal entry shared in a support request is a snapshot reference; later edits are not visible to the recipient unless re-shared. | H | Implemented by copying a rendered snapshot at send time (see `workflows.md` WF-09). |

### 4.6 Self-care routines (`FR-SELF`)

| ID | Requirement | Pri | Notes |
|---|---|---|---|
| FR-SELF-01 | A user can create, edit, deactivate, and delete routines with name, description, time of day, active weekdays, and reminder settings. | M | |
| FR-SELF-02 | A routine contains ordered items (title, optional note, optional flag, estimated minutes). | M | |
| FR-SELF-03 | A user can complete individual items and the system records a day completion for the routine's local date. | M | |
| FR-SELF-04 | Completion history is viewable per routine and per date range. | H | |
| FR-SELF-05 | No streak counters, penalties, or guilt language are shown. Progress is expressed as counts within a chosen period. | M | BR-11. |
| FR-SELF-06 | A user can undo a completion for the current or a past date. | H | |
| FR-SELF-07 | Routines not scheduled for a given weekday are shown as "not scheduled", not as missed. | M | |
| FR-SELF-08 | Reminders are optional, off by default, and suppressed during quiet hours. | H | In-app reminders in MVP; email reminders high priority. |

### 4.7 Calm Space (`FR-CALM`)

| ID | Requirement | Pri | Notes |
|---|---|---|---|
| FR-CALM-01 | A user can run guided breathing exercises with configurable pattern, animated pacer, and optional sound. | D | Content is seeded reference data. |
| FR-CALM-02 | A user can run the 5-4-3-2-1 grounding exercise with step-by-step progression. | D | |
| FR-CALM-03 | A user can use a meditation timer with a chosen duration and pause/resume. | D | |
| FR-CALM-04 | A user can browse and favourite calming affirmations. | D | |
| FR-CALM-05 | Completed sessions are logged privately with duration and optional before/after intensity. | D | |
| FR-CALM-06 | All animations respect `prefers-reduced-motion` and the user's reduced-motion preference. | M | |
| FR-CALM-07 | Calm Space never presents itself as treatment and always shows a link to support resources. | M | BR-13. |

### 4.8 Insights (`FR-INSN`)

| ID | Requirement | Pri | Notes |
|---|---|---|---|
| FR-INSN-01 | Weekly and monthly reports show check-in count, average intensity, top emotions, journal count, and routine completions. | D | |
| FR-INSN-02 | Every statement is generated from stored records and includes the underlying counts. | M | BR-12. |
| FR-INSN-03 | If a period has fewer than 3 check-ins, the report shows "Not enough data yet" instead of a trend. | M | |
| FR-INSN-04 | No causal, diagnostic, or predictive language is permitted; statements use descriptive phrasing only. | M | Copy lint list in `security.md` §13. |
| FR-INSN-05 | Insights are computed on request in MVP; no materialised analytics tables. | D | Query plans in `backend-architecture.md` §9. |

### 4.9 Notifications (`FR-NOTF`)

| ID | Requirement | Pri | Notes |
|---|---|---|---|
| FR-NOTF-01 | The system creates in-app notifications for: invitation accepted/declined, support request response, support request expiry, export ready, deletion scheduled, security alerts. | M | |
| FR-NOTF-02 | Notification bodies never contain journal text, mood notes, or support messages. | M | BR-10. |
| FR-NOTF-03 | A user can list, mark read, and mark all read. | M | |
| FR-NOTF-04 | A user can enable/disable in-app and email notifications per category and define quiet hours. | H | Stored in `UserPreferences`. |
| FR-NOTF-05 | Email delivery failures never block the originating transaction. | M | Dispatch after commit; failures logged without content. |

### 4.10 Privacy, export, deletion (`FR-PRIV`)

| ID | Requirement | Pri | Notes |
|---|---|---|---|
| FR-PRIV-01 | The user can view all consent records with type, version, grant/revoke timestamps. | M | |
| FR-PRIV-02 | The user can grant or revoke each non-required consent; required policy consents can only be revoked by deleting the account. | M | |
| FR-PRIV-03 | The user can request a data export; the archive is generated asynchronously, stored privately, and downloadable via a one-time expiring token. | H | One-time 5-minute download token; file retained 7 days. |
| FR-PRIV-04 | The export contains all user-owned data in JSON plus human-readable Markdown/CSV, and a manifest. | H | Contents list in `security.md` §10. |
| FR-PRIV-05 | The user can request account deletion; the account is deactivated immediately and purged after a 7-day cancellable grace period. | M | |
| FR-PRIV-06 | Deletion removes all personal content, tokens, exports, and sessions; audit events are retained pseudonymously for 90 days. | M | |
| FR-PRIV-07 | The user can cancel deletion via an emailed token during the grace period. | M | |
| FR-PRIV-08 | The user can read privacy information and a curated, region-tagged external support resource list. | M | Content from `privacy.SupportResource`. |
| FR-PRIV-09 | The system records audit events for all security-relevant and data-lifecycle actions. | M | |

### 4.11 Settings (`FR-SET`)

| ID | Requirement | Pri | Notes |
|---|---|---|---|
| FR-SET-01 | Settings is reachable in ≤2 clicks from any app page and on mobile via the "More" tab. | H | |
| FR-SET-02 | Settings sections: Profile, Security, Privacy & consent, Notifications, Trusted people (link), Data & export, Delete account. | M | |
| FR-SET-03 | Destructive actions require re-authentication or an emailed confirmation token. | M | |

---

## 5. Business rules

| ID | Rule | Enforcement |
|---|---|---|
| BR-01 | One check-in per user per local date. | DB unique `(user_id, local_date)` |
| BR-02 | Every user-owned row carries `user_id` (or is reachable through a parent that does) and every query filters by `request.user`. | ORM + `IsOwner` permission + authorization tests |
| BR-03 | Non-owned object IDs return **404**, never 403, to prevent existence disclosure. | Custom exception handler |
| BR-04 | A support request's recipient is exactly one trusted contact owned by the requester. | Serializer validation |
| BR-05 | Sharing mood or journal content requires a `ConsentRecord` with `consent_type='support_request_sharing'` and `scope_id` = request id, created in the same transaction. | Service layer + transaction |
| BR-06 | At most one mood entry and one journal entry per support request. | Serializer + DB check |
| BR-07 | `pending` ≠ accepted. No UI string may imply response or availability. | Copy review + component tests |
| BR-08 | Responses received through a token link are marked `response_verified = false` and displayed as "via link". | DB field + UI badge |
| BR-09 | Expiry/decline never offers a guarantee; it offers alternatives. | UI copy + E2E test |
| BR-10 | Journal text, mood notes, support messages, response notes, and search terms never enter logs, error reports, notification bodies, or email bodies. | Logging redaction filter + review checklist |
| BR-11 | No streaks, penalties, or loss-framed copy in self-care. | Copy lint + design review |
| BR-12 | Insights require ≥3 check-ins in the period; otherwise "Not enough data yet". | Service guard |
| BR-13 | No medical/diagnostic claims anywhere; wellness disclaimer visible in onboarding, Calm Space, and Insights. | Content review |
| BR-14 | All timestamps stored UTC (`timestamptz`); `local_date` captured at write time from profile timezone. | Model layer |
| BR-15 | Tokens (email verify, reset, invitation, support response, deletion cancel, export download) are stored only as SHA-256 hashes and are single-use. | Model + service |
| BR-16 | Account deletion is blocked while an export is `queued`/`processing`. | Service guard |
| BR-17 | Only one active export request per user at a time. | Partial unique index |
| BR-18 | Staff accounts cannot read user content through the admin without an explicit, audited break-glass action (not implemented in MVP; admin exposes metadata only). | Admin config |
| BR-19 | Contacts may be deleted; support-request history keeps a name snapshot. | `SET_NULL` + snapshot column |
| BR-20 | Reference content is editable by staff only and never contains user data. | Admin + seeds |

---

## 6. Non-functional requirements

### 6.1 Security (`NFR-SEC`)

| ID | Requirement | Target |
|---|---|---|
| NFR-SEC-01 | All traffic over HTTPS; HSTS enabled in production (1 year, includeSubDomains, preload). | Prod |
| NFR-SEC-02 | Passwords hashed with Argon2id; no reversible storage anywhere. | All envs |
| NFR-SEC-03 | CSRF protection on all state-changing requests; `SameSite=Lax` session cookie, `HttpOnly`, `Secure` in prod. | All envs |
| NFR-SEC-04 | Rate limits per `security.md` §8 on all auth, token, export, and deletion endpoints. | All envs |
| NFR-SEC-05 | Object-level authorization on every endpoint returning user data; verified by an automated cross-user matrix. | All envs |
| NFR-SEC-06 | Input validation on every write path (type, length, enum, range, ownership of referenced IDs). | All envs |
| NFR-SEC-07 | No secrets in source; all via environment variables; `.env` never committed. | All envs |
| NFR-SEC-08 | CSP, `X-Content-Type-Options`, `Referrer-Policy: same-origin`, `Permissions-Policy` deny-by-default, `frame-ancestors 'none'`. | All envs |
| NFR-SEC-09 | Dependency vulnerability scan in CI; no known high/critical at release. | Release |
| NFR-SEC-10 | Audit log is append-only and tamper-evident by convention (no update/delete endpoints; DB permissions restrict). | All envs |

### 6.2 Privacy (`NFR-PRIV`)

| ID | Requirement | Target |
|---|---|---|
| NFR-PRIV-01 | Data minimisation: only fields listed in `database-design.md` are collected. | Design |
| NFR-PRIV-02 | No third-party trackers, fonts, or CDNs at runtime; assets self-hosted. | Build |
| NFR-PRIV-03 | IP addresses stored only as salted SHA-256 hashes where needed for abuse defence. | All envs |
| NFR-PRIV-04 | Export completes within 5 minutes for ≤10,000 records; deletion purge within 24 hours of grace expiry. | Ops |
| NFR-PRIV-05 | Retention schedule implemented by scheduled management commands. | Ops |
| NFR-PRIV-06 | Support-request share links are revocable and expire with the request. | Product |

### 6.3 Performance (`NFR-PERF`)

| ID | Requirement | Target |
|---|---|---|
| NFR-PERF-01 | p95 server response ≤ 400 ms for read endpoints, ≤ 800 ms for writes, at 50 concurrent users on 2 vCPU / 4 GB. | Load test |
| NFR-PERF-02 | Initial JS bundle ≤ 250 KB gzipped; route-level code splitting. | Build check |
| NFR-PERF-03 | Largest Contentful Paint ≤ 2.5 s on 4G mid-tier mobile. | Lighthouse |
| NFR-PERF-04 | List endpoints paginate at 20 items; max page size 100. | API |
| NFR-PERF-05 | Insight queries bounded to the requested period with indexed predicates; no full-table scans over journal content. | Query review |

### 6.4 Accessibility (`NFR-A11Y`)

| ID | Requirement | Target |
|---|---|---|
| NFR-A11Y-01 | WCAG 2.2 AA contrast for text, icons, focus rings, and chart labels in both themes. | Audit |
| NFR-A11Y-02 | Full keyboard operation, visible focus, logical tab order, skip link, focus trapping in modals. | Audit |
| NFR-A11Y-03 | Semantic landmarks, one `h1` per page, labelled form controls, `aria-live` for async status. | Audit |
| NFR-A11Y-04 | Charts have text/table equivalents. | Audit |
| NFR-A11Y-05 | Respect `prefers-reduced-motion` and the in-app reduced-motion setting. | Audit |
| NFR-A11Y-06 | Touch targets ≥ 44×44 px on mobile. | Audit |

### 6.5 Compatibility (`NFR-COMP`)

| ID | Requirement |
|---|---|
| NFR-COMP-01 | Evergreen Chrome, Edge, Firefox, Safari (last 2 versions). |
| NFR-COMP-02 | Responsive breakpoints: ≤639 mobile, 640–1023 tablet, ≥1024 desktop. |
| NFR-COMP-03 | No horizontal scroll at 320 px width. |
| NFR-COMP-04 | Works with JavaScript enabled only (documented limitation); server-rendered fallback is out of scope. |

### 6.6 Reliability and operations (`NFR-REL`)

| ID | Requirement |
|---|---|
| NFR-REL-01 | Nightly `pg_dump` backups retained 14 days, weekly retained 8 weeks; restore drill before release. |
| NFR-REL-02 | Health endpoint `/api/v1/health/` returns DB connectivity status without sensitive data. |
| NFR-REL-03 | Structured JSON logs with request id; 30-day retention; no private content. |
| NFR-REL-04 | Migrations are reversible where feasible and always forward-only tested on a production-like dump. |
| NFR-REL-05 | Graceful degradation: if email delivery fails, in-app notifications and status remain correct. |

### 6.7 Maintainability (`NFR-MAINT`)

| ID | Requirement |
|---|---|
| NFR-MAINT-01 | Backend line coverage ≥ 85% overall, ≥ 95% on authorization and consent paths. |
| NFR-MAINT-02 | Frontend component tests for all interactive primitives; E2E for the 12 critical journeys in `roadmap.md` §5. |
| NFR-MAINT-03 | Lint + format gates (ruff/black, eslint/prettier) block merge. |
| NFR-MAINT-04 | Every module has a single owner app; no cross-app model imports except by FK string reference and service functions. |
| NFR-MAINT-05 | API schema generated by drf-spectacular and committed as `docs/openapi.yaml`. |

### 6.8 UX and tone (`NFR-UX`)

| ID | Requirement |
|---|---|
| NFR-UX-01 | Calm, non-judgmental copy; no exclamation-mark pressure, no "you failed", no red error framing for missed routines. |
| NFR-UX-02 | Every empty state explains what the space is for and offers one primary action. |
| NFR-UX-03 | Every destructive action is confirmed and reversible where feasible (deletion grace period, cancellable requests). |
| NFR-UX-04 | Loading states use skeletons, not spinners, for content areas; errors are recoverable with a retry. |
| NFR-UX-05 | Support/emergency resources reachable within 2 clicks from Calm Space, Insights, and support flows. |

---

## 7. Data classification

| Class | Examples | Handling |
|---|---|---|
| **C1 Public** | Marketing copy, support resource list, reference content | Cacheable, no auth |
| **C2 Account** | Email, display name, timezone, preferences | Authenticated, owner-scoped |
| **C3 Sensitive personal** | Mood entries, triggers, journal entries, self-care history, calm sessions | Owner-scoped, no logging, excluded from notifications, encrypted in transit and at rest (disk/volume) |
| **C4 Third-party personal** | Contact name/email/phone, support request messages and responses | Owner-scoped; recipient sees only the shared snapshot; export included |
| **C5 Secret** | Password hashes, token hashes, session keys, `SECRET_KEY` | Never serialized, never logged, never exported |

Application-level field encryption (e.g. `pgcrypto`/KMS envelope encryption for journal content) is **not** in MVP; it is documented as a hardening option in `security.md` §11 with its operational trade-offs.

---

## 8. Assumptions and constraints

| ID | Assumption / constraint |
|---|---|
| AS-01 | Single production user initially; the schema and authorization model are per-user from day one. |
| AS-02 | Frontend and API are served from the same origin in production, enabling cookie sessions without CORS. |
| AS-03 | Email is the only reliable delivery channel; SMS/WhatsApp are user-initiated deep links, not server-sent. |
| AS-04 | Contacts may never respond; the product must remain useful and honest when they don't. |
| AS-05 | No background worker infrastructure in MVP; scheduled management commands via cron/systemd timer. |
| AS-06 | Timezone changes do not rewrite historical `local_date` values. |
| AS-07 | Postgres 16+ with the `pg_trgm` extension available. |
| AS-08 | Content (prompts, affirmations, support resources) is curated by a human and versioned in seeds. |

---

## 9. Multi-user readiness

Even though the product targets one person, the following are mandatory so the system does not require redesign to support more users:

1. Every user-owned table has `user_id` with `ON DELETE CASCADE` (or ownership via parent with cascade).
2. All list endpoints filter by `request.user` at the queryset level, not post-filtering in Python.
3. Object lookups use `get_object_or_404(Model, pk=..., user=request.user)`.
4. No global singletons keyed by "the user" in settings or cache keys; cache keys include `user_id`.
5. Reference data is global and read-only for users.
6. Rate limits are per-user/per-IP, not global constants tuned for one person.

---

## 10. Requirement → document traceability

Endpoint `§` references in this table point to `api-documentation.md`.

| Requirement group | User stories | Workflows | Entities | Endpoints | Pages |
|---|---|---|---|---|---|
| FR-AUTH | US-A1…A8 | WF-01, WF-02, WF-03 | `accounts.*` | `api-documentation.md` §4 auth | `/register`, `/login`, `/verify-email/:token`, `/forgot-password`, `/reset-password/:token` |
| FR-PROF | US-P1…P4 | WF-04 | `profiles.*` | `api-documentation.md` §5 profile | `/onboarding/*`, `/app/settings/profile` |
| FR-WELL | US-W1…W7 | WF-05, WF-06 | `wellness.*` | `api-documentation.md` §6 moods | `/app/mood/*` |
| FR-CONN | US-C1…C10 | WF-07…WF-11 | `connections.*`, `privacy.ConsentRecord` | `api-documentation.md` §7, §8 | `/app/people/*`, `/app/support/*`, `/invitation/:token`, `/support-response/:token` |
| FR-JRNL | US-J1…J7 | WF-12 | `journal.*` | `api-documentation.md` §9 | `/app/journal/*` |
| FR-SELF | US-S1…S6 | WF-13 | `selfcare.*` | `api-documentation.md` §10 | `/app/selfcare/*` |
| FR-CALM | US-CALM1…4 | WF-14 | `calm_space.*` | `api-documentation.md` §11 | `/app/calm/*` |
| FR-INSN | US-I1…I3 | WF-15 | computed | `api-documentation.md` §12 | `/app/insights/*` |
| FR-NOTF | US-N1…N3 | WF-16 | `notifications.*` | `api-documentation.md` §13 | `/app/notifications` |
| FR-PRIV | US-PR1…PR6 | WF-17, WF-18 | `privacy.*` | `api-documentation.md` §14 | `/app/settings/privacy`, `/app/settings/data`, `/app/settings/delete` |
| FR-SET | US-SET1…3 | — | `profiles.*` | `api-documentation.md` §5 | `/app/settings/*` |

---

## 11. Open decisions deferred beyond v1

| ID | Decision | Why deferred |
|---|---|---|
| OD-01 | Multiple check-ins per day (requires dropping `uniq_mood_user_date`, adding `is_primary`) | One-per-day keeps calendar semantics unambiguous; revisit after real usage. |
| OD-02 | Journal trash/soft delete | Adds restore UI and purge semantics; immediate delete is simpler and privacy-stronger. |
| OD-03 | In-app messaging between linked accounts | Requires account linking, participation consent, realtime infra. |
| OD-04 | Application-level content encryption | Key management and search trade-offs; disk-level encryption ships first. |
| OD-05 | Web push notifications | Adds service worker + VAPID; email + in-app cover MVP. |
| OD-06 | Localisation beyond English | Copy volume; i18n hooks are in place (no hard-coded strings in components). |

---

## 12. Approval

| Role | Responsibility |
|---|---|
| Product owner | Scope, tone, non-goals |
| Engineering lead | Feasibility, consistency of this SRS with `database-design.md` and `api-documentation.md` |
| Security reviewer | §6.1, §7, `security.md` sign-off |
| Design lead | §6.4, §6.8, `wireframes.md` sign-off |
