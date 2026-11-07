# HerSpace — Architecture Decision Records (ADRs)

| Field | Value |
|---|---|
| Document ID | HS-ADR-001 |
| Version | 1.0 |
| Date | 2026-10-31 |
| Status | Accepted for v1 |
| Referenced by | All blueprint documents |

An ADR is added or superseded, never silently edited. If an implementation deviates from a decision, the PR must include a new ADR.

---

## ADR-001 — Modular Django monolith

**Context:** One product, one primary user, small team, uncertain long-term scope.
**Decision:** A single Django project with one app per business domain (`accounts`, `profiles`, `wellness`, `connections`, `journal`, `selfcare`, `calm_space`, `insights`, `notifications`, `privacy`) and a shared `common/` package.
**Consequences:** Simple deployment and transactions; clear boundaries without network overhead. Cross-app writes must go through service functions. No microservices, no GraphQL, no separate auth service.

---

## ADR-002 — Same-origin session authentication instead of JWT

**Context:** The website and API are served from one origin; the client is a SPA.
**Decision:** Django session cookies (`HttpOnly`, `SameSite=Lax`, `Secure` in production) plus CSRF tokens. No JWT, no refresh-token storage in the browser.
**Consequences:** Sessions are revocable server-side (`session_version`), no token theft via `localStorage`, CSRF must be handled explicitly. Mobile/third-party clients would need a future token-based scheme.

---

## ADR-003 — UUID primary keys everywhere

**Decision:** `uuid` PKs generated in the application (`uuid4`), with `gen_random_uuid()` in raw DDL.
**Consequences:** Non-enumerable URLs, safe export/merge, slightly larger indexes than `bigint`. No sequential IDs leak record volume.

---

## ADR-004 — One mood check-in per user per local date

**Context:** The product describes a *daily* check-in, a mood calendar, and weekly summaries. Multiple entries per day complicate calendar semantics and summary denominators.
**Decision:** `UNIQUE (user_id, local_date)`; re-submitting the same date updates the existing entry (`POST` upsert, `PATCH`).
**Consequences:** Clean calendar and counts. Users who want multiple entries per day are not served in v1; the migration path (drop unique, add `is_primary`, aggregate in summaries) is documented as OD-01.

---

## ADR-005 — Journal deletion is immediate and irreversible

**Context:** Soft delete adds a trash UI, restore semantics, purge scheduling, and a second place private content lives.
**Decision:** Hard delete with a typed-title confirmation; tag links cascade; shares referencing the entry are revoked and their snapshots purged.
**Consequences:** Strong privacy story and simpler schema. Accidental deletion is unrecoverable; the confirmation is deliberately heavy. A trash feature remains a v2 candidate (OD-02).

---

## ADR-006 — Support-request shares are immutable snapshots with revocable consent

**Context:** A recipient must see what was true when the request was sent, but the sender must be able to withdraw it.
**Decision:** `connections_supportrequestshare` stores a rendered JSON snapshot (`mood` or `journal`) plus `resource_id` (no FK), `granted_at`, `revoked_at`, `viewed_at`. Creating one or more shares writes a single request-scoped `ConsentRecord` in the same transaction. Revocation nulls the snapshot, sets `revoked_at`, and writes a revoking consent record only when the last active share is withdrawn. Deleting the source entry triggers the same revocation.
**Consequences:** No live access to the owner's records; edits after sending are not visible; one mood + one journal share maximum per request. `resource_id` integrity is enforced by the service layer and the nightly `verify_integrity` job.

---

## ADR-007 — Public token endpoints, responses marked unverified

**Context:** Trusted contacts may not have HerSpace accounts; requiring registration to accept an invitation would kill the core flow.
**Decision:** Invitations, support responses, deletion cancellation, and export downloads use 256-bit single-use tokens. Invitation and support responses are unauthenticated and recorded with `response_verified=false`.
**Consequences:** Anyone with the link can respond; mitigated by short TTLs, single use, minimal disclosure, revocation, and explicit "via link" labelling. Verified identity requires linked accounts (future).

---

## ADR-008 — No application-level field encryption in v1

**Context:** Journal content is the most sensitive data. Field encryption complicates search, export, deletion, and key management.
**Decision:** Rely on TLS in transit, disk/volume encryption at rest, encrypted backups, strict authorization, and no-logging guarantees. Document envelope encryption as a Phase-9+ option.
**Consequences:** A database dump exposes plaintext journal content; accepted for a single-tenant deployment with a restricted DB role. Revisit if hosting becomes multi-tenant or staff content access is introduced (`security.md` AR-03).

---

## ADR-009 — No Celery/Redis in v1; cron management commands

**Context:** Export building, expiry, purges, and reminders are the only background work. Volume is tiny.
**Decision:** Idempotent Django management commands run by cron/systemd timers; `SELECT … FOR UPDATE SKIP LOCKED` to claim work. `DatabaseCache` for throttling and sessions.
**Consequences:** 5–15 minute job latency; no retry queue. Redis/Celery can be introduced without API changes when volume or latency demands it.

