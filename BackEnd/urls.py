from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/admin/", include("Admin.urls")),
    path("api/auth/", include("Auth.urls")),
    path("api/payment/", include("Payment.urls")),
    path("api/shop/", include("Shop.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
