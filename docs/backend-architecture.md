# HerSpace — Django Backend Architecture

| Field | Value |
|---|---|
| Document ID | HS-BE-001 |
| Version | 1.0 |
| Date | 2026-10-31 |
| Stack | Python 3.13, Django 5.2 LTS, Django REST Framework 3.16, PostgreSQL 16, Gunicorn, nginx |
| Traces to | `database-design.md`, `api-documentation.md`, `workflows.md` |
| Consumed by | `roadmap.md`, `security.md` |

---

## 1. Stack and dependencies

| Concern | Choice | Notes |
|---|---|---|
| Framework | Django 5.2 LTS | Long support window, mature auth/admin |
| API | Django REST Framework 3.16 | Serializers, permissions, throttling |
| DB driver | `psycopg[binary]` 3.2 | No `psycopg2` |
| Settings | `django-environ` | `.env` in dev, real env vars in prod |
| Schema docs | `drf-spectacular` | Generates `docs/openapi.yaml` in CI |
| Filtering | `django-filter` | List endpoints only |
| Passwords | `argon2-cffi` + Argon2id hasher | NFR-SEC-02 |
| Security headers | `django-csp` | CSP with hashes/nonces |
| Static files | `whitenoise` (Django admin) + nginx (SPA) | No S3 in v1 |
| WSGI | `gunicorn` | 3 workers, 2 threads (2 vCPU baseline) |
| Cache | Django `DatabaseCache` | Throttling/sessions; Redis is a drop-in later |
| Email | SMTP (prod), console/file (dev) | `EMAIL_BACKEND` via env |
| Tests | `pytest`, `pytest-django`, `factory_boy`, `freezegun` | Coverage gate 85% |
| Lint/format | `ruff`, `black` | CI blocking |
| Types | `django-stubs` (optional, dev) | Not a release gate |

**Deliberately absent:** Celery, Redis, Channels, S3, Elasticsearch, microservices, GraphQL, JWT. All are documented upgrade paths, not v1 dependencies.

### 1.1 Requirement files

```text
backend/requirements/
├── base.txt        # django, djangorestframework, psycopg[binary], django-environ,
│                   # django-filter, drf-spectacular, argon2-cffi, django-csp, whitenoise, gunicorn
├── dev.txt         # -r base.txt, pytest, pytest-django, pytest-cov, factory_boy,
│                   # freezegun, ruff, black, django-cors-headers, ipython
└── prod.txt        # -r base.txt, sentry-sdk (optional, PII-scrubbed)
```

Pinned versions live in the files; `pip-compile` output is committed.

---

## 2. Project layout

```text
backend/
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dev.py
│   │   ├── prod.py
│   │   └── test.py
│   ├── urls.py
│   ├── api_urls.py              # /api/v1 router composition
│   ├── wsgi.py
│   ├── asgi.py
│   └── logging.py               # dictConfig + redaction filter
├── apps/
│   ├── accounts/                # user, tokens, auth endpoints, session policy
│   ├── profiles/                # profile, preferences, onboarding
│   ├── wellness/                # mood entries, emotions, triggers, calendar, mood summary
│   ├── connections/             # contacts, invitations, support requests, shares
│   ├── journal/                 # entries, tags, prompts, search
│   ├── selfcare/                # routines, items, completions, today view
│   ├── calm_space/              # activities, affirmations, sessions
│   ├── insights/                # read-only aggregation services + views
│   ├── notifications/           # notification feed + templated producers
│   └── privacy/                 # consent, export, deletion, audit, resources
├── common/
│   ├── permissions.py           # IsOwner, IsVerified, IsNotDeleting
│   ├── exceptions.py            # domain exceptions + DRF handler
│   ├── pagination.py            # StandardPagination
│   ├── models.py                # UUIDModel, TimeStampedModel, LocalDateMixin
│   ├── validators.py            # timezone, phone, safe redirect, text lengths
│   ├── crypto.py                # token generation + hashing
│   ├── audit.py                 # record_event()
│   ├── mail.py                  # send_template()
│   ├── logging_filters.py       # RedactSensitiveFilter
│   └── throttling.py            # scoped throttle classes
├── templates/email/             # plain-text + minimal HTML templates
├── manage.py
├── pytest.ini
└── .env.example
```

**App boundary rules**
- Models may reference other apps **only** via string FK (`"wellness.MoodEntry"`).
- Cross-app writes go through the owning app's service function (`journal.services.delete_entry`, `connections.services.revoke_share_for_resource`).
- `common/` contains no domain models.
- `insights/` has no models and imports only read services.

---

## 3. Settings

### 3.1 `config/settings/base.py` (essential parts)

