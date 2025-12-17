"""
URL configuration for WP_Pro-FM project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/media/', include('apps.media.urls')),
    path('api/content/', include('apps.content.urls')),
    path('api/seo/', include('apps.seo.urls')),
    path('api/email/', include('apps.email_marketing.urls')),
    path('api/front-page/', include('apps.front_page.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
