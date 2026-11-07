# HerSpace — Privacy and Security Architecture

| Field | Value |
|---|---|
| Document ID | HS-SEC-001 |
| Version | 1.0 |
| Date | 2026-10-31 |
| Traces to | `requirements.md` §6.1–§6.2, §7, `database-design.md` §11, §17 |
| Gate | §14 is the release security checklist referenced by SC-05 |

Security here is a product property: the value of HerSpace depends on a user being willing to write things she would not post anywhere else.

---

## 1. Threat model

### 1.1 Assets

| Asset | Sensitivity | Where it lives |
|---|---|---|
| Journal content | Highest | `journal_journalentry.content` |
| Mood notes, triggers | Highest | `wellness_moodentry.note`, `wellness_moodtrigger` |
| Support messages and response notes | High | `connections_supportrequest` |
| Shared snapshots | High (disclosed by design to one recipient) | `connections_supportrequestshare.snapshot` |
| Contact details (third-party PII) | High | `connections_trustedcontact` |
| Email, display name, timezone | Medium | `accounts_user`, `profiles_userprofile` |
| Routine/calm activity history | Medium | `selfcare_*`, `calm_space_calmsession` |
| Password hashes | Critical | `accounts_user.password` |
| Tokens (verification, reset, invite, support response, deletion cancel, download) | Critical | `*_token_hash` |
| Session identifiers | Critical | `django_session` |
| Audit trail | Medium | `privacy_auditevent` |
| Secrets (`SECRET_KEY`, DB password, SMTP) | Critical | environment only |

### 1.2 Adversaries

| Adversary | Capability | Primary controls |
|---|---|---|
| Anonymous internet | Scans, credential stuffing, token guessing | Rate limits, lockout, 256-bit tokens, no enumeration |
| Curious authenticated user (future multi-user) | Valid account, tries other IDs | Queryset scoping, 404 on non-owned, authorization matrix tests |
| Recipient of a share link | Has one valid token | Minimal disclosure, 72 h TTL, single use, revocation |
| Attacker with a stolen session cookie | Session hijack | `HttpOnly`, `Secure`, `SameSite=Lax`, 12 h idle expiry, logout-all, security alerts |
| Attacker with a DB dump | Reads all tables | Argon2id hashes, token hashes only, no plaintext secrets, disk encryption, no PII in logs |
| Malicious/compromised staff | Admin access | User content not registered in admin, network restriction, audit trail |
| Compromised email inbox | Reset/invite links | Single-use short-TTL reset tokens, all sessions invalidated on reset, notices to old address |
| Network attacker | MITM | HTTPS only, HSTS, secure cookies |
| Abusive contact (recipient) | Can respond, cannot browse | Public page returns only the shared snapshot, no owner data |

### 1.3 STRIDE summary

| Component | Threat | Mitigation |
|---|---|---|
| Login | Spoofing | Argon2id, generic errors, lockout, throttling, session rotation |
| Session | Elevation | Server-side session, `session_version`, verified-email permission |
| Mood/journal APIs | Information disclosure | Owner-scoped querysets, 404, no list content, no logging |
| Support shares | Information disclosure | Explicit per-request consent, snapshot only, revocation, TTL |
| Public token pages | Spoofing / tampering | 256-bit tokens, single use, expiry, state machine with `select_for_update` |
| Export | Information disclosure | Private storage outside web root, session + one-time token, 7-day retention |
| Deletion | Repudiation | Request row + audit events + cancellation token |
| Audit | Tampering | Append-only grants, no admin delete, retention job only |
| Jobs | DoS | `SKIP LOCKED` claim, bounded batches, idempotency |
| Email | Information disclosure | Templates contain no private content; hashed recipient in logs |

---

## 2. Trust boundaries

```
[Browser] --TLS--> [nginx] --unix socket--> [gunicorn/Django] --TLS--> [PostgreSQL]
                        |                          |
                        |                          +--> [SMTP relay]  (outbound only)
                        |                          +--> [private storage dir] (no web route)
                        +--> [static SPA files]
```

