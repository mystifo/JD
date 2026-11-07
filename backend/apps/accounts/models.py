"""Custom user model. Email is the login identifier; UUID is the primary key."""

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models.functions import Upper
from django.utils import timezone

from common.models import UUIDModel


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("Superuser must have is_staff and is_superuser set.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, UUIDModel):
    email = models.EmailField(max_length=254, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(default=timezone.now)
    session_version = models.PositiveIntegerField(default=0)
    failed_login_count = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    EMAIL_FIELD = "email"

    class Meta:
        db_table = "accounts_user"
        ordering = ["-date_joined"]
        constraints = [
            models.UniqueConstraint(Upper("email"), name="uniq_user_email_ci"),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            self.updated_at = timezone.now()
            update_fields = kwargs.get("update_fields")
            if update_fields is not None and "updated_at" not in update_fields:
                kwargs["update_fields"] = set(update_fields) | {"updated_at"}
        return super().save(*args, **kwargs)

    def __str__(self):
        # Never render the email: `__str__` output reaches logs and admin lists.
        return f"User({self.pk})"

    def get_full_name(self):
        return ""

    def get_short_name(self):
        return ""

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None


class OneTimeToken(UUIDModel):
    """Hashed, expiring, single-use token shared by verification and reset."""

    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    requested_ip_hash = models.CharField(  # noqa: DJ001 - nullable by schema
        max_length=64, null=True, blank=True
    )

    class Meta:
        abstract = True

    @property
    def is_used(self) -> bool:
        return self.used_at is not None


class EmailVerificationToken(OneTimeToken):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )

    class Meta:
        db_table = "accounts_emailverificationtoken"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(expires_at__gt=models.F("created_at")),
                name="chk_emailverificationtoken_expiry",
            )
        ]
        indexes = [models.Index(fields=["user", "-created_at"], name="idx_evtoken_user_created")]

    def __str__(self):
        return f"EmailVerificationToken({self.pk})"


class PasswordResetToken(OneTimeToken):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )

    class Meta:
        db_table = "accounts_passwordresettoken"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(expires_at__gt=models.F("created_at")),
                name="chk_passwordresettoken_expiry",
            )
        ]
        indexes = [models.Index(fields=["user", "-created_at"], name="idx_prtoken_user_created")]

    def __str__(self):
        return f"PasswordResetToken({self.pk})"


class EmailChangeRequest(UUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_change_requests",
    )
    new_email = models.EmailField(max_length=254)
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_emailchangerequest"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(expires_at__gt=models.F("created_at")),
                name="chk_emailchangerequest_expiry",
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(confirmed_at__isnull=True),
                name="uniq_emailchangerequest_one_pending",
            ),
        ]
        indexes = [
            models.Index(fields=["new_email"], name="idx_emailchange_new_email"),
        ]

    def __str__(self):
        return f"EmailChangeRequest({self.pk})"
