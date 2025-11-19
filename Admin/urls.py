from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, OrderViewSet, ProductViewSet,
    PaymentViewSet, AuditLogViewSet, DashboardViewSet
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="admin-users")
router.register("orders", OrderViewSet, basename="admin-orders")
router.register("products", ProductViewSet, basename="admin-products")
router.register("payments", PaymentViewSet, basename="admin-payments")
router.register("audit-logs", AuditLogViewSet, basename="admin-auditlogs")
router.register("dashboard", DashboardViewSet, basename="admin-dashboard")

urlpatterns = router.urls
