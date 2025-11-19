from rest_framework import permissions

class IsAdminOrSelf(permissions.BasePermission):
    """
    Admins can do anything.
    Non-admins can only view/update/delete their own account.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.user_type == "admin":
            return True
        return obj == request.user
