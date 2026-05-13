from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Return, RefundTransaction
from .webhook_utils import trigger_webhook


@receiver(post_save, sender=Return)
def return_saved(sender, instance, created, **kwargs):
    """
    Trigger webhooks when Return is created or status changes.
    """
    if created:
        # New return was created
        trigger_webhook('RETURN_CREATED', instance)

    elif instance.status == Return.Status.AUTHORIZED:
        # Return was approved by merchant
        trigger_webhook('RETURN_APPROVED', instance)

    elif instance.status == Return.Status.DROPPED_OFF:
        # Consumer dropped off return at return bar
        trigger_webhook('RETURN_DROPPED_OFF', instance)

    elif instance.status == Return.Status.COMPLETED:
        # Return fully completed
        trigger_webhook('RETURN_COMPLETED', instance)

    elif instance.status == Return.Status.CANCELLED:
        # Return was cancelled
        trigger_webhook('RETURN_CANCELLED', instance)


@receiver(post_save, sender=RefundTransaction)
def refund_saved(sender, instance, created, **kwargs):
    """
    Trigger webhook when refund is completed.
    """
    if instance.status == RefundTransaction.Status.COMPLETED:
        trigger_webhook('REFUND_COMPLETED', instance)