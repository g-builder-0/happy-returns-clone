from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MerchantViewSet, ConsumerViewSet, ReturnViewSet

router = DefaultRouter()
router.register(r'merchants', MerchantViewSet, basename='merchant')
router.register(r'consumers', ConsumerViewSet, basename='consumer')
router.register(r'returns', ReturnViewSet, basename='return')

urlpatterns = [
    path('', include(router.urls)),
]