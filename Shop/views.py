from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Product, ProductVariant, Order, AuditLog
from .serializers import (
    ProductSerializer,
    ProductVariantSerializer,
    OrderSerializer,
    RestockSerializer,
    AuditLogSerializer,
)

def is_admin_or_staff(user):
    """Helper function to check if a user is superuser, staff, or has the admin/staff user_type."""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser or user.is_staff:
        return True
    
    # Assuming 'user_type' field exists on the custom User model
    return hasattr(user, 'user_type') and user.user_type in ['admin', 'staff']


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().prefetch_related('variants')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] 

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def restock(self, request, pk=None):
        """Restock a product variant (Admin/Staff only)."""
        # 🟢 PERMISSION CHECK: Only authorized staff can restock
        if not is_admin_or_staff(request.user):
            raise PermissionDenied("You do not have permission to restock products.")
            
        product = self.get_object()
        serializer = RestockSerializer(data=request.data)
        
        if serializer.is_valid():
            variant_id = serializer.validated_data['variant_id']
            amount = serializer.validated_data['amount']
            
            try:
                variant = product.variants.get(id=variant_id)
                
                with transaction.atomic():
                    variant.stock += amount
                    variant.save()
                    
                    # Create audit log
                    AuditLog.objects.create(
                        user=request.user,
                        action_type="update", # Consider using a more specific action_type like 'product_restock'
                        description=f"Restocked {product.name} variant {variant.size or 'default'} by {amount}. New stock: {variant.stock}"
                    )
                
                return Response({
                    "detail": "Restocked successfully",
                    "new_stock": variant.stock
                })
            except ProductVariant.DoesNotExist:
                return Response(
                    {"detail": "Variant not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all().select_related('product')
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class OrderViewSet(viewsets.ModelViewSet):
    # Eagerly load user and the new 'last_modified_by' field for efficiency
    queryset = Order.objects.all().select_related("user", "last_modified_by").prefetch_related("items__variant")
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        """Filter orders based on user role (Admin/Staff see all, Customer sees their own)"""
        user = self.request.user
        if user.is_authenticated and is_admin_or_staff(user):
            # Admin/Staff see all orders
            return self.queryset.all()
        # Customer sees only their own orders
        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        # Audit log for creation
        order_instance = serializer.instance
        AuditLog.objects.create(
            user=self.request.user,
            order=order_instance,
            action_type="order_create",
            description=f"Order #{order_instance.id} created by customer {self.request.user.username}."
        )


    @action(detail=True, methods=["post"])
    def set_status(self, request, pk=None):
        """Change order status (Admin/Staff only) and handle stock deduction on completion."""
        # 🟢 PERMISSION CHECK: Only Admin/Staff/Superuser can change status
        if not is_admin_or_staff(request.user):
            raise PermissionDenied("Only administrative staff can change order status.")
            
        order = self.get_object()
        new_status = request.data.get("status")
        user = request.user

        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({"detail": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        if order.status == new_status:
            return Response({"detail": f"Order status is already {new_status}"}, status=status.HTTP_200_OK)

        old_status = order.status
        
        with transaction.atomic():
            if new_status == "completed":
                if old_status == "completed":
                    pass 
                elif old_status == "cancelled":
                    raise ValidationError({"detail": "Cannot complete a cancelled order."})
                else:
                    # Deduct stock for all items
                    for item in order.items.all():
                        if item.variant.stock < item.quantity:
                            raise ValidationError({
                                "detail": f"Not enough stock for {item.variant.product.name} ({item.variant.size}). Required: {item.quantity}, Available: {item.variant.stock}"
                            })
                        item.variant.stock -= item.quantity
                        item.variant.save()

            # 🟢 AUDIT STEP 1: Update order fields
            order.status = new_status
            order.last_modified_by = user
            order.save(update_fields=["status", "last_modified_by"])

            # 🟢 AUDIT STEP 2: Create detailed audit log entry
            AuditLog.objects.create(
                user=user,
                order=order,
                action_type="order_status_update",
                description=f"Status changed from '{old_status}' to '{new_status}'. Handled by: {user.username} (ID: {user.id})."
            )

        return Response(OrderSerializer(order, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancels an order (Admin/Staff only)."""
        # 🟢 PERMISSION CHECK: Only Admin/Staff/Superuser can cancel an order
        if not is_admin_or_staff(request.user):
            raise PermissionDenied("Only administrative staff can cancel orders.")
            
        order = self.get_object()
        user = request.user
        
        if order.status in ('completed', 'cancelled'):
            # Already finalized or cancelled, prevent cancellation
            raise ValidationError({"detail": f"Order status is already {order.status} and cannot be cancelled."})

        old_status = order.status
        
        with transaction.atomic():
            # 🟢 AUDIT STEP 1: Update order fields
            order.status = 'cancelled'
            order.last_modified_by = user
            order.save(update_fields=["status", "last_modified_by"])

            # 🟢 AUDIT STEP 2: Create detailed audit log entry
            AuditLog.objects.create(
                user=user,
                order=order,
                action_type='order_cancel',
                description=f"Order explicitly cancelled (from status '{old_status}'). Handled by: {user.username} (ID: {user.id})."
            )
        
        return Response(OrderSerializer(order, context={"request": request}).data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    # We select the related user and order objects for display efficiency
    queryset = AuditLog.objects.all().select_related("user", "order").order_by('-created_at')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Only admins/staff can see audit logs"""
        user = self.request.user
        if is_admin_or_staff(user):
            return self.queryset
        # Non-admin/staff users see nothing
        return AuditLog.objects.none()