Boundaries:
1. **Browser ↔ nginx:** untrusted input; all validation server-side.
2. **nginx ↔ Django:** trusted network, but Django still authenticates every request.
3. **Django ↔ Postgres:** trusted, least-privilege role.
4. **Django ↔ SMTP:** outbound only; no inbound mail parsing.
5. **Django ↔ private storage:** same host, filesystem permissions; never served by nginx.

The frontend is **outside** the authorization boundary. Hiding a button is never a control (BR-02).

---

## 3. Authentication security

| Control | Implementation |
|---|---|
| Password hashing | Argon2id via `argon2-cffi`; parameters `memory_cost=65536` (64 MiB), `time_cost=3`, `parallelism=1`, tuned to keep login p95 < 500 ms on 2 vCPU |
| Password policy | ≥12 chars; not common; not entirely numeric; not similar to email; server-side authoritative |
| Password storage | Only the hash; never logged, never exported, never in error payloads |
| Session | Server-side DB session, `HttpOnly`, `Secure`, `SameSite=Lax`, 12 h sliding idle, rotated on login |
| Session invalidation | `session_version` bumped on password change/reset, logout-all, account deactivation |
| Login throttling | 10/min/IP, 5/min/email; lockout after 10 consecutive failures for 15 min (`423`) |
| Timing | Dummy hash check for unknown emails to reduce timing signal |
| Email verification | Token 24 h, single use, SHA-256 at rest; unverified users blocked from private endpoints (`403 email_not_verified`) |
| Password reset | 60 min, single use, invalidated by any password change; identical response for unknown emails; all sessions end on success |
| Email change | Current password required; token to the new address; notice to the old address; address changes only after confirmation |
| Re-authentication | Required for account deletion; recommended for email change and export (export requires a valid session) |
| Logout | Destroys the session server-side and clears cookies |
| Security notices | `security_alert` notification + email on password change/reset, new login, logout-all, email change |

**Argon2 tuning note:** if the production host cannot sustain 64 MiB per hash under concurrency, reduce `memory_cost` to 32768 and increase `time_cost` to 4; never below OWASP's minimum recommendation. The chosen parameters are recorded in `docs/decisions.md` at deployment time.

---

## 4. Authorization model

1. **Single end-user role** (`owner`); `is_staff` is operational only.
2. **Ownership columns** on every user-owned table (`user_id`, `owner_id`, `requester_id`).
3. **Queryset scoping** is the primary control: `Model.objects.filter(user=request.user)`.
4. **`get_object_or_404`** on the scoped queryset → non-owned IDs return `404` (BR-03).
5. **`IsOwner` permission** as defense in depth on detail routes.
6. **Nested resources** re-validate the parent (`/routines/{id}/items/{itemId}/` checks both the routine owner and item membership).
7. **Referenced IDs** in write payloads (`mood_entry_id`, `trigger_ids`, `share_journal_entry_id`) are validated against the caller's own rows; failures are field errors, not 403s.
8. **Staff** cannot read user content: journal/mood/support models are not registered in admin.
9. **Public token endpoints** bypass user auth by design and are limited to the minimum data in `api-documentation.md` §7.10 and 8.6.

### 4.1 Mandatory authorization test matrix

For every user-owned resource (`mood`, `journal`, `contact`, `invitation`, `support request`, `share`, `routine`, `item`, `completion`, `notification`, `export`, `consent scope`):

| Case | Expected |
|---|---|
| Owner, valid ID | `200`/`204` |
| Other authenticated user, valid ID | `404` |
| Anonymous | `401` |
| Owner, ID from another user in a nested path | `404` |
| Owner, foreign referenced ID in body | `400` with field error |
| Staff user, valid ID | `404` (no content access) |
| Deleted/nonexistent ID | `404` |

The suite is generated from a fixture list so a new resource cannot ship without matrix coverage (`NFR-MAINT-01`).

---

## 5. Input handling and injection

