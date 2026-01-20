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
    STATUS_INITIATED = 'INITIATED'
    STATUS_AUTHORIZED = 'AUTHORIZED'
    STATUS_DROPPED_OFF = 'DROPPED_OFF'
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_INITIATED, 'Initiated'),
        (STATUS_AUTHORIZED, 'Authorized'),
        (STATUS_DROPPED_OFF, 'Dropped Off'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    # Relationships
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='returns')
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='returns')

    # Return details
    order_number = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INITIATED)
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
    REASON_DEFECTIVE = 'DEFECTIVE'
    REASON_WRONG_ITEM = 'WRONG_ITEM'
    REASON_NOT_AS_DESCRIBED = 'NOT_AS_DESCRIBED'
    REASON_UNWANTED = 'UNWANTED'
    REASON_OTHER = 'OTHER'

    REASON_CHOICES = [
        (REASON_DEFECTIVE, 'Defective'),
        (REASON_WRONG_ITEM, 'Wrong Item'),
        (REASON_NOT_AS_DESCRIBED, 'Not As Described'),
        (REASON_UNWANTED, 'Unwanted'),
        (REASON_OTHER, 'Other'),
    ]

    # Condition choices
    CONDITION_NEW = 'NEW'
    CONDITION_LIKE_NEW = 'LIKE_NEW'
    CONDITION_GOOD = 'GOOD'
    CONDITION_DAMAGED = 'DAMAGED'

    CONDITION_CHOICES = [
        (CONDITION_NEW, 'New'),
        (CONDITION_LIKE_NEW, 'Like New'),
        (CONDITION_GOOD, 'Good'),
        (CONDITION_DAMAGED, 'Damaged'),
    ]

    # Relationships
    return_obj = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')

    # Item details
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    return_reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.product_name} (x{self.quantity})"