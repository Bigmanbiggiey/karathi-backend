from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from Shop.models import Order
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from Admin.models import AdminKey, StaffKey

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Basic user info serializer (safe to expose)."""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "user_type",
            "billing_address",
        ]
        read_only_fields = ["id", "email", "user_type"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    admin_key = serializers.CharField(write_only=True, required=False)
    staff_key = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "user_type",
            "billing_address",
            "admin_key",
            "staff_key",
        ]

    def validate(self, data):
        user_type = data.get("user_type")
        
        # Enforce billing_address for customers
        if user_type == "customer" and not data.get("billing_address"):
            raise serializers.ValidationError({"billing_address": "Billing address is required for customers."})

        # Enforce keys for staff/admin
        if user_type == "admin":
            key = data.get("admin_key")
            if not key or not AdminKey.objects.filter(key=key, used=False).exists():
                raise serializers.ValidationError({"admin_key": "Invalid or missing admin key."})
        elif user_type == "staff":
            key = data.get("staff_key")
            if not key or not StaffKey.objects.filter(key=key, used=False).exists():
                raise serializers.ValidationError({"staff_key": "Invalid or missing staff key."})

        return data

    def create(self, validated_data):
        user_type = validated_data.get("user_type", "customer")
    
        # Remove keys from validated_data BEFORE creating user
        admin_key = validated_data.pop("admin_key", None)
        staff_key = validated_data.pop("staff_key", None)
    
    # Mark key as used if applicable
        if user_type == "admin" and admin_key:
            AdminKey.objects.filter(key=admin_key).update(used=True)
        elif user_type == "staff" and staff_key:
            StaffKey.objects.filter(key=staff_key).update(used=True)
    
    # Extract password
        password = validated_data.pop("password")
    
    # Create user with remaining fields
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=password,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            user_type=user_type,
            billing_address=validated_data.get("billing_address", ""),
        )
    
        return user


class LoginSerializer(serializers.Serializer):
    """Handles login with email + password."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        # Authenticate directly with email (USERNAME_FIELD="email")
        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=password
        )

        if not user:
            raise serializers.ValidationError("Invalid email or password")

        data["user"] = user
        return data


class ProfileSerializer(serializers.ModelSerializer):
    """Returns profile details + purchase history for customers."""
    purchase_history = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "billing_address",
            "purchase_history",
        ]
        read_only_fields = ["purchase_history", "email"]

    def get_purchase_history(self, obj):
        orders = Order.objects.filter(user=obj).order_by("-created_at")
        history = []

        for order in orders:
            items_data = []
            for item in order.items.all():  # assumes related_name="items" in OrderItem
                items_data.append({
                    "product": item.variant.product.name,
                    "variant": item.variant.size or "Default",
                    "quantity": item.quantity,
                    "price": item.variant.price,
                })

            history.append({
                "order_id": order.id,
                "status": order.status,
                "total_price": order.total_price,
                "created_at": order.created_at,
                "items": items_data,
            })

        return history

class SessionSerializer(serializers.ModelSerializer):
    blacklisted = serializers.SerializerMethodField()

    class Meta:
        model = OutstandingToken
        fields = ["id", "jti", "created_at", "expires_at", "blacklisted"]

    def get_blacklisted(self, obj):
        return BlacklistedToken.objects.filter(token=obj).exists()