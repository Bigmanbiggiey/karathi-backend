# shop/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ProductVariantViewSet, OrderViewSet, AuditLogViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("variants", ProductVariantViewSet, basename="variant")
router.register("orders", OrderViewSet, basename="order")
router.register("audit-logs", AuditLogViewSet, basename="auditlog")

urlpatterns = [
    path("", include(router.urls)),
]