| Risk | Control |
|---|---|
| SQL injection | Django ORM only; `extra()`, `RawSQL`, and string-formatted SQL are banned by lint; migrations reviewed |
| XSS | React auto-escaping; no `dangerouslySetInnerHTML`; no user HTML rendering; strict CSP |
| Stored XSS via names/titles | Treated as text everywhere, including email templates (autoescaped) |
| Mass assignment | Explicit serializer `fields`; `user_id` never accepted from clients |
| Open redirect | `next` must be a same-origin absolute path (`^/(?!/)`) |
| Path traversal | No user-supplied file paths; export filenames generated server-side |
| SSRF | No server-side fetch of user-supplied URLs; support-resource URLs are staff-entered and `https://` only |
| Header injection | Email subjects/bodies built from templates with fixed values; no user text in headers |
| JSON depth/size | `DATA_UPLOAD_MAX_MEMORY_SIZE=1 MB`; depth validated by DRF parsers |
| Regex DoS | No user-supplied regex; search uses escaped `ILIKE` |
| Integer/date abuse | Range validators + DB check constraints (intensity 1–10, durations, lengths) |
| Unicode abuse | Normalise emails (lowercase + `UPPER` unique index), trim whitespace, NFC-normalise display names |
| Duplicate-key races | Unique constraints + `select_for_update` where state transitions matter |

---

## 6. Enumeration and account discovery

### 6.1 Login
Identical status, body, and message for unknown email and wrong password (`401 invalid_credentials`). Lockout is only reported for an existing account, which is an accepted, documented signal (it requires 10 failures).

### 6.2 Password reset
Always `202` with the same body. No timing branch: the email send is queued after the response is generated.

### 6.3 Registration
`409 email_in_use` is returned on submit. This **does** reveal that an address has an account. Accepted trade-off: a silent success would strand users with a confusing "check your inbox" screen and no way forward, and the product is invitation-free and low-profile. Mitigations: rate limit 5/hour/IP, no account metadata in the response, and no password-reset-style probing.

**Documented alternative** if the threat model changes: return `202` always and send either a "welcome" or "someone tried to register with your address" email. This requires a queue to avoid timing leaks and is listed as a future hardening item.

### 6.4 Invitations and support tokens
Tokens are 256-bit random; a wrong token returns `410 token_invalid` after the same work as an expired token. No endpoint confirms whether a contact or request exists by ID without ownership.

---

## 7. Public token endpoints

These are the only unauthenticated state-changing endpoints. Their security model is deliberately narrow.

### 7.1 Design rules

1. Token: `secrets.token_urlsafe(32)` (256 bits), stored as SHA-256, looked up by hash, compared with `hmac.compare_digest`.
2. Single use for all tokens; expiry enforced in the query **and** in the state machine.
3. TTL: email verification 24 hours, password reset 60 minutes, email change 2 hours, invitation 7 days, support request 72 hours, deletion cancel 7 days, export download token 5 minutes.
4. Response body contains only the fields listed in the API doc; no owner email, phone, other contacts, or unshared content.
5. `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex, nofollow`.
6. No session is created; no CSRF token is required (no ambient authority to abuse).
7. Rate limited per IP and per token hash.
8. State changes use `SELECT … FOR UPDATE` to prevent double-response races.
9. Tokens are redacted from logs (path segments under `/public/` and `token=` query params).
10. A token never grants access to any other record.

### 7.2 What a leaked link can do

| Link | Worst case | Mitigation |
|---|---|---|
| Invitation | Accept/decline on the owner's behalf; reveals owner display name + relationship | 7-day TTL, single use, owner sees the response and can revoke/delete the contact |
| Support response | Accept/decline and read the shared snapshot; reveals display name | 72-hour TTL, single use, minimal snapshot, revocable share, owner sees "via link" |
| Deletion cancel | Cancel a deletion | Requires the link **and** is only useful to the account owner; low harm |
| Export download | Download the archive | Requires a valid owner session **and** the token; single use; 5 min |