```python
import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    SESSION_COOKIE_SECURE=(bool, True),
    CSRF_COOKIE_SECURE=(bool, True),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "csp",
    "apps.accounts",
    "apps.profiles",
    "apps.wellness",
    "apps.connections",
    "apps.journal",
    "apps.selfcare",
    "apps.calm_space",
    "apps.insights",
    "apps.notifications",
    "apps.privacy",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "csp.middleware.CSPMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.privacy.middleware.RequestContextMiddleware",   # request id + actor for audit
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
AUTH_USER_MODEL = "accounts.User"

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = False          # explicit transactions in services
DATABASES["default"]["CONN_MAX_AGE"] = 60
DATABASES["default"]["OPTIONS"] = {"sslmode": env("DB_SSLMODE", default="prefer")}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",   # migration fallback
]

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "sessionid"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE")
SESSION_COOKIE_AGE = 12 * 60 * 60
SESSION_SAVE_EVERY_REQUEST = True          # sliding 12h idle window
CSRF_COOKIE_HTTPONLY = False               # JS must read it
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "herspace_cache",
        "TIMEOUT": 3600,
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": ["common.throttling.GeneralUserThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "300/min",
        "register": "5/hour",
        "login": "10/min",
        "login_email": "5/min",
        "password_reset": "10/hour",
        "password_reset_email": "3/hour",
        "verify_resend": "3/hour",
        "invite": "20/day",
        "invite_contact": "1/hour",
        "support_create": "10/hour",
        "public_invite": "30/hour",
        "public_invite_respond": "10/hour",
        "public_support": "60/hour",
        "public_support_respond": "10/hour",
        "export_request": "1/day",
        "export_download": "5/hour",
        "deletion": "3/day",
    },
}

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="HerSpace <hello@herspace.local>")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)

TIME_ZONE = "UTC"
USE_TZ = True
LANGUAGE_CODE = "en"

STORAGE_ROOT = Path(env("PRIVATE_STORAGE_ROOT", default=str(BASE_DIR / "private_storage")))
MEDIA_URL = "/media/"           # never used for exports
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATA_UPLOAD_MAX_MEMORY_SIZE = 1_048_576     # 1 MB JSON bodies
```

### 3.2 CSP (`base.py`)

```python
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'sha256-<inline-theme-script-hash>'"],
        "style-src": ["'self'"],
        "img-src": ["'self'", "data:"],
        "font-src": ["'self'"],
        "connect-src": ["'self'"],
        "frame-ancestors": ["'none'"],
        "base-uri": ["'none'"],
        "form-action": ["'self'"],
        "object-src": ["'none'"],
    }
}
```
No `unsafe-inline`, no third-party origins. If Vite injects inline styles in dev only, `dev.py` relaxes `style-src` with `'unsafe-inline'` — never in production.

### 3.3 Environment variables (`.env.example`)

```dotenv
DJANGO_SECRET_KEY=change-me-64-random-chars
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://herspace:herspace@db:5432/herspace
DB_SSLMODE=prefer
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://localhost:8000
SECURE_SSL_REDIRECT=False
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=HerSpace <hello@herspace.local>
FRONTEND_BASE_URL=http://localhost:5173
PRIVATE_STORAGE_ROOT=./private_storage
TOKEN_HASH_SALT=change-me-32-random-chars
POLICY_TERMS_VERSION=1.0
POLICY_PRIVACY_VERSION=1.0
POLICY_WELLNESS_VERSION=1.0
```

`TOKEN_HASH_SALT` is used only for IP hashing (tokens are hashed without a salt because they are already high-entropy).

---

## 4. Apps and responsibilities

| App | Owns | Key modules | Public surface |
|---|---|---|---|
| `accounts` | `User`, verification/reset/email-change tokens, login/lockout/session | `models.py`, `services/auth.py`, `views/auth.py`, `throttles.py` | `/auth/*` |
| `profiles` | `UserProfile`, `UserPreferences`, onboarding completion | `models.py`, `views/profile.py`, `views/preferences.py` | `/profile/`, `/preferences/`, `/onboarding/complete/` |
| `wellness` | Mood entries, emotions, triggers, calendar, weekly mood summary | `models.py`, `services/moods.py`, `views/moods.py` | `/moods/*` |
| `connections` | Contacts, invitations, support requests, shares | `models.py`, `services/contacts.py`, `services/invitations.py`, `services/support.py`, `views/*` | `/contacts/*`, `/invitations/*`, `/support-requests/*`, `/public/*` |
| `journal` | Entries, tags, prompts, search | `models.py`, `services/journal.py`, `views/journal.py` | `/journal/*` |
| `selfcare` | Routines, items, day/item completions, today view | `models.py`, `services/routines.py`, `views/routines.py` | `/routines/*` |
| `calm_space` | Activities, affirmations, favourites, sessions | `models.py`, `views/calm.py` | `/calm/*` |
| `insights` | Aggregation + statement templates (no models) | `services/weekly.py`, `services/monthly.py`, `services/overview.py`, `copy.py` | `/insights/*` |
| `notifications` | Notification model, templated producers, feed | `models.py`, `services/notify.py`, `views/notifications.py` | `/notifications/*` |
| `privacy` | Consent, export, deletion, audit, resources, middleware | `models.py`, `services/consent.py`, `services/export.py`, `services/deletion.py`, `services/audit.py`, `views/*` | `/privacy/*` |

