import hmac
import hashlib
import json
import requests
from django.utils import timezone
from .models import WebhookDelivery, WebhookEndpoint


def generate_signature(payload, secret):
    """
    Generate HMAC signature for webhook payload.
    Merchant uses this to verify the webhook came from Happy Returns.
    """
    message = json.dumps(payload, sort_keys=True).encode('utf-8')
    signature = hmac.new(
        secret.encode('utf-8'),
        message,
        hashlib.sha256
    ).hexdigest()
    return signature


def send_webhook(webhook_endpoint, event_type, payload):
    """
    Send webhook to merchant's endpoint with retry tracking.
    Returns WebhookDelivery object.
    """
    # Create delivery log
    delivery = WebhookDelivery.objects.create(
        webhook_endpoint=webhook_endpoint,
        event_type=event_type,
        payload=payload,
        status=WebhookDelivery.Status.PENDING
    )

    try:
        # Generate signature
        signature = generate_signature(payload, webhook_endpoint.secret)

        # Send HTTP POST to merchant's webhook URL
        response = requests.post(
            webhook_endpoint.url,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'X-Webhook-Signature': signature,
                'X-Webhook-Event': event_type,
            },
            timeout=5  # 5 second timeout
        )

        # Log response
        delivery.response_status = response.status_code
        delivery.response_body = response.text[:1000]  # First 1000 chars
        delivery.attempt_count += 1

        # Check if successful (2xx status code)
        if 200 <= response.status_code < 300:
            delivery.status = WebhookDelivery.Status.SUCCESS
            delivery.delivered_at = timezone.now()
        else:
            delivery.status = WebhookDelivery.Status.FAILED
            delivery.failed_at = timezone.now()

        delivery.save()
        return delivery

    except requests.exceptions.Timeout:
        # Merchant's server didn't respond in time
        delivery.response_body = "Request timeout after 5 seconds"
        delivery.status = WebhookDelivery.Status.FAILED
        delivery.failed_at = timezone.now()
        delivery.attempt_count += 1
        delivery.save()
        return delivery

    except requests.exceptions.RequestException as e:
        # Network error, DNS failure, etc.
        delivery.response_body = f"Request failed: {str(e)}"
        delivery.status = WebhookDelivery.Status.FAILED
        delivery.failed_at = timezone.now()
        delivery.attempt_count += 1
        delivery.save()
        return delivery


def trigger_webhook(event_type, return_obj):
    """
    Trigger webhooks for all merchants subscribed to this event.
    Called when return status changes.
    """
    merchant = return_obj.merchant

    # Get active webhook endpoints for this merchant
    webhooks = WebhookEndpoint.objects.filter(
        merchant=merchant,
        is_active=True
    )

    for webhook in webhooks:
        # Check if merchant subscribed to this event
        if event_type in webhook.events:
            # Build payload
            payload = {
                'event': event_type,
                'return': {
                    'id': return_obj.id,
                    'authorization_code': return_obj.authorization_code,
                    'order_number': return_obj.order_number,
                    'status': return_obj.status,
                    'refund_amount': str(return_obj.refund_amount),
                },
                'timestamp': timezone.now().isoformat(),
            }

            # Send webhook
            send_webhook(webhook, event_type, payload)