### 7.3 Response authenticity

Support responses are marked `response_verified=false` because possession of the link is the only proof. The owner UI displays "via link" and never implies cryptographic identity. This is a product honesty requirement (BR-08), not just a technical one.

### 7.4 Email preview safety

Emails contain the owner's display name, the support type, and a link. They never contain journal text, mood notes, or the support message. This keeps lock-screen previews and shared inboxes safe (BR-10).

---

## 8. Rate limiting, lockout and abuse controls

| Control | Value | Scope |
|---|---|---|
| Register | 5/hour | IP |
| Login | 10/min IP, 5/min email | IP + hashed email |
| Account lockout | 10 failures → 15 min | account |
| Password reset request | 3/hour email, 10/hour IP | email + IP |
| Password reset confirm | 10/hour | IP |
| Verify email | 10/hour | IP |
| Verify resend | 3/hour | user |
| Email change | 3/day | user |
| Contact create | 30/day | user |
| Invite | 1/hour per contact, 20/day | user |
| Public invitation GET | 30/hour | IP |
| Public invitation respond | 10/hour | IP |
| Support create | 10/hour, 5 pending max | user |
| Public support GET | 60/hour | IP |
| Public support respond | 10/hour | IP |
| Journal create | 200/day | user |
| Routine create | 50/day | user |
| Routine complete | 300/day | user |
| Calm session | 100/day | user |
| Consent write | 30/day | user |
| Export request | 1/day, 1 active | user |
| Export download | 5/hour | user |
| Deletion request | 3/day | user |
| Public deletion cancel | 10/hour | IP |
| General authenticated | 300/min | user |
| General anonymous | 60/min | IP |

Implementation: DRF scoped throttles keyed by user id, hashed email, hashed IP, or token hash; `DatabaseCache` in v1, Redis-compatible keys. `Retry-After` on `429`. Throttle keys never contain raw emails or IPs.

Additional abuse controls:
- `statement_timeout = 5s` per request; `idle_in_transaction_session_timeout = 30s`.
- Max page size 100; max 12 emotions, 10 tags, 20 routine items, 5 pending requests.
- Request body cap 1 MB; no file uploads.
- Export archive size cap 200 MB (fail with `export_too_large`, no partial file).

---

## 9. Application hardening

### 9.1 Headers and CSP

