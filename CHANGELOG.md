# Changelog

All notable changes to HerSpace are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
milestone identifiers from `docs/roadmap.md` instead of semantic version tags
until the first release.

## [Unreleased]

### Added - M2 authentication and profile

- Authentication endpoints: register, login, logout, logout-all, session, CSRF,
  email verification (+ resend), password reset (+ confirm), password change,
  email change (+ confirm).
- `accounts.User` timestamps (`created_at`, `updated_at`) and a `save()` that
  keeps `updated_at` fresh, including for partial `update_fields` saves.
- Hashed single-use token models: `EmailVerificationToken`,
  `PasswordResetToken`, `EmailChangeRequest` (verification 24 h, reset 60 min,
  email change 2 h; SHA-256 at rest, raw value only in the email).
- Lockout after 10 consecutive failures for 15 minutes, with timing-equalised
  unknown-email handling and `auth.login_failed`/`auth.lockout` audit events.
- Session-version middleware: password change/reset and logout-all invalidate
  other sessions; the acting session survives via `update_session_auth_hash`.
- `profiles.UserProfile` and `profiles.UserPreferences` (theme, motion, week
  start, time format, reminders, quiet hours, calm defaults, dismissible
  suggestion keys) with database check constraints.
- `privacy.ConsentRecord` (append-only, superseding/revoking semantics) and
  `apps.privacy.services.consent` for grant/revoke/query.
- `notifications.Notification` and the fixed-copy `notify_security()` producer;
  feed and reminders remain M8.
- Profile, preferences, and onboarding endpoints; email notification toggles
  mirror into consent history.
- `CsrfProtectedAPIView` enforces CSRF on every unsafe request, including
  anonymous login/registration/token posts.
- Strict body validation (`400 unknown_field`) through
  `StrictSerializer`/`StrictModelSerializer`.
- Text-only email templates for verification, reset, email-change verification,
  and email-change notice.
- Test suites for every auth branch, profile/preferences validation, consent
  history, CSRF enforcement, and security notices (139 tests total).

### Changed

- `api-documentation.md` §5.4 documents the closed `dismissed_suggestions`
  vocabulary; `frontend-architecture.md` and `wireframes.md` add the
  `/confirm-email-change/:token` route.
- Decision: email is `varchar(254)` with a `UPPER(email)` unique constraint
  instead of `citext` (Django 5.2 removed `CITextField`); `citext` is no longer
  created, `pg_trgm` still is.
- `README.md` documents the M2 API surface and CSRF requirements.

### Added - M1 backend foundation

- Repository skeleton: `backend/`, `frontend/`, `docs/`, `docker-compose.yml`,
  `.editorconfig`, `.gitignore`, CI workflow.
- Django 5.2 project with split settings (`base`, `dev`, `prod`, `test`) and
  `django-environ` configuration.
- PostgreSQL 16 Compose service with healthcheck; `citext` and `pg_trgm`
  extensions created in the first accounts migration.
- Custom `accounts.User` with `UserManager`, UUID primary key, email login,
  `session_version`, lockout counters, and `CITextField` email uniqueness.
- `common/`: `UUIDModel`/`TimeStampedModel`, domain exceptions and DRF handler,
  standard pagination envelope, permissions, token crypto, audit helper, mail
  helper, structured logging with redaction, throttles, validators, and the
  cross-tenant authorization test harness.
- `privacy.AuditEvent` append-only model, closed event vocabulary, and
  `common.audit.record()`.
- `GET /api/v1/health/` with database probe and `X-Request-ID` middleware.
- `seed_reference_data` management command skeleton.
- Test suites proving the error envelope, pagination envelope, redaction
  filter, health endpoint, audit constraints, and that the authorization
  harness fails on a deliberately leaky view.

### Changed

- `README.md` gains an M1 status and quickstart section.

## Blueprint baseline

- M0: requirements, user stories, workflows, database design, API documentation,
  wireframes, frontend and backend architecture, security, roadmap, and 20 ADRs.
