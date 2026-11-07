# HerSpace

A private, human-centered emotional wellness website. Check in with yourself, write what is true, keep gentle routines, and reach the real people you trust — without feeds, strangers, or an AI companion.

> **Status: Blueprint v1.0 approved · Milestone M1 (backend foundation) complete.**
> The specification set remains normative; `backend/` now contains the Django 5.2 project and `docker-compose.yml` runs it against PostgreSQL 16. The frontend lands in M3.

---

## 1. What HerSpace is

| It is | It is not |
|---|---|
| A private space for one person's emotional life | A social network or public profile |
| A mood log, private journal, and self-care space | A medical device, diagnosis, or therapy service |
| A structured way to ask a trusted human for support | An AI companion, chatbot, or "AI girlfriend" |
| Privacy-first: explicit consent, export, deletion | An advertising or analytics product |
| A responsive website (Android comes later, if ever) | A general life-management or productivity suite |

The product's central principle: **support comes from real people.** HerSpace makes asking easier and more honest; it never simulates a relationship or promises that someone will respond.

---

## 2. Non-negotiable invariants

These are enforced by tests, not by intention. Any PR that breaks one is rejected.

1. **No cross-user access.** Every user-owned query is scoped to `request.user`; non-owned IDs return `404`, never `403`.
2. **No automatic sharing.** Mood and journal content leave the account only through an explicit, per-request consent record that the user can revoke.
3. **No private content in logs, emails, or notifications.** Journal text, mood notes, support messages, and response notes never appear outside their own records and the owner's UI/export.
4. **No false reassurance.** `pending` is never rendered as accepted or available; expiry offers alternatives, not blame.
5. **No diagnosis, no AI, no strangers.** Copy and features are reviewed against a banned-phrase list and the product non-goals.
6. **No hidden destructive actions.** Deletion and irreversible actions require explicit confirmation; account deletion has a 7-day cancellable grace period.
7. **Server-side authorization only.** Hiding a button is never a security control.
8. **Tokens are secrets.** 256-bit, hashed at rest, single-use, expiring, redacted from logs.

---

## 3. Repository layout (target)

```text
.
├── backend/                 # Django 5.2 + DRF (see docs/backend-architecture.md)
│   ├── config/
│   ├── apps/                # accounts, profiles, wellness, connections, journal,
│   │                        # selfcare, calm_space, insights, notifications, privacy
│   ├── common/
│   ├── templates/email/
│   ├── requirements/
│   └── manage.py
├── frontend/                # React 18 + Vite (see docs/frontend-architecture.md)
│   ├── public/
│   └── src/                 # assets, components, layouts, pages, services, hooks,
│                            # context, styles
├── docs/                    # this blueprint
├── docker-compose.yml       # planned (M1)
└── README.md
```

The blueprint is complete and M1 is implemented: `backend/` and `docker-compose.yml` exist. `frontend/` is a placeholder until M3.

---

## 4. Documentation map

| # | Document | ID | What it decides |
|---|---|---|---|
| 1 | [`docs/requirements.md`](docs/requirements.md) | HS-SRS-001 | Scope, FR/BR/NFR with stable IDs, data classification, non-goals |
| 2 | [`docs/user-stories.md`](docs/user-stories.md) | HS-US-001 | 60+ stories with Given/When/Then acceptance criteria |
| 3 | [`docs/workflows.md`](docs/workflows.md) | HS-WF-001 | 18 end-to-end workflows, state machines, transactions, failure branches |
| 4 | [`docs/database-design.md`](docs/database-design.md) | HS-DB-001 | 33 tables, field-level types, constraints, indexes, ERD, retention |
| 5 | [`docs/api-documentation.md`](docs/api-documentation.md) | HS-API-001 | 98 endpoints, payloads, errors, permissions, rate limits |
| 6 | [`docs/wireframes.md`](docs/wireframes.md) | HS-UX-001 | Design tokens, responsive shells, every screen, states, a11y |
| 7 | [`docs/frontend-architecture.md`](docs/frontend-architecture.md) | HS-FE-001 | Routing, state, HTTP layer, components, performance, tests |
| 8 | [`docs/backend-architecture.md`](docs/backend-architecture.md) | HS-BE-001 | Django layout, settings, services, permissions, jobs, deployment |
| 9 | [`docs/security.md`](docs/security.md) | HS-SEC-001 | Threat model, token design, privacy program, release checklist |
| 10 | [`docs/roadmap.md`](docs/roadmap.md) | HS-PLAN-001 | M0–M10 milestones, test gates, 12 E2E journeys, risks |
| 11 | [`docs/decisions.md`](docs/decisions.md) | HS-ADR-001 | 20 accepted architecture decisions and their trade-offs |
| 12 | [`docs/openapi.yaml`](docs/openapi.yaml) | HS-OPENAPI-001 | Generated schema for the endpoints implemented so far; grows per milestone |

