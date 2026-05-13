from rest_framework import serializers
from .models import WebhookEndpoint, WebhookDelivery


class WebhookEndpointSerializer(serializers.ModelSerializer):
    """Serializer for webhook endpoint configuration"""

    class Meta:
        model = WebhookEndpoint
        fields = [
            'id', 'merchant', 'url', 'events', 'is_active',
            'secret', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'secret']

    def create(self, validated_data):
        """Auto-generate secret on creation"""
        import secrets
        validated_data['secret'] = secrets.token_urlsafe(32)
        return super().create(validated_data)


class WebhookDeliverySerializer(serializers.ModelSerializer):
    """Serializer for webhook delivery logs"""

    class Meta:
        model = WebhookDelivery
        fields = [
            'id', 'webhook_endpoint', 'event_type', 'payload',
            'response_status', 'response_body', 'attempt_count',
            'status', 'delivered_at', 'failed_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'webhook_endpoint', 'event_type', 'payload',
            'response_status', 'response_body', 'attempt_count',
            'status', 'delivered_at', 'failed_at', 'created_at'
        ]