from django.urls import path, include
from . import admin_views, views

urlpatterns = [
    # API endpoints from PaymentViewSet
    path('initiate/', views.initiate_payment, name='initiate_payment'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('status/<int:payment_id>/', views.check_payment_status, name='payment_status'),

    # Admin/staff-only endpoints
    path("admin/list/", admin_views.list_payments, name="list_payments"),
    path("admin/<int:payment_id>/", admin_views.payment_detail, name="payment_detail"),
    path("admin/<int:payment_id>/reconcile/", admin_views.reconcile_payment, name="reconcile_payment"),
]