**Dependency direction:** `accounts` ← `profiles` ← domain apps → `privacy`, `notifications`. Domain apps never import each other's views or serializers.

---

## 5. Model layer conventions

```python
# common/models.py
import uuid
from django.db import models

class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Meta:
        abstract = True

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True
```

Rules
1. Every user-owned model has `user`/`owner`/`requester` FK with `on_delete=CASCADE` and `related_name`.
2. `related_name` is explicit and plural (`mood_entries`, `journal_entries`, `contacts`).
3. Enumerations use `models.TextChoices` whose values exactly match `database-design.md` §1.2.
4. `Meta.constraints` mirrors the DDL: `UniqueConstraint`, `CheckConstraint`, partial uniques via `condition=Q(...)`.
5. `Meta.indexes` mirrors the documented index list; no unindexed FK.
6. No model method sends email, writes files, or calls external services — that is service-layer work.
7. `save()` is not overridden for business logic; services own orchestration.
8. `__str__` never includes private content (e.g. `f"JournalEntry({self.pk})"`).

### 5.1 Example: mood model

```python
class MoodEntry(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="mood_entries")
    local_date = models.DateField()
    timezone = models.CharField(max_length=64)
    intensity = models.PositiveSmallIntegerField()
    note = models.TextField(null=True, blank=True)
    emotions = models.ManyToManyField("MoodEmotion", through="MoodEntryEmotion",
                                      related_name="mood_entries")
    triggers = models.ManyToManyField("MoodTrigger", through="MoodEntryTrigger",
                                      related_name="mood_entries")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "local_date"],
                                    name="uniq_wellness_moodentry_user_date"),
            models.CheckConstraint(check=Q(intensity__gte=1, intensity__lte=10),
                                   name="chk_wellness_moodentry_intensity"),
            models.CheckConstraint(
                check=Q(note__isnull=True) | Q(note__length__lte=2000),
                name="chk_wellness_moodentry_note_len"),
        ]
        indexes = [models.Index(fields=["user", "-local_date"])]
```

---

## 6. Service layer

### 6.1 Rules
- One function per business operation, named after the workflow (`create_support_request`, `respond_to_invitation`, `delete_journal_entry`).
- Every write runs in `transaction.atomic()`; external effects use `transaction.on_commit`.
- Services raise domain exceptions (`common.exceptions.Conflict`, `ConsentRequired`, `TokenExpired`) that the API layer maps to status codes.
- Services never accept `request` objects; they take explicit arguments (`actor`, `payload`).
- Services write audit events inside the transaction.

### 6.2 Domain exceptions

```python
# common/exceptions.py
class DomainError(Exception):
    code = "domain_error"
    status = 400
    def __init__(self, message, *, fields=None, code=None):
        super().__init__(message)
        self.message = message
        self.fields = fields or {}
        if code is not None:
            self.code = code

class ValidationFailure(DomainError): code, status = "validation_error", 400
class ConsentRequired(DomainError):   code, status = "consent_required", 400
class Conflict(DomainError):          code, status = "conflict", 409
class NotFound(DomainError):          code, status = "not_found", 404
class PermissionDenied(DomainError):  code, status = "permission_denied", 403
class TokenExpired(DomainError):      code, status = "token_expired", 410
class TokenUsed(DomainError):         code, status = "token_used", 409
class RateLimited(DomainError):       code, status = "rate_limited", 429
class Locked(DomainError):            code, status = "account_locked", 423
```

### 6.3 Example: create support request (the most sensitive write)

