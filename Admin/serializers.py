from rest_framework import serializers
from django.contrib.auth import get_user_model
from Shop.models import Order, Product, AuditLog
from Payment.models import Payment

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","username", "email", "user_type", "date_joined"]

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Order
        fields = "__all__"

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"

class PaymentSerializer(serializers.ModelSerializer):
    order = serializers.StringRelatedField

    class Meta:
        model = Payment
        fields = "__all__"

class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = AuditLog
        fields = "__all__"        