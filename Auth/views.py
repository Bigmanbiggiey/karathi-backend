from rest_framework import generics, status, viewsets, mixins, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    LoginSerializer,
    ProfileSerializer,
    SessionSerializer,
)
from .permissions import IsAdminOrSelf
import logging

User = get_user_model()


# --- Register ---
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}", exc_info=True)
            return Response({"detail": "Registration failed"}, status=400)


# --- Login ---
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # JWT tokens
        refresh = RefreshToken.for_user(user)

        # Role-based response
        if user.user_type == "admin":
            message = f"Welcome Admin {user.username}! Redirecting to admin dashboard."
            redirect_url = "/admin/dashboard"
        elif user.user_type == "staff":
            message = f"Welcome Staff {user.username}! Redirecting to orders & products dashboard."
            redirect_url = "/staff/dashboard"
        else:
            message = f"Welcome {user.username}! Redirecting to home page."
            redirect_url = "/"

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
                "message": message,
                "redirect_url": redirect_url,
            },
            status=status.HTTP_200_OK,
        )



# --- Profile (fetch/update logged-in user) ---
class ProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or update logged-in user's profile"""
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# --- Logout (blacklist refresh token) ---
class LogoutView(APIView):
    """Invalidate a refresh token so it can’t be reused"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "Refresh token required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "Successfully logged out."},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except Exception:
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST,
            )


# --- User Management (admin can manage all users, others only self) ---
class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """User management:
    - Admins can list/update/delete all users
    - Non-admins can only see/update their own account
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSelf]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == "admin":
            return User.objects.all()
        return User.objects.filter(pk=user.pk)
    
# auth/views.py
class SessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        List sessions:
        - Regular users: only their own tokens
        - Admins: can see all users' tokens
        """
        user = request.user
        if user.user_type == "admin":
            tokens = OutstandingToken.objects.all()
        else:
            tokens = OutstandingToken.objects.filter(user=user)

        serializer = SessionSerializer(tokens, many=True)
        return Response(serializer.data)

    def delete(self, request):
        """
        Revoke sessions:
        - Regular users: only their own sessions
        - Admins: can revoke any user's sessions
        """
        session_id = request.data.get("id")
        revoke_all = request.data.get("all", False)
        target_user_id = request.data.get("user_id")  # Admin can specify user
        keep_current = request.data.get("keep_current", False)

        user = request.user

        # Determine the target user
        if target_user_id and user.user_type == "admin":
            try:
                target_user = User.objects.get(pk=target_user_id)
            except User.DoesNotExist:
                return Response({"error": "Target user not found"}, status=404)
        else:
            target_user = user

        # Revoke all sessions
        if revoke_all:
            tokens = OutstandingToken.objects.filter(user=target_user)
            for token in tokens:
                if keep_current and str(token.jti) == str(request.auth.get("jti", "")):
                    continue
                BlacklistedToken.objects.get_or_create(token=token)
            return Response({"detail": f"All sessions revoked for {target_user.username}"}, status=200)

        # Revoke single session
        elif session_id:
            try:
                token = OutstandingToken.objects.get(id=session_id, user=target_user)
                BlacklistedToken.objects.get_or_create(token=token)
                return Response({"detail": "Session revoked"}, status=200)
            except OutstandingToken.DoesNotExist:
                return Response({"error": "Session not found"}, status=404)

        return Response({"error": "Provide 'id' or 'all'"}, status=400)
    
    
logger = logging.getLogger(__name__)