```python
# apps/connections/services/support.py
from django.db import transaction
from django.utils import timezone
from common import audit
from common.crypto import new_token, hash_token
from common.exceptions import ConsentRequired, Conflict, ValidationFailure
from apps.notifications.services.notify import notify
from apps.privacy.services.consent import record_consent
from ..models import SupportRequest, SupportRequestShare, TrustedContact
from ..snapshots import build_mood_snapshot, build_journal_snapshot

ALLOWED_CONTACT_STATUS = {"active", "invited", "unavailable"}
PENDING_LIMIT = 5
SUPPORT_TTL = timezone.timedelta(hours=72)

@transaction.atomic
def create_support_request(*, actor, contact_id, support_type, message=None,
                           channel=None, share_mood_entry_id=None,
                           share_journal_entry_id=None, include_mood_note=False,
                           consent_confirmed=False, client_request_id=None):
    if client_request_id:
        existing = SupportRequest.objects.filter(
            requester=actor, client_request_id=client_request_id
        ).first()
        if existing:
            return existing, None, True

    contact = TrustedContact.objects.select_for_update().filter(
        pk=contact_id, owner=actor
    ).first()
    if contact is None:
        raise NotFound("Contact not found.")
    if contact.status not in ALLOWED_CONTACT_STATUS:
        raise Conflict("This contact can't be asked right now.", code="contact_unavailable")

    if SupportRequest.objects.filter(requester=actor, status="pending").count() >= PENDING_LIMIT:
        raise Conflict("You have several requests waiting already.",
                       code="too_many_pending")

    has_share = bool(share_mood_entry_id or share_journal_entry_id)
    if has_share and not consent_confirmed:
        raise ConsentRequired("Confirm what you're sharing before sending.")

    token = new_token()
    request = SupportRequest.objects.create(
        requester=actor,
        contact=contact,
        contact_name=contact.full_name,
        support_type=support_type,
        message=message or None,
        channel=channel or (contact.preferred_channel if contact.preferred_channel != "none" else "link"),
        status="pending",
        client_request_id=client_request_id,
        response_token_hash=hash_token(token),
        sent_at=timezone.now(),
        expires_at=timezone.now() + SUPPORT_TTL,
    )

    shares = []
    if share_mood_entry_id:
        shares.append(("mood", share_mood_entry_id,
                       build_mood_snapshot(actor, share_mood_entry_id,
                                           include_note=include_mood_note)))
    if share_journal_entry_id:
        shares.append(("journal", share_journal_entry_id,
                       build_journal_snapshot(actor, share_journal_entry_id)))

    for resource_type, resource_id, snapshot in shares:
        SupportRequestShare.objects.create(
            support_request=request,
            resource_type=resource_type,
            resource_id=resource_id,
            snapshot=snapshot,
        )

    if shares:
        record_consent(
            user=actor, consent_type="support_request_sharing", granted=True,
            scope_type="support_request", scope_id=request.id,
            metadata={"share_types": [s[0] for s in shares],
                      "share_ids": [str(s.id) for s in request.shares.all()]},
        )

    notify(
        user=actor, category="support_request_sent",
        title="Request sent", body=f"Your request to {contact.full_name} was sent.",
        link_path=f"/app/support/{request.id}",
    )
    audit.record(actor, "support.requested", target=request,
                 metadata={"support_type": support_type,
                           "share_count": len(shares),
                           "channel": request.channel})
    return request, token, False
```

**Notes**
- `select_for_update` prevents two concurrent sends racing the pending limit.
- The raw token is returned to the view once and never stored.
- The notification body contains only the contact name — never the message.
- Email dispatch happens in the view after commit (`transaction.on_commit`), so a mail failure cannot roll back the request.

### 6.4 Service inventory

| Service | Functions |
|---|---|
| `accounts.services.auth` | `register_user`, `authenticate_user`, `issue_session`, `invalidate_sessions`, `request_password_reset`, `confirm_password_reset`, `change_password`, `request_email_change`, `confirm_email_change`, `verify_email` |
| `profiles.services` | `update_profile`, `update_preferences`, `complete_onboarding` |
| `wellness.services.moods` | `upsert_check_in`, `update_entry`, `delete_entry`, `month_calendar`, `weekly_summary` |
| `connections.services.contacts` | `create_contact`, `update_contact`, `delete_contact` |
| `connections.services.invitations` | `send_invitation`, `resend_invitation`, `revoke_invitation`, `respond_to_invitation` |
| `connections.services.support` | `create_support_request`, `cancel_request`, `revoke_share`, `revoke_request_shares`, `respond_to_request`, `expire_due_requests`, `revoke_shares_for_resource` |
| `journal.services` | `create_entry`, `update_entry`, `delete_entry`, `search_entries` |
| `selfcare.services.routines` | `create_routine`, `update_routine`, `delete_routine`, `add_item`, `update_item`, `delete_item`, `today_view`, `complete_day`, `undo_day`, `undo_item` |
| `calm_space.services` | `record_session` |
| `insights.services` | `weekly_report`, `monthly_report`, `overview` |
| `notifications.services.notify` | `notify`, `notify_many`, `mark_read`, `mark_all_read` |
| `privacy.services.consent` | `record_consent`, `current_consents`, `revoke_consent` (`support_request_sharing` delegates to `revoke_request_shares`) |
| `privacy.services.export` | `request_export`, `build_export`, `issue_download_token`, `stream_download`, `purge_expired` |
| `privacy.services.deletion` | `schedule_deletion`, `cancel_deletion`, `purge_due_deletions` |
| `privacy.services.audit` | `record` |
| `privacy.services.resources` | `list_resources` |

