from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import KeywordViewSet, SiteAuditViewSet, BacklinkViewSet, IndexNowViewSet

router = DefaultRouter()
router.register(r'keywords', KeywordViewSet, basename='keywords')
router.register(r'audits', SiteAuditViewSet, basename='audits')
router.register(r'backlinks', BacklinkViewSet, basename='backlinks')
router.register(r'indexnow', IndexNowViewSet, basename='indexnow')

urlpatterns = [
    path('', include(router.urls)),
]
