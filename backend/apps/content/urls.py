from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PostViewSet, CategoryViewSet, TagViewSet,
    ContentTemplateViewSet, ContentGenerationJobViewSet
)

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='posts')
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'templates', ContentTemplateViewSet, basename='templates')
router.register(r'jobs', ContentGenerationJobViewSet, basename='generation-jobs')

urlpatterns = [
    path('', include(router.urls)),
]