---

## 7. API layer

### 7.1 View style

- `APIView`/generics for simple resources, `ViewSet` only where CRUD is genuinely uniform (journal, contacts, routines).
- Public token endpoints are plain `APIView` with `permission_classes = [AllowAny]` and explicit throttle scopes.
- No business logic in views: validate → call service → serialize → return.

```python
# apps/journal/views/journal.py
class JournalEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsVerified, IsNotDeleting, IsOwner]
    serializer_class = JournalEntrySerializer

    def get_queryset(self):
        return JournalEntry.objects.filter(user=self.request.user).prefetch_related("tags")

    def perform_destroy(self, instance):
        journal_services.delete_entry(actor=self.request.user, entry=instance)
```

### 7.2 Permissions (`common/permissions.py`)

```python
class IsVerified(BasePermission):
    message = "Verify your email to use this part of HerSpace."
    def has_permission(self, request, view):
        return bool(request.user.email_verified_at)

class IsNotDeleting(BasePermission):
    def has_permission(self, request, view):
        return not AccountDeletionRequest.objects.filter(
            user=request.user, status="scheduled").exists()

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None) \
                or getattr(obj, "requester", None)
        return owner == request.user
```

`IsOwner` is defense in depth; the queryset filter is the primary control.

### 7.3 Exception handler

```python
# common/exceptions.py
def api_exception_handler(exc, context):
    if isinstance(exc, DomainError):
        return Response(
            {"error": {"code": exc.code, "message": exc.message,
                       "fields": exc.fields or None,
                       "request_id": getattr(context["request"], "request_id", None)}},
            status=exc.status,
        )
    response = drf_exception_handler(exc, context)
    if response is None:
        logger.exception("unhandled_api_error", extra={"request_id": ...})
        return Response({"error": {"code": "server_error",
                                   "message": "Something went wrong. Please try again."}},
                        status=500)
    response.data = {"error": {"code": map_code(response), "message": humanize(response),
                               "fields": response.data if response.status_code == 400 else None,
                               "request_id": ...}}
    return response
```

- DRF `ValidationError` → `400 validation_error` with field map.
- `Http404`/`DoesNotExist` → `404 not_found` (never 403).
- `NotAuthenticated` → `401 authentication_required`.
- `PermissionDenied` → `403 permission_denied` with a specific `code` where relevant (`email_not_verified`, `deletion_pending`).
- Unhandled exceptions → `500 server_error`, logged with request id, **no** exception text in the response.

### 7.4 Pagination

```python
class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
```
Envelope matches `api-documentation.md` §1.4. `page` beyond range raises `NotFound("page_out_of_range")`.

### 7.5 Serializers

- Explicit `fields` lists; never `__all__`.
- Write serializers are separate from read serializers where the shapes differ (mood create vs detail, support create vs detail).
- `validate_<field>` for single fields, `validate` for cross-field rules (consent, shares, date ranges).
- `SerializerMethodField` only for derived read-only values (`shared_in_requests`, `usage_count`, `entry_count`).
- No serializer writes to another app's models directly.

### 7.6 Throttling

Scoped `SimpleRateThrottle` subclasses with rates from settings. Keys:
- user-scoped: `f"{scope}:{user.pk}"`
- email-scoped: `f"{scope}:{sha256(email)}"`
- IP: `f"{scope}:{sha256(ip)}"`
- public token: `f"{scope}:{sha256(token)}"` plus IP

`429` responses include `Retry-After`. Login lockout (`423`) is separate from throttling and lives in `accounts.services.auth`.

### 7.7 OpenAPI

`drf-spectacular` with `SPECTACULAR_SETTINGS = {"TITLE": "HerSpace API", "VERSION": "1.0.0", "SERVE_INCLUDE_SCHEMA": False}`. CI runs `manage.py spectacular --file docs/openapi.yaml --validate` and fails on drift without a changelog entry.

---

## 8. Authentication implementation details

### 8.1 Custom user model

```python
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin, UUIDModel):
    email = models.EmailField(unique=True, max_length=254)   # + UPPER(email) unique
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(default=timezone.now)
    session_version = models.PositiveIntegerField(default=0)
    failed_login_count = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()
```

Django 5.2 removed `django.contrib.postgres.fields.CITextField`, so case-insensitive uniqueness is enforced by a functional unique constraint instead of the `citext` type:

```python
class Meta:
    constraints = [models.UniqueConstraint(Upper("email"), name="uniq_user_email_ci")]
```

The manager lowercases the address before every write, and the field keeps `unique=True` because Django requires `USERNAME_FIELD` to be unique. Login lookups use `email__iexact`. The initial accounts migration creates `pg_trgm` (used by journal search in M5); `citext` is not installed.