**Planned artefacts (created during implementation, listed so nothing is silently missing):**

| Artefact | Created in | Purpose |
|---|---|---|
| `docs/openapi.yaml` | M1 ✅ | Generated from drf-spectacular; CI-validated |
| `docs/operations.md` | M10 | Runbooks, on-call contact, secret rotation |
| `CHANGELOG.md` | M1 ✅ | User-visible and API changes |
| `backend/`, `docker-compose.yml` | M1 ✅ | The implementation |
| `frontend/` | M3 | React application |

### Reading order

1. `requirements.md` — what and why.
2. `user-stories.md` — who needs it and how we know it works.
3. `workflows.md` — how the pieces move together.
4. `database-design.md` — what is stored and how it is protected.
5. `api-documentation.md` — the contract between frontend and backend.
6. `wireframes.md` → `frontend-architecture.md` — what it looks like and how it is built.
7. `backend-architecture.md` → `security.md` — how it is built safely.
8. `roadmap.md` + `decisions.md` — how it gets delivered and why it is shaped this way.

---

## 5. Consistency matrix

Every workflow maps to requirements, entities, endpoints, pages, and tests. This table is the blueprint's integrity check: **no row may have an empty cell.**

| WF | Workflow | Requirements | Entities | Endpoints | Pages | Tests |
|---|---|---|---|---|---|---|
| 01 | Register + verify email | FR-AUTH-01…05 | `User`, `UserProfile`, `UserPreferences`, `ConsentRecord`, `EmailVerificationToken`, `AuditEvent` | `POST /auth/register/`, `/auth/verify-email/`, `/auth/verify-email/resend/`, `GET /auth/csrf/` | `/register`, `/verify-email/:token` | J1, `test_auth_flows` |
| 02 | Login, lockout, session | FR-AUTH-06…08, 12, 13 | `User`, `AuditEvent`, `Notification` | `POST /auth/login/`, `/auth/logout/`, `/auth/logout-all/`, `GET /auth/session/` | `/login`, `/app` | J1, `test_auth_flows` |
| 03 | Password reset / change | FR-AUTH-09…11, 13 | `PasswordResetToken`, `Notification`, `AuditEvent` | `/auth/password-reset/`, `/confirm/`, `/auth/password-change/` | `/forgot-password`, `/reset-password/:token`, `/app/settings/security` | `test_auth_flows` |
| 04 | Onboarding | FR-PROF-01…05 | `UserProfile`, `UserPreferences`, `TrustedContact`, `ConsentRecord` | `PATCH /profile/`, `/preferences/`, `POST /onboarding/complete/` | `/onboarding/{profile,wellness,notifications,people,privacy}` | J1 |
| 05 | Daily check-in | FR-WELL-01, 02 | `MoodEntry`, `MoodEntryEmotion`, `MoodEntryTrigger`, `MoodTrigger` | `POST /moods/`, `PATCH /moods/{id}/` | `/app/mood/check-in`, `/app` | J2 |
| 06 | Mood review | FR-WELL-03…07 | `MoodEntry` (read) | `GET /moods/`, `/moods/calendar/`, `/moods/insights/`, `/moods/emotions/` | `/app/mood`, `/app/mood/calendar`, `/app/mood/:id` | J2, J9 |
| 07 | Contact + invitation | FR-CONN-01…04, 07, 08 | `TrustedContact`, `ContactInvitation`, `AuditEvent` | `/contacts/`, `/contacts/{id}/invite/`, `/invitations/{id}/resend\|revoke/` | `/app/people/*`, `/app/invitations` | J4 |
| 08 | Invitation response | FR-CONN-05, 06 | `ContactInvitation`, `TrustedContact`, `ConsentRecord`, `Notification` | `GET/POST /public/invitations/{token}/*` | `/invitation/:token` | J4 |
| 09 | Support request + shares | FR-CONN-09…11, FR-JRNL-09 | `SupportRequest`, `SupportRequestShare`, `ConsentRecord`, `Notification`, `AuditEvent` | `POST /support-requests/` | `/app/support/new` | J5 |
| 10 | Support response | FR-CONN-14, 15 | `SupportRequest`, `Notification`, `AuditEvent` | `GET/POST /public/support-requests/{token}/*` | `/support-response/:token`, `/app/support/:id` | J5 |
| 11 | Expiry / cancel / revoke | FR-CONN-12, 13, 16, 17 | `SupportRequest`, `SupportRequestShare`, `ConsentRecord` | `POST /support-requests/{id}/cancel/`, `DELETE …/shares/{shareId}/`, expiry job | `/app/support/:id`, `/app/support` | J6 |
| 12 | Journal lifecycle | FR-JRNL-01…08 | `JournalEntry`, `JournalTag`, `JournalEntryTag`, `WritingPrompt` | `/journal/` CRUD, `/journal/tags/`, `/journal/prompts/` | `/app/journal/*` | J3 |
| 13 | Routines + completion | FR-SELF-01…08 | `Routine`, `RoutineItem`, `RoutineDayCompletion`, `RoutineItemCompletion` | `/routines/*`, `POST /routines/{id}/complete/` | `/app/selfcare/*` | J7 |
| 14 | Calm session | FR-CALM-01…07 | `CalmActivity`, `Affirmation`, `AffirmationFavorite`, `CalmSession` | `GET /calm/activities/`, `POST /calm/sessions/` | `/app/calm/*` | J8 |
| 15 | Insights | FR-INSN-01…05 | none (computed) | `GET /insights/weekly\|monthly\|overview/` | `/app/insights/*` | J9 |
| 16 | Notifications | FR-NOTF-01…05 | `Notification` | `GET /notifications/`, `PATCH /notifications/{id}/`, `POST /notifications/read-all/` | `/app/notifications`, `/app/settings/notifications` | J10 |
| 17 | Data export | FR-PRIV-03, 04 | `DataExportRequest`, `Notification`, `AuditEvent` | `GET/POST /privacy/export/`, `POST …/download/`, `GET …/download/?token=` | `/app/settings/data` | J11 |
| 18 | Account deletion | FR-PRIV-05…07, FR-AUTH-08 | `AccountDeletionRequest`, `AuditEvent` | `POST /privacy/account-deletion/`, `POST /public/account-deletion/cancel/{token}/` | `/app/settings/delete` | J12 |

