from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminorVendor(BasePermission):
    """
    Allows access only to admins or staff for write operations (POST, PUT, DELETE).
    Customers and anyone else can read (GET, HEAD, OPTIONS).
    
    This is ideal for Product Views.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        
        # Write operations are restricted to authenticated admin or staff (vendor role removed)
        return request.user.is_authenticated and (
            request.user.is_superuser or 
            request.user.is_staff or 
            (hasattr(request.user, 'user_type') and request.user.user_type in ["admin", "staff"])
        )
    
class IsOwnerorAdmin(BasePermission):
    """
    Controls access for Order manipulation.
    - Admins/Staff can view all orders (list/detail) and perform actions.
    - Customers can only view/manage their own orders.
    """ 
    
    # 🟢 Method for LIST/CREATE access (runs first)
    def has_permission(self, request, view):
        # Admins/Staff/Superusers can access the order list endpoint (e.g., GET /orders/)
        if request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff or (hasattr(request.user, 'user_type') and request.user.user_type in ["admin", "staff"])):
            return True
        
        # For non-admin users, they must be authenticated to access their own list or create an order
        return request.user.is_authenticated

    # 🟢 Method for DETAIL/OBJECT access (runs second)
    def has_object_permission(self, request, view, obj):
        # Admins/Staff/Superusers can view/edit any order
        if request.user.is_superuser or request.user.is_staff or (hasattr(request.user, 'user_type') and request.user.user_type in ["admin", "staff"]):
            return True
            
        # Owner can view/manage their specific object
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        return False