### 8.2 Session version enforcement

Custom middleware compares `request.session["sv"]` with `user.session_version`; mismatch → `logout()` + `401`. This implements "log out everywhere", password-change invalidation, and deletion deactivation without a session table scan. On deletion scheduling, the requesting session's `sv` is refreshed before the response so that session remains usable only for `GET /privacy/account-deletion/`, `POST /privacy/account-deletion/cancel/`, `/auth/logout/`, and `/auth/session/`; every other private endpoint returns `403 deletion_pending`.

### 8.3 Login flow

```python
def authenticate_user(*, email, password, request):
    user = User.objects.filter(email__iexact=email).first()
    if user and user.locked_until and user.locked_until > timezone.now():
        raise Locked("Too many attempts.", fields={"retry_after_seconds": ...})
    if not user or not user.check_password(password):
        _register_failure(user)
        raise InvalidCredentials("That email and password don't match.")
    if not user.is_active:
        raise PermissionDenied("This account is scheduled for deletion.", code="deletion_pending")
    _reset_failures(user)
    login(request, user)
    request.session["sv"] = user.session_version
    audit.record(user, "auth.login")
```

Timing equalisation: when the user does not exist, run `check_password` against a dummy hash to reduce the timing difference.

### 8.4 Tokens

```python
# common/crypto.py
import hashlib, hmac, secrets

def new_token() -> str:
    return secrets.token_urlsafe(32)          # 256 bits

def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

def verify_token(raw: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_token(raw), stored_hash)
```
Tokens are looked up by hash (indexed), then verified with `compare_digest`. Single-use is enforced by `used_at` inside a `select_for_update` transaction.

---

## 9. Query design

### 9.1 List endpoints

- `select_related` for FK display (`contact`, `routine`), `prefetch_related` for tags/emotions/shares.
- Explicit `.only()`/`.values()` for list payloads that exclude `content`/`note`.
- Counts via `Count` annotations, not per-row queries.
- `page_size` capped; no unbounded scans.

### 9.2 Calendar query

```python
rows = (MoodEntry.objects
        .filter(user=user, local_date__range=(first, last))
        .prefetch_related("emotions__emotion")
        .order_by("local_date"))
```
One query for entries + one prefetch for emotions. The service fills missing days in Python (≤31 iterations).

### 9.3 Journal search

MVP:
```python
qs = JournalEntry.objects.filter(user=user)
if q:
    qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
```
- `%` and `_` escaped before the query.
- Backed by `gin_trgm_ops` indexes; the `user_id` predicate is applied first so Postgres can combine a btree filter with the trigram index.
- Snippet computed in Python from the matched row (±60 chars), never in SQL.
- Benchmark gate: 5,000 entries, p95 ≤400 ms (`user-stories.md` US-J5).

Upgrade path (documented, not implemented): `SearchVectorField` + `GinIndex` with `to_tsvector('english', title || ' ' || content)`, keeping trigram for substring matching.

### 9.4 Insights queries

| Metric | Query |
|---|---|
| check-ins | `MoodEntry.objects.filter(user, local_date__range).count()` |
| average intensity | `.aggregate(Avg("intensity"))` |
| emotion frequency | `MoodEntryEmotion.objects.filter(mood_entry__user, mood_entry__local_date__range).values("emotion__key").annotate(n=Count("id"))` |
| journal entries | `JournalEntry.objects.filter(user, entry_date__range).count()` |
| routine completions | `RoutineDayCompletion.objects.filter(user, local_date__range)` + `values("routine__name").annotate(n=Count("id"))` |
| calm minutes | `CalmSession.objects.filter(user, local_date__range).aggregate(Sum("duration_seconds"))` |
| support requests | `SupportRequest.objects.filter(requester, sent_at__date__range).count()` |

All are single-table aggregates on indexed predicates. Target: ≤8 queries per report. If p95 exceeds 400 ms, add a daily per-user cache key `insights:{user_id}:{period}:{anchor}` — the API shape does not change.

### 9.5 Statement generation

```python
# apps/insights/copy.py
TEMPLATES = {
    "top_emotion": "You recorded {emotion} {count} times {period}.",
    "routine_count": "You completed {routine} {count} times {period}.",
    "checkin_count": "You recorded {count} check-ins {period}.",
}
BANNED = ["depress", "anxiety disorder", "diagnos", "because you", "proves",
          "getting worse", "should", "must"]
```
`render_statement(key, **evidence)` formats and asserts no banned substring. A unit test renders every template with sample values and scans the output (`security.md` §13).

---

## 10. Email and notifications

