# admin/admin.py
from django.contrib import admin
from .models import AdminKey, StaffKey

@admin.register(AdminKey)
class AdminKeyAdmin(admin.ModelAdmin):
    list_display = ("key", "used", "created_at")
    readonly_fields = ("created_at",)

@admin.register(StaffKey)
class StaffKeyAdmin(admin.ModelAdmin):
    list_display = ("key", "used", "created_at")
    readonly_fields = ("created_at",)
