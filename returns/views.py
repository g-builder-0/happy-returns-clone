from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .permissions import IsMerchantOwner, IsReturnBarStaff, IsConsumerOwner
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Merchant, Consumer, Return, ReturnItem, ReturnBarLocation, ReturnLabel, ItemConditionAssessment, \
    RefundTransaction, WebhookDelivery, WebhookEndpoint
from .serializers import MerchantSerializer, ConsumerSerializer, ReturnSerializer, ReturnBarLocationSerializer, \
    ReturnLabelSerializer, ItemConditionAssessmentSerializer, RefundTransactionSerializer
from .serializers_webhooks import WebhookEndpointSerializer, WebhookDeliverySerializer


class MerchantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Merchant CRUD operations
    """
    queryset = Merchant.objects.all()
    serializer_class = MerchantSerializer


class ConsumerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Consumer CRUD operations
    """
    queryset = Consumer.objects.all()
    serializer_class = ConsumerSerializer


class ReturnViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Return CRUD operations with nested items
    """
    queryset = Return.objects.select_related('merchant', 'consumer').prefetch_related('items').all()
    serializer_class = ReturnSerializer
    permission_classes = [IsAuthenticated, IsMerchantOwner]
    filterset_fields = ['status', 'merchant']

    def get_queryset(self):
        """
        CRITICAL SECURITY:
        Automatically filter to only show returns for user's merchant.
        Prevents cross-merchant data access.
        """
        return Return.objects.filter(
            merchant=self.request.user.profile.merchant
        ).select_related('merchant', 'consumer').prefetch_related('items')

    def perform_create(self, serializer):
        """
        CRITICAL SECURITY:
        Force merchant to be the authenticated user's merchant.
        Prevents attackers from creating returns for other merchants.
        """
        serializer.save(merchant=self.request.user.profile.merchant)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a return (transition to AUTHORIZED status)"""
        return_obj = self.get_object()

        if return_obj.status != Return.Status.INITIATED:
            return Response(
                {'error': 'Can only approve returns in INITIATED status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return_obj.status = Return.Status.AUTHORIZED
        return_obj.save()

        serializer = self.get_serializer(return_obj)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a return"""
        return_obj = self.get_object()

        if return_obj.status in [Return.Status.COMPLETED, Return.Status.CANCELLED]:
            return Response(
                {'error': 'Cannot cancel completed or already cancelled returns'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return_obj.status = Return.Status.CANCELLED
        return_obj.save()

        serializer = self.get_serializer(return_obj)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a return (final status)"""
        return_obj = self.get_object()

        if return_obj.status != Return.Status.PROCESSING:
            return Response(
                {'error': 'Can only complete returns in PROCESSING status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return_obj.status = Return.Status.COMPLETED
        return_obj.completed_at = timezone.now()
        return_obj.save()

        serializer = self.get_serializer(return_obj)
        return Response(serializer.data)


class ConsumerReturnViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Consumer-facing endpoint for tracking their own returns.
    Consumers can only VIEW their returns, not create/edit them.
    """
    queryset = Return.objects.select_related('merchant', 'consumer').all()
    serializer_class = ReturnSerializer
    permission_classes = [IsAuthenticated, IsConsumerOwner]

    def get_queryset(self):
        """
        CRITICAL SECURITY:
        Consumers only see THEIR OWN returns.
        """
        return Return.objects.filter(
            consumer=self.request.user.profile
        ).select_related('merchant', 'consumer').prefetch_related('items')


class ReturnBarLocationViewSet(viewsets.ModelViewSet):
    """ViewSet for return bar locations"""
    queryset = ReturnBarLocation.objects.all()
    serializer_class = ReturnBarLocationSerializer
    filterset_fields = ['city', 'state', 'is_active', 'partner_type']


class ReturnLabelViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for return labels (read-only, labels are auto-generated)"""
    queryset = ReturnLabel.objects.select_related('return_obj').all()
    serializer_class = ReturnLabelSerializer


class ItemConditionAssessmentViewSet(viewsets.ModelViewSet):
    """ViewSet for item condition assessments"""
    queryset = ItemConditionAssessment.objects.select_related('return_item').all()
    serializer_class = ItemConditionAssessmentSerializer
    permission_classes = [IsAuthenticated, IsReturnBarStaff]


class RefundTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for refund transactions"""
    queryset = RefundTransaction.objects.select_related('return_obj').all()
    serializer_class = RefundTransactionSerializer
    filterset_fields = ['return_obj', 'status', 'refund_method']


class WebhookEndpointViewSet(viewsets.ModelViewSet):
    """
    Merchants manage their webhook endpoints.
    """
    queryset = WebhookEndpoint.objects.all()
    serializer_class = WebhookEndpointSerializer
    permission_classes = [IsAuthenticated, IsMerchantOwner]

    def get_queryset(self):
        """
        CRITICAL SECURITY:
        Merchants only see their own webhook endpoints.
        """
        return WebhookEndpoint.objects.filter(
            merchant=self.request.user.profile.merchant
        )

    def perform_create(self, serializer):
        """
        CRITICAL SECURITY:
        Force merchant to be the authenticated user's merchant.
        """
        serializer.save(merchant=self.request.user.profile.merchant)


class WebhookDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Merchants view webhook delivery logs (read-only).
    """
    queryset = WebhookDelivery.objects.select_related('webhook_endpoint').all()
    serializer_class = WebhookDeliverySerializer
    permission_classes = [IsAuthenticated, IsMerchantOwner]
    filterset_fields = ['status', 'event_type']

    def get_queryset(self):
        """
        CRITICAL SECURITY:
        Merchants only see delivery logs for their own webhooks.
        """
        return WebhookDelivery.objects.filter(
            webhook_endpoint__merchant=self.request.user.profile.merchant
        ).select_related('webhook_endpoint')