- All email goes through `common.mail.send_template(template, to, context, category)`.
- Templates are plain text + minimal HTML; **no** user content is interpolated (BR-10). Only display names, dates, and links.
- Dispatch happens in `transaction.on_commit`; failures are logged with `event=email_failed`, template name, and a hashed recipient — never the address or body.
- `Notification` rows are created inside the transaction so the in-app feed is always consistent, even if email fails.
- Email categories respect `UserPreferences` and `ConsentRecord`; `security_alert` and `account_deletion_scheduled` bypass toggles (documented exception in `user-stories.md` US-N3).
- Unsubscribe: every non-transactional email includes a link to `/app/settings/notifications`.

---

## 11. Background jobs, scheduled commands, integrity checks

No Celery in v1. Jobs are Django management commands run by cron/systemd timers.

| Command | Schedule | Purpose |
|---|---|---|
| `expire_support_requests` | every 15 min | pending → expired, notifications, audit |
| `expire_invitations` | hourly | sent/opened past `expires_at` → expired |
| `build_exports` | every 5 min | claim `queued` → `processing` → `ready` |
| `purge_exports` | daily 03:10 | delete files >7 days, status → `expired`, rows >90 days |
| `purge_due_deletions` | hourly | complete scheduled deletions |
| `purge_notifications` | daily 03:20 | delete >90 days |
| `purge_audit_events` | daily 03:30 | null `ip_hash` after 90 days; delete >180 days; deletion-related >90 days |
| `purge_tokens` | daily 03:40 | expired/used tokens >30 days |
| `purge_invitations` | daily 03:50 | terminal invitations >180 days |
| `purge_deletion_requests` | daily 04:00 | completed rows >30 days |
| `send_due_reminders` | every 15 min | check-in and routine reminders, respecting quiet hours |
| `verify_integrity` | daily 04:30 | cross-tenant and orphan checks |

### 11.1 Export job claim

```python
with transaction.atomic():
    job = (DataExportRequest.objects
           .select_for_update(skip_locked=True)
           .filter(status="queued")
           .order_by("requested_at")
           .first())
    if not job:
        return
    job.status = "processing"; job.started_at = timezone.now(); job.save()
```
Then build outside the transaction, and finalise in a short transaction.

### 11.2 Integrity checks (`verify_integrity`)

| Check | Action on failure |
|---|---|
| `MoodEntryTrigger.trigger.user != MoodEntry.user` | delete offending link, log `integrity_violation` |
| `JournalEntryTag.tag.user != entry.user` | delete link, log |
| `RoutineItemCompletion.item.routine != day.routine` | delete row, log |
| `SupportRequestShare.resource_id` with no source row and `revoked_at IS NULL` | revoke share, log |
| `SupportRequest.status='pending' AND expires_at < now()` | expire it |
| `ConsentRecord` for a revoked share still granted | write a revoking record |
| `User.is_active=false` without a scheduled deletion | reactivate or flag for review |

The command exits non-zero when violations are found, so monitoring alerts.

### 11.3 Failure semantics

- Jobs are idempotent; re-running must not duplicate notifications (check by `category` + `link_path` + `created_at` window, or a `job_run` marker in cache).
- A failed job logs a structured event and continues with the next item where possible.
- `build_exports` marks `failed` with a stable `error_code` (never a traceback).

---

## 12. Django admin

- Staff-only, `is_staff=True`, 2FA not implemented in v1 (documented limitation; admin is bound to localhost/VPN in production).
- **User content is not browsable:** `JournalEntry`, `MoodEntry`, `SupportRequest`, `SupportRequestShare`, and `CalmSession` are **not registered**.
- Registered models: `User` (read-only fields: email, flags, timestamps), `UserProfile` (display name only), `TrustedContact` (metadata only), `MoodEmotion`, `WritingPrompt`, `CalmActivity`, `Affirmation`, `SupportResource`, `ConsentRecord` (metadata), `AuditEvent` (read-only, no add/change/delete), `DataExportRequest` (status only), `AccountDeletionRequest` (status only).
- Audit log admin has no delete permission and no bulk actions.
- Reference content edits are audited via `LogEntry` and require a `reviewed_at` update for support resources.

---

## 13. Logging and observability