| Header | Value |
|---|---|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' 'sha256-<theme>'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `same-origin`; `no-referrer` on public token pages |
| `X-Frame-Options` | `DENY` (with CSP `frame-ancestors 'none'`) |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=(), usb=()` |
| `Cross-Origin-Opener-Policy` | `same-origin` |
| `Cross-Origin-Resource-Policy` | `same-origin` |
| `Cache-Control` | `private, no-store` for user data and public token pages |

### 9.2 Logging and redaction

`RedactSensitiveFilter` (backend §13) enforces:

- Drop or hash: `email`, `phone`, `password`, `token`, `authorization`, `cookie`, `csrf`, `content`, `note`, `message`, `response_note`, `snapshot`, `q`, `search`.
- Redact `token=` query values and `/public/.../<token>/` path segments in both application and access logs; only the route template is retained.
- Never log request/response bodies. Access logs record the path template without the query string; application logs redact `q` and `search` values.
- Error trackers (if added) receive `event`, `code`, `status`, `request_id`, `path_template` — never `request.data`.

Automated test: post a sentinel string (`HS_SENTINEL_9f3a…`) into a mood note, journal title/content, support message, response note, and a journal search query; assert the captured log output contains zero occurrences.

### 9.3 Database security

- App role: `SELECT/INSERT/UPDATE/DELETE` on domain tables, **no DDL**, no `TRUNCATE`.
- Audit table: app role has `INSERT` and `SELECT` only (no `UPDATE`/`DELETE`); retention job uses a separate maintenance role.
- Migrations run with a deploy role that has DDL rights, only during deploy.
- TLS to Postgres in production (`sslmode=require` or `verify-full` with a CA).
- Separate database and credentials per environment.
- `pg_stat_statements` enabled; slow query log ≥200 ms.

### 9.4 Audit trail

- Append-only by grant and by code (no update/delete paths).
- Metadata is limited to enums, counts, and IDs — never content.
- Retention: 180 days; 90 days after account deletion (anonymised).
- Review queries documented in `backend-architecture.md` §12.
- No admin bulk delete.

### 9.5 Secrets

- All secrets from environment variables; `.env` git-ignored; `.env.example` contains no real values.
- `SECRET_KEY` ≥64 random characters; rotation invalidates sessions and password-reset links (documented runbook).
- SMTP credentials scoped to sending only.
- No secrets in the frontend bundle, source maps, logs, or error messages.
- CI secret scanning (gitleaks) blocks commits containing key-like patterns.

---

## 10. Privacy program

### 10.1 Data map

| Data | Why | Basis | Retention | Recipients |
|---|---|---|---|---|
| Email, password hash | Account, security | Contract / legitimate interest | Until deletion + 30 days (request rows) | None |
| Display name, timezone, pronouns, bio | Personalisation, correct dates | Consent at signup | Until deletion | None |
| Mood entries, triggers, notes | Core feature | Consent | Until deletion | Only if explicitly shared in a support request |
| Journal entries, tags | Core feature | Consent | Until deletion | Only if explicitly shared |
| Self-care routines and completions | Core feature | Consent | Until deletion | None |
| Calm sessions | Core feature | Consent | Until deletion | None |
| Trusted contacts (name, email, phone) | Human connection | Consent; the contact is informed by invitation | Until deletion or contact removal | The contact receives only the invitation/support link |
| Support requests, shares, responses | Human connection | Consent per request | Until deletion | The chosen contact, for the TTL |
| Consent records | Proof of permission | Legal obligation | Until deletion | None |
| Audit events | Security | Legitimate interest | 180 days (90 after deletion, anonymised) | None |
| Notifications | In-app function | Contract | 90 days | None |
| Export archives | User request | Consent | 7 days | The owner only |
| IP hash | Abuse defence | Legitimate interest | 90 days | None |
| Session records | Authentication | Contract | 12 h idle | None |

### 10.2 Cookies and storage

| Name | Purpose | Type | Lifetime |
|---|---|---|---|
| `sessionid` | Authentication | First-party, `HttpOnly`, `Secure`, `SameSite=Lax` | 12 h sliding |
| `csrftoken` | CSRF protection | First-party, JS-readable | Session |
| `localStorage["hs-theme"]` | Prevent theme flash | Local only, no identifier | Persistent until cleared |

No analytics cookies, no third-party cookies, no fingerprinting, no advertising IDs. The SPA stores no user content in web storage.

### 10.3 Third parties

| Party | Data | Notes |
|---|---|---|
| SMTP relay | Recipient email, template text | No journal/mood/support content; transactional only |
| Hosting provider | Encrypted disk, network metadata | DPA required; region documented |
| Backup storage | Encrypted database dumps | Same retention as §10.5 |

No analytics, no crash-reporting SDK with payloads, no CDN, no font service, no payment processor.

### 10.4 Export contents (FR-PRIV-04)

`herspace-export-<user_id>-<timestamp>.zip`:

```
manifest.json          schema_version, generated_at, counts, exclusions
account.json           email, email_verified_at, account created_at (no credentials or sessions)
profile.json           display name, pronouns, bio, date of birth, timezone, locale, onboarding, created_at
preferences.json       theme, notification prefs, quiet hours, calm defaults
moods.json             entries + emotions + triggers
moods.csv              human-readable check-in table (date, intensity, emotions, triggers, note)
journal.json           entries + tags + prompt references
journal.md             human-readable entries, chronological
selfcare.json          routines, items, day completions, item completions
calm.json              sessions + activity titles + affirmation favourites (reference ids resolved)
connections.json       contacts (name, relationship, email, phone, note) + invitations metadata
support_requests.json  requests, shares (snapshots), responses
notifications.json     in-app notification metadata and read state
consents.json          full consent history
README.txt             what each file is, what is excluded, how deletion works
```

**Excluded:** password hash, token hashes, session data, audit internals, staff data, other users' rows, internal file paths, rate-limit counters.

### 10.5 Deletion semantics

1. Request: password + typed `DELETE` → `scheduled`, `is_active=false`, all other sessions ended, the requesting session restricted to cancellation/logout, cancellation link emailed.
2. Grace: 7 days, cancellable via emailed token or the restricted requesting session.
3. Purge: export files deleted; final confirmation email sent to `email_snapshot`; user row deleted → cascades all owned rows; audit events anonymised (`actor=NULL`, `actor_pseudonym` retained) and expired at 90 days; request row marked `completed`, with `email_snapshot`, `reason`, and `cancel_token_hash` cleared, `user_id=NULL`, then purged after 30 days.
4. Backups: the user's data remains in encrypted backups until the backup retention window expires (≤8 weeks). This is stated in the privacy page; backups are not selectively edited.

### 10.6 Privacy information page

`/privacy` must state, in plain language and matching this document: what is collected, why, who can see it, how long it is kept, how to export, how to delete, what happens to backups, and the limits of the service (not medical care, no guaranteed human response).

---

## 11. Encryption strategy

| Layer | v1 | Notes |
|---|---|---|
| In transit | TLS 1.2+ (1.3 preferred), HSTS | nginx config, certificate renewal monitored |
| At rest (volume) | Provider/disk encryption | Required for production |
| Backups | Encrypted archives | Key stored separately from the backup |
| Passwords | Argon2id | Irreversible |
| Tokens | SHA-256 hash only | Raw value exists only in the email/link and in memory |
| Journal/mood fields | **Not** application-encrypted in v1 | See below |

**Why no field-level encryption in v1:** it breaks server-side search and sorting, requires key management (KMS or envelope encryption), complicates export and deletion, and adds a failure mode where a lost key destroys the user's data. Disk encryption + strict authorization + no logging covers the primary threats (stolen disk, stolen backup, curious operator) for a single-tenant deployment.

**Upgrade path (documented, not implemented):**
1. Envelope encryption with a KMS-managed data key per user.
2. Encrypt `journal_journalentry.content`, `wellness_moodentry.note`, `connections_supportrequest.message/response_note`, and share snapshots.
3. Move search to a client-side or per-user index, or store a blind index of hashed tokens (loses substring search).
4. Rotate keys with a re-encryption job; store key versions per row.

This is a Phase-9+ decision and must be recorded in `docs/decisions.md` before implementation.

---

## 12. Backup, restore, incident response

### 12.1 Backup

- Nightly `pg_dump -Fc` at 02:00 UTC; 14 daily + 8 weekly copies.
- Encrypted at rest (age/GPG), key held outside the backup bucket.
- Private storage (exports) is **not** backed up; exports are regenerable.
- Backups stored in a different region/account where available.
- Monthly restore drill into a scratch database; record the time-to-restore.

**Targets:** RPO 24 h, RTO 4 h.

### 12.2 Restore procedure

1. Provision a clean Postgres instance.
2. Restore the latest dump; run `migrate` to the current release.
3. Verify row counts and `verify_integrity`.
4. Rotate `SECRET_KEY` (invalidates sessions), force password resets if credentials may be exposed.
5. Point the app at the restored DB; monitor 5xx and 401 rates.

### 12.3 Incident response

| Severity | Example | Response |
|---|---|---|
| S1 | Confirmed cross-user data exposure, DB compromise | Immediate containment, rotate secrets, notify affected users, legal review within 72 h |
| S2 | Auth bypass, token forgery, export leak | Contain within 4 h, patch, audit review |
| S3 | Rate-limit bypass, spam, minor info leak | Fix within 72 h |
| S4 | Cosmetic/security hardening | Next release |

Runbook steps: preserve logs (no PII), identify scope via audit events, contain (disable endpoint/feature flag, rotate keys), eradicate, recover from clean backup if needed, notify, write a post-mortem with concrete follow-ups.

**Contact:** a single named security owner is recorded in `docs/operations.md` (not in this public blueprint).

---

## 13. Content safety and tone enforcement

### 13.1 Disclaimers (required placements)

| Placement | Copy |
|---|---|
| Onboarding step 5 | "HerSpace doesn't diagnose anything and isn't a replacement for care." |
| Calm Space footer | "These are wellness tools, not treatment. If you need a person, support resources are here." |
| Insights footer | "These are observations from your own records, not medical advice." |
| Support resources | "If you are in immediate danger, contact your local emergency number." |

### 13.2 Banned phrase list (automated lint)

The build fails if any of these appear in user-facing strings:

```
diagnos, disorder, depressed, depression, anxiety disorder, bipolar, trauma response,
symptom, treatment, therapy, cure, heal your, you are getting worse, you are improving,
because you, proves that, should have, you must, you failed, streak, don't break,
on the way, guaranteed, will respond, always available, AI companion, AI friend
```

Allowed exceptions: the word "support" in "support request"; "care" in "not a replacement for care". The lint operates on `frontend/src/**/*.{js,jsx}` string literals and on insight templates, with an allowlist file for reviewed exceptions.

### 13.3 Support resource maintenance

- Staff-entered, region-tagged, `https://` only, `reviewed_at` required.
- A management command warns when any resource is older than 12 months.
- The list must never be empty for a supported region; `GLOBAL` fallback always exists.
- No resource is added without a human verification of the number/URL.

