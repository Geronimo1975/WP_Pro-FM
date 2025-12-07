from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MediaFileViewSet, MediaCollectionViewSet, MediaSyncLogViewSet

router = DefaultRouter()
router.register(r'files', MediaFileViewSet, basename='media-files')
router.register(r'collections', MediaCollectionViewSet, basename='media-collections')
router.register(r'sync-logs', MediaSyncLogViewSet, basename='media-sync-logs')

urlpatterns = [
    path('', include(router.urls)),
]
