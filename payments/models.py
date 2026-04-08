from django.db import models


class TransactionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    AWAITING_3DS = "awaiting_3ds", "Awaiting 3DS"
    FAILED = "failed", "Failed"


class Transaction(models.Model):
    """Persisted charge attempt. Card PAN/CVV are never stored (PCI)."""

    reference = models.CharField(max_length=255, unique=True, db_index=True)
    amount = models.CharField(max_length=32)
    currency = models.CharField(max_length=8)

    firstname = models.CharField(max_length=128)
    lastname = models.CharField(max_length=128)
    email = models.EmailField()
    phone = models.CharField(max_length=32)

    card_name = models.CharField(max_length=128)
    card_last4 = models.CharField(max_length=4, blank=True)
    exp_month = models.CharField(max_length=2)
    exp_year = models.CharField(max_length=4)

    country = models.CharField(max_length=2)
    city = models.CharField(max_length=128)
    address = models.TextField()
    zip_code = models.CharField(max_length=32)
    state = models.CharField(max_length=128)

    ip_address = models.CharField(max_length=64)
    callback_url = models.URLField(max_length=2048)
    webhook_url = models.URLField(max_length=2048, blank=True, null=True)

    status = models.CharField(
        max_length=16,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
    )
    provider_status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    provider_response = models.JSONField(null=True, blank=True)
    swipepoint_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name="SwipePoint data",
        help_text="Snapshot of request fields sent to charge API (card masked, CVV not stored).",
    )
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.reference} ({self.status})"


class SwipePointData(Transaction):
    """
    Proxy model — same DB rows as Transaction.
    Used in admin as a dedicated "SwipePoint data" section listing all charges.
    """

    class Meta:
        proxy = True
        verbose_name = "SwipePoint data"
        verbose_name_plural = "SwipePoint data"
