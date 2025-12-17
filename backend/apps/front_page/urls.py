"""
URL routing for Front Page management API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SliderRevolutionViewSet,
    SlideViewSet,
    SlideLayerViewSet,
    HomepageSectionViewSet,
    HomepageSectionItemViewSet,
    FrontPageSettingsViewSet,
)

app_name = 'front_page'

router = DefaultRouter()
router.register(r'sliders', SliderRevolutionViewSet, basename='slider')
router.register(r'slides', SlideViewSet, basename='slide')
router.register(r'layers', SlideLayerViewSet, basename='layer')
router.register(r'sections', HomepageSectionViewSet, basename='section')
router.register(r'section-items', HomepageSectionItemViewSet, basename='section-item')
router.register(r'settings', FrontPageSettingsViewSet, basename='settings')

urlpatterns = [
    path('', include(router.urls)),
]