### 13.4 Human-connection honesty

- The UI never states or implies that a contact is available, online, or likely to respond.
- `pending` copy: "Waiting for a response." plus an explanation that sending is not the same as being seen.
- Expiry copy offers alternatives, never blame.
- No push-style nagging; reminders are opt-in and quiet-hours aware.

---

## 14. Release security checklist (SC-05 gate)

Every item must be **Pass** with evidence before a production release.

### Authentication and session
- [ ] Argon2id is the active hasher; a test asserts `identify_hasher` returns Argon2 for new users.
- [ ] Password minimum length 12 enforced server-side; common-password rejection tested.
- [ ] Login responses are identical for unknown email and wrong password (body, status, message).
- [ ] Lockout triggers at 10 failures and clears after 15 minutes; tested with a frozen clock.
- [ ] Session cookie is `HttpOnly`, `Secure` (prod), `SameSite=Lax`; CSRF enforced on all unsafe methods.
- [ ] Password change/reset and logout-all invalidate other sessions (`session_version`).
- [ ] Verification/reset tokens are hashed at rest, single-use, and expire as specified.
- [ ] Email change requires the current password and re-verification.

### Authorization
- [ ] Authorization matrix passes for every resource (owner 200 / other 404 / anon 401 / staff 404).
- [ ] No endpoint accepts a `user_id` from the client.
- [ ] Nested resources validate both parent ownership and child membership.
- [ ] Public token endpoints return only the documented fields (snapshot test).
- [ ] `404` (not `403`) is returned for non-owned object IDs.

