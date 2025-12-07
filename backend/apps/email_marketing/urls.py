from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubscriberViewSet, SubscriberTagViewSet, MailingListViewSet,
    EmailTemplateViewSet, CampaignViewSet, AutomationWorkflowViewSet
)

router = DefaultRouter()
router.register(r'subscribers', SubscriberViewSet, basename='subscribers')
router.register(r'tags', SubscriberTagViewSet, basename='subscriber-tags')
router.register(r'lists', MailingListViewSet, basename='mailing-lists')
router.register(r'templates', EmailTemplateViewSet, basename='email-templates')
router.register(r'campaigns', CampaignViewSet, basename='campaigns')
router.register(r'automations', AutomationWorkflowViewSet, basename='automations')

urlpatterns = [
    path('', include(router.urls)),
]
