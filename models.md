import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


# ──────────────────────────────────────────────
# CHOICES
# ──────────────────────────────────────────────

ROLE_CHOICES = [
    ('master_admin', 'Master Admin'),
    ('local_admin', 'Local Admin'),
]

BRAND_CHOICES = [
    ('kuttukaran', 'Kuttukaran'),
    ('maruti', 'Maruti'),
    ('other', 'Other'),
]

REVIEW_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('replied', 'Replied'),
    ('ignored', 'Ignored'),
]

REPLY_TYPE_CHOICES = [
    ('ai_generated', 'AI Generated'),
    ('templated', 'Templated'),
    ('manual', 'Manual'),
]

SENTIMENT_CHOICES = [
    ('positive', 'Positive'),
    ('negative', 'Negative'),
    ('neutral', 'Neutral'),   # ← added: 3-star reviews are neither
]

ALERT_CHANNEL_CHOICES = [
    ('email', 'Email'),
    ('whatsapp', 'WhatsApp'),
]

ALERT_STATUS_CHOICES = [
    ('sent', 'Sent'),
    ('failed', 'Failed'),
]

REGISTRATION_STATUS_CHOICES = [
    ('pending_verification', 'Pending Verification'),
    ('active', 'Active'),
    ('expired', 'Expired'),
]


# ──────────────────────────────────────────────
# SOFT DELETE BASE
# ──────────────────────────────────────────────

class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)

    def delete(self):
        from django.utils import timezone
        return self.update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

    def deleted_only(self):
        return SoftDeleteQuerySet(self.model, using=self._db).dead()


class SoftDeleteModel(models.Model):
    """
    Abstract base: adds soft-delete support.
    Use .objects.alive() for normal queries,
    .objects.all_with_deleted() for reporting/audit.
    """
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()

    def delete(self, using=None, keep_parents=False):
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self):
        super().delete()

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    class Meta:
        abstract = True


# ──────────────────────────────────────────────
# PROFILE
# ──────────────────────────────────────────────

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True)
    avatar_url = models.URLField(blank=True, null=True)
    google_oauth_uid = models.CharField(max_length=255, blank=True, null=True, unique=True)
    is_super_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.email}"


# ──────────────────────────────────────────────
# TENANT
# ──────────────────────────────────────────────

class Tenant(SoftDeleteModel):  # ← soft-delete added
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    website_domain = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TenantRegistration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business_name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255)
    contact_email = models.EmailField(unique=True)
    status = models.CharField(max_length=30, choices=REGISTRATION_STATUS_CHOICES, default='pending_verification')
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True)
    tenant = models.OneToOneField(Tenant, on_delete=models.SET_NULL, null=True, blank=True, related_name='registration')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business_name} ({self.status})"


# ──────────────────────────────────────────────
# USER TENANT MEMBERSHIP
# ──────────────────────────────────────────────

class UserTenantMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    email_alerts = models.BooleanField(default=True)
    whatsapp_alerts = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='invitations_sent')

    class Meta:
        unique_together = [('user', 'tenant')]

    def __str__(self):
        return f"{self.user.email} -> {self.tenant.name} ({self.role})"


class OAuthState(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state_token = models.UUIDField(default=uuid.uuid4, unique=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OAuthState {self.state_token}"


# ──────────────────────────────────────────────
# GOOGLE ACCOUNT
# ──────────────────────────────────────────────

class GoogleAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='google_accounts')
    email = models.EmailField()
    refresh_token = models.TextField()
    is_active = models.BooleanField(default=True)
    token_updated_at = models.DateTimeField(auto_now=True)
    connected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='connected_google_accounts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('tenant', 'email')]

    def __str__(self):
        return f"{self.email} ({self.tenant.name})"


# ──────────────────────────────────────────────
# GBP PROFILE
# ──────────────────────────────────────────────

class GBPProfile(SoftDeleteModel):  # ← soft-delete added
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='gbp_profiles')
    google_account = models.ForeignKey(GoogleAccount, on_delete=models.CASCADE, related_name='profiles')
    local_admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_profiles')
    gbp_location_id = models.CharField(max_length=255, unique=True)
    business_name = models.CharField(max_length=255)
    city = models.CharField(max_length=100, blank=True)
    brand = models.CharField(max_length=20, choices=BRAND_CHOICES, default='other', db_index=True)  # ← indexed
    # avg_rating / total_reviews kept as cache fields.
    # Always use annotated querysets for reporting; these are for display only.
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    auto_respond = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'brand']),   # ← composite for dashboard grouping
            models.Index(fields=['tenant', 'is_active']),
        ]

    def __str__(self):
        return f"{self.business_name} - {self.city}"


class StaffBusinessAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    profile = models.ForeignKey(GBPProfile, on_delete=models.CASCADE, related_name='assignments')
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assignments_made')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'profile'],
                condition=models.Q(is_active=True),
                name='unique_active_assignment_per_user_profile',
            )
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.profile.business_name}"


# ──────────────────────────────────────────────
# REVIEW
# ──────────────────────────────────────────────

class Review(SoftDeleteModel):  # ← soft-delete added
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(GBPProfile, on_delete=models.CASCADE, related_name='reviews')
    gbp_review_id = models.CharField(max_length=255, unique=True)
    reviewer_name = models.CharField(max_length=255, blank=True)
    star_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]  # ← validated
    )
    review_text = models.TextField(blank=True)
    sentiment = models.CharField(                               # ← moved here from ReplyTemplate only
        max_length=10,
        choices=SENTIMENT_CHOICES,
        null=True,
        blank=True,
        db_index=True,
    )
    status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='pending', db_index=True)  # ← indexed
    review_posted_at = models.DateTimeField(db_index=True)     # ← indexed for time-series
    synced_at = models.DateTimeField(auto_now=True)
    status_changed_at = models.DateTimeField(null=True, blank=True)  # ← track when status changed (response time)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['profile', 'review_posted_at']),   # ← volume over time per profile
            models.Index(fields=['profile', 'status']),
            models.Index(fields=['star_rating']),                    # ← rating aggregations
        ]

    def save(self, *args, **kwargs):
        # Auto-stamp status_changed_at when status transitions
        if self.pk:
            try:
                old = Review.objects.get(pk=self.pk)
                if old.status != self.status:
                    from django.utils import timezone
                    self.status_changed_at = timezone.now()
            except Review.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.star_rating}star - {self.reviewer_name} @ {self.profile.business_name}"


# ──────────────────────────────────────────────
# REPLY
# ──────────────────────────────────────────────

class ReplyTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='reply_templates')
    brand = models.CharField(max_length=20, choices=BRAND_CHOICES)
    sentiment = models.CharField(max_length=10, choices=SENTIMENT_CHOICES)
    template_text = models.TextField()
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='templates_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('tenant', 'brand', 'sentiment')]

    def __str__(self):
        return f"{self.brand} / {self.sentiment} ({self.tenant.name})"


class Reply(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='reply')
    reply_text = models.TextField()
    reply_type = models.CharField(max_length=20, choices=REPLY_TYPE_CHOICES)
    replied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    posted_to_google = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    posted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.reply_type} reply -> review {self.review_id}"


# ──────────────────────────────────────────────
# ALERTS
# ──────────────────────────────────────────────

class AlertLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='alert_logs')
    sent_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='received_alerts')
    channel = models.CharField(max_length=20, choices=ALERT_CHANNEL_CHOICES)
    status = models.CharField(max_length=10, choices=ALERT_STATUS_CHOICES, db_index=True)  # ← indexed
    failure_reason = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True, db_index=True)  # ← indexed

    def __str__(self):
        return f"{self.channel} -> {self.sent_to} ({self.status})"


# ──────────────────────────────────────────────
# AUDIT LOG
# ──────────────────────────────────────────────

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='audit_logs')
    profile = models.ForeignKey(GBPProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=100, db_index=True)  # ← indexed
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.action} by {self.actor} at {self.created_at}"