### Data protection
- [ ] Sentinel test proves journal/mood/support text never appears in logs or error output.
- [ ] Notification and email templates contain no user-written content (template review + test).
- [ ] Export archive contains no password hash, token hash, or other users' data; download is session + token protected and single-use.
- [ ] Deletion purges all owned rows, deletes export files, and anonymises audit events; tested end to end.
- [ ] Private storage is outside the web root and not reachable by URL (manual check).
- [ ] Database TLS enabled; backups encrypted; restore drill completed this quarter.

### Web hardening
- [ ] CSP has no `unsafe-inline`/`unsafe-eval` in production; the theme script hash matches.
- [ ] HSTS, `nosniff`, `frame-ancestors 'none'`, `Referrer-Policy`, `Permissions-Policy` present.
- [ ] No third-party origins in `connect-src`, `font-src`, `img-src`, or the bundle.
- [ ] `DEBUG=False`, `ALLOWED_HOSTS` explicit, `SECRET_KEY` from env, no secrets in the repo.
- [ ] Dependency audit: no high/critical vulnerabilities (`pip-audit`, `npm audit`).
- [ ] `npm run build` contains no source maps served publicly.

### Abuse and reliability
- [ ] All rate limits from §8 are active and return `429` with `Retry-After`.
- [ ] Request body cap, page-size cap, and `statement_timeout` configured.
- [ ] Export and deletion jobs are idempotent and safe to re-run.
- [ ] `verify_integrity` runs clean on a seeded production-like dataset.
- [ ] Health endpoint returns 503 when the DB is down and leaks nothing.