**Cross-cutting rows**

| Concern | Requirements | Where enforced |
|---|---|---|
| Consent visibility | FR-PRIV-01, 02 | `/app/settings/privacy`, `GET/POST /privacy/consents/` |
| Theme / accessibility | FR-PROF-03, NFR-A11Y-01…06 | tokens + `ThemeContext` + axe gates |
| Privacy information | FR-PRIV-08 | `/privacy`, `/terms`, `/support-resources` |
| Audit trail | FR-AUTH-13, FR-PRIV-09 | `privacy_auditevent`, no UI |
| Rate limiting | NFR-SEC-04 | `security.md` §8, DRF throttles |
| Data retention | NFR-PRIV-05 | `database-design.md` §17, purge commands |

---

## 6. Key decisions at a glance

| Decision | ADR | Effect |
|---|---|---|
| Modular Django monolith | ADR-001 | One deployable, domain apps |
| Session auth (no JWT) | ADR-002 | Revocable, CSRF-protected |
| UUID keys | ADR-003 | Non-enumerable URLs |
| One check-in per day | ADR-004 | Clean calendar and counts |
| Hard delete for journal | ADR-005 | No second copy of private content |
| Immutable share snapshots | ADR-006 | Recipient sees what was sent; sender can revoke |
| Public token endpoints, unverified responses | ADR-007 | Contacts need no account; labelled "via link" |
| No field encryption in v1 | ADR-008 | Documented risk, upgrade path defined |
| Cron jobs, no Celery | ADR-009 | Simple ops, 5–15 min latency |
| CSS Modules + tokens | ADR-010 | Distinct calm design, no utility framework |
| `/api/v1` versioning | ADR-011 | Safe evolution |
| 7-day deletion grace | ADR-012 | Accidental deletion is recoverable |
| Audit 180/90 days | ADR-013 | Security review window |
| Idempotent support requests | ADR-014 | No duplicate asks to a real person |
| Session + one-time export token | ADR-015 | Archive never exposed by URL alone |
| Contact delete keeps name snapshot | ADR-016 | History survives |
| Trigram search | ADR-017 | Predictable substring search |
| Notification prefs in preferences | ADR-018 | One source of truth |
| Reference content staff-seeded | ADR-019 | Safe, reviewable copy |
| 404 for non-owned | ADR-020 | No existence disclosure |

---

## 7. How to verify the blueprint

Run these checks before starting M1 and after any blueprint change:

