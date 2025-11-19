from rest_framework import serializers
from .models import Product, ProductVariant, Order, OrderItem, AuditLog
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializerForOrder(serializers.ModelSerializer):
    class Meta:
        model= User
        fields = ["id", "username", "first_name", "last_name"]

class ProductVariantSerializer(serializers.ModelSerializer):
    # Ensure price is always numeric (default 0 if None)
    price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ["id", "product", "size", "price", "stock"]

    def get_price(self, obj):
        return float(obj.price) if obj.price is not None else 0.0


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    price = serializers.SerializerMethodField()  # lowest variant price

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "category",
            "image",
            "variants",
            "price",         # added here
            "created_at",
        ]

    def get_price(self, obj):
        variants = obj.variants.all()
        if not variants.exists():
            return 0.0
        return float(min(v.price or 0 for v in variants))


class OrderItemSerializer(serializers.ModelSerializer):
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),
        source="variant",
        write_only=True,
    )

    class Meta:
        model = OrderItem
        fields = ["id", "variant", "variant_id", "quantity"]


class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializerForOrder(read_only=True)
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ["id", "user", "items", "status", "total_price", "created_at"]
        read_only_fields = ["id", "total_price", "created_at", "status"]

    def _recalculate_total(self, order):
        """Utility method to recompute order total from items."""
        total = sum(
            (item.variant.price or 0) * item.quantity
            for item in order.items.all()
        )
        order.total_price = total
        order.save(update_fields=["total_price"])
        return order

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        user = self.context["request"].user
        order = Order.objects.create(user=user, **validated_data)

        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        # recalc after creating all items
        self._recalculate_total(order)
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)

        # update status or other fields if passed
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            # Clear old items and rewrite
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)

        # recalc after updating items
        self._recalculate_total(instance)
        return instance

    def to_representation(self, instance):
        # Always recalc before returning response
        self._recalculate_total(instance)
        return super().to_representation(instance)


class RestockSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = AuditLog
        fields = "__all__"
