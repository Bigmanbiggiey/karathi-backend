from django.contrib import admin
from .models import Product, ProductVariant, Order, OrderItem, AuditLog


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("name", "description")
    ordering = ("-created_at",)
    inlines = [ProductVariantInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    autocomplete_fields = ["variant"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_price", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__username", "user__email")
    ordering = ("-created_at",)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "variant", "quantity")
    search_fields = ("order__id", "variant__product__name")
    autocomplete_fields = ["order", "variant"]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "size", "price", "stock")
    search_fields = ("product__name", "size")
    list_filter = ("product__category",)
    ordering = ("-id",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "action_type", "created_at", "description")
    list_filter = ("action_type", "created_at")
    search_fields = ("user__username", "description")
    ordering = ("-created_at",)
