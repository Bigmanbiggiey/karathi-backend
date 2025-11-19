from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "user",
        "phone_number",
        "amount",
        "status",
        "transaction_id",   # ✅ use this instead of mpesa_receipt_number
        "created_at",       # ✅ keep created_at instead of transaction_date
    )
    list_filter = ("status", "payment_method", "created_at")  # ✅ no transaction_date
    search_fields = ("order__id", "user__username", "phone_number", "transaction_id")
    ordering = ("-created_at",)