### 13.1 Structured logging

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"redact": {"()": "common.logging_filters.RedactSensitiveFilter"}},
    "formatters": {"json": {"()": "common.logging_filters.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json",
                             "filters": ["redact"]}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
```

`RedactSensitiveFilter`:
- Drops keys matching `password`, `token`, `authorization`, `cookie`, `csrf`, `content`, `note`, `message`, `response_note`, `snapshot`, `email`, `phone`, `q`, `search`.
- Redacts `token=` query parameters from `request.path`/`request.META["QUERY_STRING"]`.
- Access logs record the path template **without the query string**; application logs redact `q` and `search` values.
- Replaces email values with `sha256(value)[:12]` in log records.

**Never logged:** request bodies, journal text, mood notes, support messages, response notes, contact emails/phones, raw tokens, session ids.

### 13.2 What is logged

`request_id`, `method`, `path` (with tokens redacted), `status`, `duration_ms`, `user_id` (pseudonymous UUID), `event` name, `error_code`. Access logs record the path template without the query string and mask token segments for `/api/v1/public/*` and `/download/*`.

### 13.3 Metrics (optional, ops)

- Request latency p50/p95 per route (nginx or middleware counter).
- 5xx rate, 429 rate, 423 rate.
- Job success/failure and duration.
- DB connections, slow query log (`pg_stat_statements`, threshold 200 ms).

No product analytics, no third-party trackers (NFR-PRIV-02).

---

## 14. Testing

### 14.1 Layout

```text
apps/<app>/tests/
├── test_models.py
├── test_services.py
├── test_api.py
├── test_permissions.py      # cross-user matrix
└── factories.py
```

### 14.2 Fixtures

```python
@pytest.fixture
def owner(db):
    return UserFactory(email="owner@example.com", email_verified=True)

@pytest.fixture
def other_user(db):
    return UserFactory(email="other@example.com", email_verified=True)

@pytest.fixture
def api_client(owner):
    client = APIClient()
    client.force_login(owner)
    client.force_authenticate(owner)
    return client
```

### 14.3 Required test suites

| Suite | Contents |
|---|---|
| `test_auth_flows` | register, verify, login, lockout, reset, change, logout-all |
| `test_authorization_matrix` | for every resource: owner 200, other user 404, anonymous 401 |
| `test_consent_transactions` | support request without consent fails and writes nothing; with consent writes request + share + consent atomically |
| `test_token_lifecycle` | expiry, reuse, revoke, resend invalidation |
| `test_mood_upsert` | unique per day, edit path, timezone edge cases |
| `test_journal_privacy` | no content in list, search scoping, deletion revokes shares |
| `test_routine_completion` | idempotency, undo, backfill limits |
| `test_export_flow` | one active, archive contents, download once, expiry |
| `test_deletion_flow` | schedule, cancel, purge cascade, audit anonymisation |
| `test_logging_redaction` | sentinel string never appears in captured logs |
| `test_insight_copy` | banned-phrase scan over all templates |
| `test_integrity_checks` | seeded violations are detected and repaired |

### 14.4 Gates

- `pytest --cov=apps --cov=common --cov-fail-under=85`.
- Authorization modules require 95% (`--cov-fail-under` per package via `coverage.toml`).
- `ruff check .` and `black --check .`.
- `manage.py makemigrations --check --dry-run` (no missing migrations).
- `manage.py spectacular --validate`.
- `python manage.py test --settings=config.settings.test` smoke run in Docker.

---

## 15. Local development

```bash
# 1. Environment
cp .env.example .env            # edit secrets
docker compose up -d db

# 2. Backend
cd backend
python -m venv .venv && .venv/Scripts/activate      # Windows
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_reference_data
python manage.py runserver 8000

# 3. Frontend
cd frontend
npm install
npm run dev                      # http://localhost:5173, proxies /api → :8000
```

`docker-compose.yml` services: `db` (postgres:16, volume, healthcheck), `backend` (build, migrate on start, gunicorn), `frontend` (build → nginx). Dev uses Vite's proxy so cookies stay same-origin at `localhost:5173`.

---

## 16. Production deployment

```
nginx (443, TLS, static SPA, /api proxy, CSP header)
  └── gunicorn (3 workers × 2 threads, unix socket)
        └── PostgreSQL 16 (managed or same host, private network)
        └── SMTP relay
        └── cron/systemd timers → management commands
```

Checklist
1. `DEBUG=False`, real `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`.
2. HTTPS + HSTS + secure cookies; HTTP → HTTPS redirect at nginx.
3. `migrate` before workers start; `collectstatic`.
4. Private storage directory outside the web root, mode `0700`, owned by the app user.
5. Nightly `pg_dump` (14 daily + 8 weekly), restore drill before release.
6. Log rotation, 30-day retention, no PII.
7. Health check `/api/v1/health/` from the load balancer.
8. Backups encrypted at rest; restore documented in `security.md` §12.

---

## 17. Known limitations (v1)

1. No async task queue: exports and purges are cron-driven with a 5–15 minute latency.
2. DB cache for throttling: acceptable for one node; multi-node requires Redis.
3. No field-level encryption of journal content (see `security.md` §11).
4. Admin 2FA not implemented; admin is network-restricted instead.
5. No in-app messaging or realtime notifications.
6. Session store is the database; fine at this scale, not at high concurrency.
7. Search is trigram-based, not linguistic.
8. No multi-tenant organisations; one user per account, per-user scoping only.
