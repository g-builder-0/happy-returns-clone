from rest_framework import serializers
from .models import Merchant, Consumer, Return, ReturnItem


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


class ReturnItemSerializer(serializers.ModelSerializer):
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
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ReturnSerializer(serializers.ModelSerializer):
    items = ReturnItemSerializer(many=True)

    class Meta:
        model = Return
        fields = [
            'id',
            'merchant',
            'consumer',
            'order_number',
            'status',
            'authorization_code',
            'refund_amount',
            'items',
            'initiated_at',
            'completed_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'initiated_at', 'created_at', 'updated_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        return_obj = Return.objects.create(**validated_data)

        for item_data in items_data:
            ReturnItem.objects.create(return_obj=return_obj, **item_data)

        return return_obj