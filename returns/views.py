from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Merchant, Consumer, Return, ReturnItem, ReturnBarLocation, ReturnLabel, ItemConditionAssessment, \
    RefundTransaction
from .serializers import MerchantSerializer, ConsumerSerializer, ReturnSerializer, ReturnBarLocationSerializer, \
    ReturnLabelSerializer, ItemConditionAssessmentSerializer, RefundTransactionSerializer


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
    filterset_fields = ['status', 'merchant']

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


class RefundTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for refund transactions"""
    queryset = RefundTransaction.objects.select_related('return_obj').all()
    serializer_class = RefundTransactionSerializer
    filterset_fields = ['return_obj', 'status', 'refund_method']