### Product safety
- [ ] Banned-phrase lint passes; disclaimers present in the four required placements.
- [ ] Support resources reviewed within 12 months; `GLOBAL` fallback present.
- [ ] `pending` never rendered as accepted/available; copy reviewed against `wireframes.md` §17.
- [ ] No AI-generated emotional response exists anywhere in the product.

**Sign-off:** engineering lead + security reviewer + product owner. Any unchecked item blocks release; exceptions require a written risk acceptance with an expiry date.

---

## 15. Accepted risks (v1)

| ID | Risk | Why accepted | Review trigger |
|---|---|---|---|
| AR-01 | Registration reveals whether an email has an account (`409`) | UX clarity; low-value target; rate limited | If the product becomes multi-user/public |
| AR-02 | Support responses are unverified (link possession only) | Contacts may have no account; verified identity is out of scope | If linked accounts ship |
| AR-03 | Journal content not application-encrypted | Search/export/key-management trade-offs; disk encryption covers main threats | If multi-tenant hosting or staff content access is introduced |
| AR-04 | Backups retain deleted data up to 8 weeks | Standard backup practice; documented to users | If retention requirements change |
| AR-05 | Admin has no 2FA | Admin is network-restricted and cannot read content | Before any remote admin access |
| AR-06 | DB cache used for throttling | Single-node deployment | When scaling beyond one app node |
| AR-07 | Email delivery is best-effort | In-app state is authoritative; no delivery guarantee | If email becomes a primary channel |
| AR-08 | No CSRF token on public token POSTs | No ambient session authority; token is the capability | If public pages ever create sessions |
| AR-09 | Single-region hosting | Cost/complexity for one user | If user base or residency requirements change |

---

## 16. Secure development lifecycle

| Stage | Control |
|---|---|
| Design | This document + `database-design.md` review before coding a module |
| Code | PR review checklist: authorization, validation, logging, transactions |
| CI | ruff/black, pytest + coverage, `makemigrations --check`, `spectacular --validate`, pip-audit, npm audit, gitleaks, banned-phrase lint, bundle budget |
| Test | Authorization matrix, sentinel logging test, token lifecycle, deletion/export end-to-end |
| Release | §14 checklist, backup verified, migrations dry-run on a production dump |
| Operate | Log review, failed-login/lockout alerts, job failure alerts, dependency updates monthly |
| Decommission | Export offered, deletion purged, backups aged out, secrets rotated |

---

## 17. Security contacts and disclosure

A `security.txt` file is served at `/.well-known/security.txt` with a monitored contact and a 90-day disclosure window. The contact address is configured by environment, not hard-coded, and is excluded from the public repo.

---

## 18. Traceability

| Requirement | Section |
|---|---|
| NFR-SEC-01…10 | §3, §9, §14 |
| NFR-PRIV-01…06 | §10, §11 |
| BR-02, BR-03 | §4 |
| BR-05, BR-08 | §7.3 |
| BR-10 | §9.2, §13 |
| BR-12, BR-13 | §13 |
| BR-15 | §3, §7.1 |
| FR-PRIV-03…07 | §10.4, §10.5 |
| SC-05 | §14 |
