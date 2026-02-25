from rest_framework import serializers

from .models import Merchant, Consumer, Return, ReturnItem, ReturnBarLocation, ReturnLabel, RefundTransaction, \
    ItemConditionAssessment


class MerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = ['id', 'name', 'email', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        # Exclude api_key for security


class ConsumerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consumer
        fields = ['id', 'email', 'first_name', 'last_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReturnBarLocationSerializer(serializers.ModelSerializer):
    """Serializer for return bar locations"""

    class Meta:
        model = ReturnBarLocation
        fields = [
            'id',
            'name',
            'partner_type',
            'address',
            'city',
            'state',
            'zip_code',
            'latitude',
            'longitude',
            'is_active',
            'hours_of_operation',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_hours_of_operation(self, value):
        """Validate hours_of_operation JSON format"""
        if value:
            valid_days = ['monday', 'tuesday', 'wednesday', 'thursday',
                          'friday', 'saturday', 'sunday']
            for day in value.keys():
                if day.lower() not in valid_days:
                    raise serializers.ValidationError(
                        f"Invalid day: {day}. Must be one of {valid_days}"
                    )
        return value


class ReturnLabelSerializer(serializers.ModelSerializer):
    """Serializer for return shipping labels"""

    class Meta:
        model = ReturnLabel
        fields = [
            'id',
            'return_obj',
            'tracking_number',
            'carrier',
            'label_url',
            'qr_code',
            'generated_at',
            'expires_at'
        ]
        read_only_fields = ['id', 'generated_at', 'qr_code', 'label_url']

    def validate(self, data):
        """Validate that expires_at is in the future"""
        from django.utils import timezone

        if 'expires_at' in data:
            if data['expires_at'] <= timezone.now():
                raise serializers.ValidationError(
                    {'expires_at': 'Expiration date must be in the future'}
                )

        return data

    def create(self, validated_data):
        """Auto-generate QR code when creating label"""
        import uuid

        # Generate unique QR code
        validated_data['qr_code'] = f"RET-{uuid.uuid4().hex[:12].upper()}"

        # In production, you'd generate label_url via shipping API (Shippo/EasyPost)
        # For now, we'll create a placeholder
        validated_data['label_url'] = f"https://labels.example.com/{validated_data['tracking_number']}.pdf"

        return super().create(validated_data)


class ItemConditionAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for item condition assessments"""

    class Meta:
        model = ItemConditionAssessment
        fields = [
            'id', 'return_item', 'assessed_by', 'condition',
            'notes', 'photo_urls', 'assessed_at', 'assessor_name'
        ]
        read_only_fields = ['id', 'assessed_at']

    def validate_photo_urls(self, value):
        if value:
            for url in value:
                if not url.startswith(('http://', 'https://')):
                    raise serializers.ValidationError(
                        f"Invalid photo URL: {url}"
                    )
        return value


class ReturnItemSerializer(serializers.ModelSerializer):
    assessments = ItemConditionAssessmentSerializer(many=True, read_only=True)

    class Meta:
        model = ReturnItem
        fields = [
            'id',
            'product_name',
            'product_sku',
            'quantity',
            'unit_price',
            'return_reason',
            'condition',
            'assessments',  # Now includes nested assessments!
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RefundTransactionSerializer(serializers.ModelSerializer):
    """Serializer for refund transactions"""

    class Meta:
        model = RefundTransaction
        fields = [
            'id',
            'return_obj',
            'amount',
            'refund_method',
            'transaction_id',
            'status',
            'initiated_at',
            'completed_at',
            'failure_reason'
        ]
        read_only_fields = ['id', 'initiated_at']

    def validate(self, data):
        """Validate refund amount doesn't exceed return total"""
        from django.db.models import Sum

        return_obj = data.get('return_obj')
        amount = data.get('amount')

        if return_obj and amount:
            # Get total of completed refunds for this return
            total_refunded = RefundTransaction.objects.filter(
                return_obj=return_obj,
                status=RefundTransaction.Status.COMPLETED
            ).aggregate(Sum('amount'))['amount__sum'] or 0

            # Check if adding this refund would exceed return amount
            if total_refunded + amount > return_obj.refund_amount:
                raise serializers.ValidationError(
                    f"Total refunds (${total_refunded + amount}) would exceed "
                    f"return amount (${return_obj.refund_amount})"
                )

        return data


class ReturnSerializer(serializers.ModelSerializer):
    items = ReturnItemSerializer(many=True)
    return_bar_location = ReturnBarLocationSerializer(read_only=True)
    label = ReturnLabelSerializer(read_only=True)
    refund_transactions = RefundTransactionSerializer(many=True, read_only=True)
    total_refunded = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Return
        fields = [
            'id', 'merchant', 'consumer', 'return_bar_location',
            'dropped_off_at', 'expected_refund_date', 'order_number',
            'status', 'authorization_code', 'refund_amount', 'items',
            'label', 'refund_transactions', 'total_refunded', 'is_overdue',
            'initiated_at', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'initiated_at', 'created_at', 'updated_at']

    def get_total_refunded(self, obj):
        """Calculate total of completed refunds"""
        from django.db.models import Sum
        total = obj.refund_transactions.filter(
            status=RefundTransaction.Status.COMPLETED
        ).aggregate(Sum('amount'))['amount__sum']
        return float(total) if total else 0.0

    def get_is_overdue(self, obj):
        """Check if return is past expected refund date"""
        from django.utils import timezone
        if obj.expected_refund_date:
            return timezone.now().date() > obj.expected_refund_date
        return False

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        return_obj = Return.objects.create(**validated_data)
        for item_data in items_data:
            ReturnItem.objects.create(return_obj=return_obj, **item_data)
        return return_obj