1. **ID integrity** — every FR group in `requirements.md` §4 appears in the traceability table (§10) and maps to at least one user story.
2. **Workflow completeness** — every row in §5 above has an entity, endpoint, page, and test.
3. **Schema/API agreement** — every persisted field in `api-documentation.md` exists in `database-design.md`; derived fields are marked as computed; every enum in the API matches `database-design.md` §1.2.
4. **Route agreement** — every page in `wireframes.md` §19 exists in `frontend-architecture.md` §3.1 and vice versa.
5. **Consent integrity** — no path shares content without `support_request_sharing`; the only grant writer is `connections.services.support.create_support_request` (revocation may also come from the consent centre).
6. **Privacy language** — no banned phrase from `security.md` §13 appears in product copy or templates.
7. **Non-goals** — search all documents for `AI`, `chat`, `feed`, `follower`, `stranger`; the only matches may be prohibitions, the in-app "notification feed", or external crisis-resource channels (phone/SMS/chat/website). Any other match is scope creep.
8. **Cross-references** — every `§` reference resolves to an existing section (manual review; no broken links).
9. **Mermaid** — every diagram parses (GitHub preview or `mmdc`).
10. **Numbers** — entity count (33), endpoint count (98), workflow count (18), E2E count (12), milestone count (11) are consistent wherever quoted.

Suggested one-liners (PowerShell, from the repo root):

```powershell
# Enum drift between DB doc and API doc
Select-String -Path docs\database-design.md -Pattern '`(talk|advice|lonely|company|difficult_day|listen)`'
# Banned concepts outside prohibition sections (allow "notification feed" and crisis-resource "chat")
Select-String -Path docs\*.md -Pattern '\bAI companion\b|\bfollower\b|\bstranger matching\b'
# Broken relative doc links
Select-String -Path docs\*.md -Pattern '\]\(([^)]+\.md)\)'
```

---

## 8. Running the backend (M1–M2)

```bash
# 1. Database + API
docker compose up -d
curl http://localhost:8000/api/v1/health/

# 2. Tests and gates (same image, same database)
docker compose run --rm backend pytest
docker compose run --rm backend ruff check .
docker compose run --rm backend black --check .
docker compose run --rm backend python manage.py makemigrations --check --dry-run
```

- **Host port:** `docker-compose.yml` maps Postgres to `${DB_HOST_PORT:-5432}:5432`. On this machine 5432 belongs to another project, so the git-ignored root `.env` sets `DB_HOST_PORT=5433`. A clean machine needs no override.
- **Non-Docker development:** `cd backend`, use a Python 3.13 virtualenv, `pip install -r requirements/dev.txt`, copy `.env.example` to `.env`, then `python manage.py migrate` and `python manage.py runserver 8000`.
- **API surface at M2:** `GET /api/v1/health/`, `POST /api/v1/auth/register/`, `POST /api/v1/auth/login/`, `POST /api/v1/auth/logout/`, `POST /api/v1/auth/logout-all/`, `GET /api/v1/auth/session/`, `GET /api/v1/auth/csrf/`, `POST /api/v1/auth/verify-email/`, `POST /api/v1/auth/verify-email/resend/`, `POST /api/v1/auth/password-reset/`, `POST /api/v1/auth/password-reset/confirm/`, `POST /api/v1/auth/password-change/`, `POST /api/v1/auth/email-change/`, `POST /api/v1/auth/email-change/confirm/`, `GET|PATCH /api/v1/profile/`, `GET|PATCH /api/v1/preferences/`, and `POST /api/v1/onboarding/complete/`. `docs/openapi.yaml` is regenerated from the code; the target contract remains `docs/api-documentation.md`.
- **CSRF:** every unsafe request needs `X-CSRFToken`. The SPA bootstraps it with `GET /api/v1/auth/csrf/`; public token endpoints listed in `api-documentation.md` §1.2 are the only exemptions.
- **Reference data:** `python manage.py seed_reference_data` runs the seeder registry; content modules are added with their owning apps.


Local tooling available: Python 3.14 and Node 24. **The project targets Python 3.13** for dependency stability; use a 3.13 interpreter or the Docker image.

---

## 9. Out of scope for v1

Android app, real-time chat, AI features, public profiles, group support, voice/video, payments, multi-language UI, third-party analytics, staff access to user content. These are product decisions (`requirements.md` §1.3), not unfinished work.

---

## 10. Working agreement

- Documents are normative. Code that disagrees with them is a bug in one of the two; fix both in the same PR.
- New behaviour requires an FR/BR, a workflow, a schema/API change, and a test. "Small" features are not exempt.
- If a decision changes, add an ADR; never rewrite history silently.
- Private content is treated as sensitive in code review, logs, fixtures, and screenshots.
- The release gate is `security.md` §14. It is not advisory.

---

*Blueprint version 1.0 · M2 complete · Next milestone: M3 — Frontend foundation and app shell.*
