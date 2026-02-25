from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MerchantViewSet, ConsumerViewSet, ReturnViewSet, ReturnBarLocationViewSet, ReturnLabelViewSet, \
    ItemConditionAssessmentViewSet, RefundTransactionViewSet

router = DefaultRouter()
router.register(r'merchants', MerchantViewSet, basename='merchant')
router.register(r'consumers', ConsumerViewSet, basename='consumer')
router.register(r'returns', ReturnViewSet, basename='return')
router.register(r'return-bar-locations', ReturnBarLocationViewSet, basename='returnbarlocation')
router.register(r'return-labels', ReturnLabelViewSet, basename='returnlabel')
router.register(r'assessments', ItemConditionAssessmentViewSet, basename='assessment')
router.register(r'refund-transactions', RefundTransactionViewSet, basename='refundtransaction')

urlpatterns = [
    path('', include(router.urls)),
]