---

## ADR-010 — CSS Modules and design tokens; no utility framework

**Context:** The brief specifies HTML5/CSS3 and a distinctive, calm visual identity.
**Decision:** CSS custom properties for tokens, CSS Modules for component scoping, self-hosted fonts, no Tailwind/styled-components.
**Consequences:** Small runtime, full control over the aesthetic, token-level theming and contrast testing. More CSS written by hand; no utility-class velocity.

---

## ADR-011 — Versioned API paths (`/api/v1`)

**Context:** The product brief lists unversioned paths; the website will outlive v1 and may gain a mobile client.
**Decision:** All endpoints live under `/api/v1`; the mapping from the brief is documented in `api-documentation.md` §1.8.
**Consequences:** Breaking changes can ship as `/api/v2`; clients must ignore unknown fields. Slight divergence from the brief, documented deliberately.

---

## ADR-012 — Seven-day cancellable deletion grace period

**Context:** Immediate deletion is dangerous; indefinite soft delete contradicts "delete my data".
**Decision:** Deletion deactivates the account immediately, ends all other sessions (the requesting session is restricted to cancellation/logout), emails a cancellation link, and purges after 7 days. Purge deletes all owned rows, export files, and anonymises audit events.
**Consequences:** Users can recover from an accidental deletion; data exists for up to 7 days after the request plus backup retention (documented). Deletion is blocked while an export is running.

---

## ADR-013 — Audit retention: 180 days, 90 after deletion

**Decision:** Security-relevant events are retained 180 days; after account deletion the actor is anonymised and events expire after 90 days.
**Consequences:** Enough window for incident review without becoming a shadow copy of user history. Metadata is restricted to enums, counts, and IDs.

---

## ADR-014 — Idempotency key on support-request creation

**Context:** A double-tap or retry can send a second request and a second email to a real person, which is socially costly.
**Decision:** Optional `client_request_id` (UUID) with `UNIQUE (requester_id, client_request_id)`; duplicates return the original request with `idempotent: true` and send no email.
**Consequences:** Clients should generate the key when the form opens. Other endpoints are naturally idempotent (upserts, unique constraints) or low-risk.

---

## ADR-015 — Export download: authenticated + one-time short-lived token

**Context:** Export archives contain everything. A long-lived URL token would leak through logs, referrers, and shared browsers.
**Decision:** `POST /privacy/export/{id}/download/` requires the owner session and issues a 5-minute single-use token; `GET …?token=` streams once, then invalidates. Files live outside the web root and expire after 7 days.
**Consequences:** Two-step download; the token appears in a query string but is short-lived, single-use, session-bound, and redacted from logs. The SPA must not put the URL in `Referer`-generating links.

---

## ADR-016 — Contact deletion preserves history via a name snapshot

**Decision:** `SupportRequest.contact_id` is `ON DELETE SET NULL` and `contact_name` is copied at creation.
**Consequences:** Users can remove a person without erasing their own support history; the history shows "contact removed". No orphaned PII beyond the name the user already typed.

---

## ADR-017 — Trigram search instead of full-text search in v1

**Context:** Journal search must find substrings across titles and content for a single user's data.
**Decision:** `pg_trgm` GIN indexes + escaped `ILIKE`, scoped by `user_id`. `tsvector` is documented as an upgrade.
**Consequences:** Predictable substring behaviour and simple ranking; no stemming. Performance gate: 5,000 entries, p95 ≤400 ms.

---

## ADR-018 — Notification preferences live in `UserPreferences`

**Context:** The brief lists both "User Preferences" and notification settings.
**Decision:** One 1:1 `profiles_userpreferences` row holds theme, locale, quiet hours, and notification toggles; `notifications` owns only the feed and producers. `email_notifications` consent records mirror preference changes for audit.
**Consequences:** One PATCH endpoint for settings; no duplicated source of truth. Per-category tables can be added later if categories grow.

---

## ADR-019 — Reference content is seeded, staff-editable, never user-owned

**Decision:** Emotions, writing prompts, calm activities, affirmations, and support resources are global tables seeded by idempotent migrations and editable only in admin.
**Consequences:** Consistent vocabulary and safe copy review; users cannot create harmful "affirmations". Support resources require a human `reviewed_at` date.

---

## ADR-020 — 404 for non-owned resources, never 403

**Context:** `403` confirms that a record exists.
**Decision:** All owner-scoped lookups use the scoped queryset, producing `404`. `403` is reserved for authenticated-but-blocked states (unverified email, deletion pending, required consent).
**Consequences:** Slightly less helpful error messages for the owner's own mistakes; no existence disclosure. Enforced by tests, not convention.

---

## Superseding an ADR

1. Add a new ADR with the next number and `Supersedes: ADR-0xx`.
2. Update every document that referenced the old decision.
3. Keep the old ADR with status `Superseded by ADR-0yy`.

Undocumented deviations found in review are treated as defects.
