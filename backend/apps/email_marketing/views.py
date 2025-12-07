from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count

from .models import (
    Subscriber, SubscriberTag, MailingList, EmailTemplate,
    Campaign, CampaignEmail, AutomationWorkflow
)
from .serializers import (
    SubscriberSerializer, SubscriberListSerializer, SubscriberTagSerializer,
    MailingListSerializer, EmailTemplateSerializer,
    CampaignSerializer, CampaignListSerializer, CampaignEmailSerializer,
    AutomationWorkflowSerializer, SendCampaignSerializer
)
from .tasks import send_campaign, process_automation_trigger


class SubscriberViewSet(viewsets.ModelViewSet):
    """ViewSet for managing subscribers"""
    queryset = Subscriber.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'language', 'lists', 'tags']
    search_fields = ['email', 'first_name', 'last_name', 'company']
    ordering_fields = ['subscribed_at', 'email', 'emails_opened']

    def get_serializer_class(self):
        if self.action == 'list':
            return SubscriberListSerializer
        return SubscriberSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get subscriber statistics"""
        total = Subscriber.objects.count()
        by_status = {}
        for status_choice in Subscriber.SubscriberStatus.choices:
            by_status[status_choice[0]] = Subscriber.objects.filter(status=status_choice[0]).count()

        return Response({
            'total': total,
            'by_status': by_status,
            'active': by_status.get('active', 0),
            'growth_this_month': Subscriber.objects.filter(
                subscribed_at__month=timezone.now().month
            ).count() if 'timezone' in dir() else 0
        })

    @action(detail=True, methods=['post'])
    def unsubscribe(self, request, pk=None):
        """Unsubscribe a subscriber"""
        subscriber = self.get_object()
        subscriber.status = Subscriber.SubscriberStatus.UNSUBSCRIBED
        subscriber.unsubscribed_at = timezone.now()
        subscriber.save()
        return Response({'message': 'Subscriber unsubscribed'})

    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        """Import subscribers from CSV"""
        # Placeholder for CSV import functionality
        return Response({'message': 'Import not yet implemented'}, status=501)


class SubscriberTagViewSet(viewsets.ModelViewSet):
    """ViewSet for managing subscriber tags"""
    queryset = SubscriberTag.objects.all()
    serializer_class = SubscriberTagSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name']


class MailingListViewSet(viewsets.ModelViewSet):
    """ViewSet for managing mailing lists"""
    queryset = MailingList.objects.all()
    serializer_class = MailingListSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_public', 'is_active']

    @action(detail=True, methods=['get'])
    def subscribers(self, request, pk=None):
        """Get subscribers in a mailing list"""
        mailing_list = self.get_object()
        subscribers = mailing_list.subscribers.filter(status=Subscriber.SubscriberStatus.ACTIVE)
        serializer = SubscriberListSerializer(subscribers, many=True)
        return Response(serializer.data)


class EmailTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email templates"""
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['template_type', 'is_active']
    search_fields = ['name', 'subject']

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a template"""
        template = self.get_object()
        template.pk = None
        template.name = f"{template.name} (Copy)"
        template.save()
        serializer = self.get_serializer(template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for managing campaigns"""
    queryset = Campaign.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'mailing_lists']
    search_fields = ['name', 'subject']
    ordering_fields = ['created_at', 'scheduled_at', 'emails_sent']

    def get_serializer_class(self):
        if self.action == 'list':
            return CampaignListSerializer
        return CampaignSerializer

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send or schedule a campaign"""
        campaign = self.get_object()

        if campaign.status not in [Campaign.CampaignStatus.DRAFT, Campaign.CampaignStatus.SCHEDULED]:
            return Response(
                {'error': 'Campaign cannot be sent in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        send_now = request.data.get('send_now', False)
        scheduled_at = request.data.get('scheduled_at')

        if send_now:
            task = send_campaign.delay(campaign.id)
            return Response({
                'message': 'Campaign sending started',
                'task_id': task.id
            }, status=status.HTTP_202_ACCEPTED)
        elif scheduled_at:
            campaign.scheduled_at = scheduled_at
            campaign.status = Campaign.CampaignStatus.SCHEDULED
            campaign.save()
            return Response({'message': 'Campaign scheduled'})
        else:
            return Response(
                {'error': 'Either send_now or scheduled_at is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a sending campaign"""
        campaign = self.get_object()
        if campaign.status == Campaign.CampaignStatus.SENDING:
            campaign.status = Campaign.CampaignStatus.PAUSED
            campaign.save()
            return Response({'message': 'Campaign paused'})
        return Response(
            {'error': 'Campaign is not currently sending'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['get'])
    def emails(self, request, pk=None):
        """Get campaign email details"""
        campaign = self.get_object()
        emails = campaign.emails.all()[:100]
        serializer = CampaignEmailSerializer(emails, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get campaign statistics"""
        from django.db.models import Sum, Avg

        campaigns = Campaign.objects.filter(status=Campaign.CampaignStatus.SENT)
        stats = campaigns.aggregate(
            total_sent=Sum('emails_sent'),
            total_opened=Sum('unique_opens'),
            total_clicked=Sum('unique_clicks'),
            avg_open_rate=Avg('unique_opens') * 100 / Avg('emails_delivered') if campaigns.exists() else 0
        )

        return Response({
            'total_campaigns': campaigns.count(),
            'total_emails_sent': stats['total_sent'] or 0,
            'total_opens': stats['total_opened'] or 0,
            'total_clicks': stats['total_clicked'] or 0,
        })


class AutomationWorkflowViewSet(viewsets.ModelViewSet):
    """ViewSet for managing automation workflows"""
    queryset = AutomationWorkflow.objects.all()
    serializer_class = AutomationWorkflowSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['trigger_type', 'is_active']

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a workflow"""
        workflow = self.get_object()
        workflow.is_active = True
        workflow.save()
        return Response({'message': 'Workflow activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a workflow"""
        workflow = self.get_object()
        workflow.is_active = False
        workflow.save()
        return Response({'message': 'Workflow deactivated'})


# Import timezone at module level
from django.utils import timezone
