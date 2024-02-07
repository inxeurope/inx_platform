from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),  # Keep the admin URLs first
    path("members/", include('django.contrib.auth.urls')),
    # path("members/", include('inx_platform_members.urls')),
    path("", include('inx_platform_app.urls')),
    # path("", include('admin_tabler.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
