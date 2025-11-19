from rest_framework import viewsets, permissions
from django.db.models import Sum, Count
from django.utils.timezone import now, timedelta

from .serializers import (
    UserSerializer, OrderSerializer, ProductSerializer,
    PaymentSerializer, AuditLogSerializer
)
from django.contrib.auth import get_user_model
from Shop.models import Order, Product, AuditLog
from Payment.models import Payment

User = get_user_model()

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == "admin"

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminUser]

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]

# Custom Admin Dashboard API
from rest_framework.decorators import action
from rest_framework.response import Response

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=["get"])
    def summary(self, request):
        today = now().date()
        last_7_days = today - timedelta(days=7)

        total_sales = Payment.objects.aggregate(total=Sum("amount"))["total"] or 0
        total_orders = Order.objects.count()
        total_users = User.objects.count()
        new_users = User.objects.filter(date_joined__gte=last_7_days).count()

        return Response({
            "total_sales": total_sales,
            "total_orders": total_orders,
            "total_users": total_users,
            "new_users_last_7_days": new_users
        })
