from django.db import models


class Merchant(models.Model):
    """Merchant/business that uses the returns platform"""
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    api_key = models.CharField(max_length=100, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Consumer(models.Model):
    """End customer initiating returns"""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Return(models.Model):
    """Main return transaction"""

    # Status choices
    class Status(models.TextChoices):
        INITIATED = 'INITIATED', 'Initiated'
        AUTHORIZED = 'AUTHORIZED', 'Authorized'
        DROPPED_OFF = 'DROPPED_OFF', 'Dropped Off'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'



    # Relationships
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='returns')
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='returns')

    return_bar_location = models.ForeignKey(
        'ReturnBarLocation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returns'
    )
    dropped_off_at = models.DateTimeField(null=True, blank=True)
    expected_refund_date = models.DateField(null=True, blank=True)

    # Return details
    order_number = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)
    authorization_code = models.CharField(max_length=50, unique=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['merchant', 'status']),
            models.Index(fields=['authorization_code']),
        ]

    def __str__(self):
        return f"Return {self.authorization_code} - {self.status}"


class ReturnItem(models.Model):
    """Individual items within a return"""

    # Return reason choices
    class ReturnReason(models.TextChoices):
        DEFECTIVE = 'DEFECTIVE', 'Defective'
        WRONG_ITEM = 'WRONG_ITEM', 'Wrong Item'
        NOT_AS_DESCRIBED = 'NOT_AS_DESCRIBED', 'Not As Described'
        UNWANTED = 'UNWANTED', 'Unwanted'
        OTHER = 'OTHER', 'Other'

    # Condition choices
    class Condition(models.TextChoices):
        NEW = 'NEW', 'New'
        LIKE_NEW = 'LIKE_NEW', 'Like New'
        GOOD = 'GOOD', 'Good'
        DAMAGED = 'DAMAGED', 'Damaged'

    # Relationships
    return_obj = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')

    # Item details
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    return_reason = models.CharField(max_length=20, choices=ReturnReason.choices)
    condition = models.CharField(max_length=20, choices=Condition.choices, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.product_name} (x{self.quantity})"


class ReturnBarLocation(models.Model):
    """Physical locations where consumers can drop off returns"""

    class PartnerType(models.TextChoices):
        STAPLES = 'STAPLES', 'Staples'
        PAPER_SOURCE = 'PAPER_SOURCE', 'Paper Source'
        FEDEX_OFFICE = 'FEDEX_OFFICE', 'FedEx Office'
        UPS_STORE = 'UPS_STORE', 'UPS Store'

    name = models.CharField(max_length=255)
    partner_type = models.CharField(max_length=20, choices=PartnerType.choices)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)  # US state code
    zip_code = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    hours_of_operation = models.JSONField(default=dict, blank=True)  # {"monday": "9-5", ...}
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['city', 'name']
        indexes = [
            models.Index(fields=['city', 'state', 'is_active']),
            models.Index(fields=['zip_code']),
        ]

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"


class ReturnLabel(models.Model):
    """Shipping label and QR code for return processing"""

    class Carrier(models.TextChoices):
        UPS = 'UPS', 'UPS'
        FEDEX = 'FEDEX', 'FedEx'
        USPS = 'USPS', 'USPS'
        DHL = 'DHL', 'DHL'

    return_obj = models.OneToOneField(Return, on_delete=models.CASCADE, related_name='label')
    tracking_number = models.CharField(max_length=100, unique=True)
    carrier = models.CharField(max_length=10, choices=Carrier.choices)
    label_url = models.URLField(max_length=500, blank=True)  # Link to printable label
    qr_code = models.CharField(max_length=255, unique=True)  # QR code data for scanning
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"Label {self.tracking_number} ({self.carrier})"

    def clean(self):
        """Validate that expires_at is after generated_at"""
        from django.core.exceptions import ValidationError
        if self.expires_at and self.generated_at and self.expires_at <= self.generated_at:
            raise ValidationError('Expiration date must be after generation date')


class ItemConditionAssessment(models.Model):
    """Formal assessment of returned item condition"""

    class AssessedBy(models.TextChoices):
        RETURN_BAR = 'RETURN_BAR', 'Return Bar Staff'
        MERCHANT_WAREHOUSE = 'MERCHANT_WAREHOUSE', 'Merchant Warehouse'
        AUTOMATED = 'AUTOMATED', 'Automated System'

    class Condition(models.TextChoices):
        NEW = 'NEW', 'New'
        LIKE_NEW = 'LIKE_NEW', 'Like New'
        GOOD = 'GOOD', 'Good'
        DAMAGED = 'DAMAGED', 'Damaged'
        UNSELLABLE = 'UNSELLABLE', 'Unsellable'

    return_item = models.ForeignKey(
        ReturnItem,
        on_delete=models.CASCADE,
        related_name='assessments'
    )
    assessed_by = models.CharField(max_length=20, choices=AssessedBy.choices)
    condition = models.CharField(max_length=20, choices=Condition.choices)
    notes = models.TextField(blank=True)
    photo_urls = models.JSONField(default=list, blank=True)  # List of photo URLs
    assessed_at = models.DateTimeField(auto_now_add=True)
    assessor_name = models.CharField(max_length=100, blank=True)  # Staff member name

    class Meta:
        ordering = ['-assessed_at']

    def __str__(self):
        return f"{self.return_item.product_name} - {self.condition} ({self.assessed_by})"


class RefundTransaction(models.Model):
    """Refund payment processing record"""

    class RefundMethod(models.TextChoices):
        ORIGINAL_PAYMENT = 'ORIGINAL_PAYMENT', 'Original Payment Method'
        STORE_CREDIT = 'STORE_CREDIT', 'Store Credit'
        CHECK = 'CHECK', 'Check'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        REVERSED = 'REVERSED', 'Reversed'

    return_obj = models.ForeignKey(
        Return,
        on_delete=models.CASCADE,
        related_name='refund_transactions'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    refund_method = models.CharField(max_length=20, choices=RefundMethod.choices)
    transaction_id = models.CharField(max_length=100, unique=True)  # External payment processor ID
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-initiated_at']

    def __str__(self):
        return f"Refund ${self.amount} - {self.status} ({self.transaction_id})"

    def clean(self):
        """Validate that total refunds don't exceed return amount"""
        from django.core.exceptions import ValidationError
        from django.db.models import Sum

        # Get total of all completed refunds for this return (excluding this one)
        total_refunded = RefundTransaction.objects.filter(
            return_obj=self.return_obj,
            status=RefundTransaction.Status.COMPLETED
        ).exclude(id=self.id).aggregate(Sum('amount'))['amount__sum'] or 0

        # Add this refund amount
        total_with_this = total_refunded + self.amount

        if total_with_this > self.return_obj.refund_amount:
            raise ValidationError(
                f'Total refunds (${total_with_this}) would exceed return amount (${self.return_obj.refund_amount})'
            )