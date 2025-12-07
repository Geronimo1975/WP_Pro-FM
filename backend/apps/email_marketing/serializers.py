from rest_framework import serializers
from .models import (
    Subscriber, SubscriberTag, MailingList, EmailTemplate,
    Campaign, CampaignEmail, AutomationWorkflow, AutomationStep
)


class SubscriberTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriberTag
        fields = ['id', 'name', 'color', 'description']


class MailingListSerializer(serializers.ModelSerializer):
    subscriber_count = serializers.ReadOnlyField()

    class Meta:
        model = MailingList
        fields = ['id', 'name', 'slug', 'description', 'is_public', 'is_active', 'subscriber_count']


class SubscriberSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    open_rate = serializers.ReadOnlyField()
    click_rate = serializers.ReadOnlyField()
    lists = MailingListSerializer(many=True, read_only=True)
    tags = SubscriberTagSerializer(many=True, read_only=True)
    list_ids = serializers.PrimaryKeyRelatedField(
        queryset=MailingList.objects.all(),
        many=True,
        write_only=True,
        source='lists',
        required=False
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=SubscriberTag.objects.all(),
        many=True,
        write_only=True,
        source='tags',
        required=False
    )

    class Meta:
        model = Subscriber
        fields = [
            'id', 'email', 'first_name', 'last_name', 'company', 'full_name',
            'status', 'language', 'lists', 'tags', 'list_ids', 'tag_ids',
            'source', 'emails_sent', 'emails_opened', 'emails_clicked',
            'open_rate', 'click_rate', 'subscribed_at', 'confirmed_at'
        ]
        read_only_fields = ['status', 'emails_sent', 'emails_opened', 'emails_clicked', 'subscribed_at']


class SubscriberListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    class Meta:
        model = Subscriber
        fields = ['id', 'email', 'first_name', 'last_name', 'status', 'subscribed_at']


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'template_type', 'subject', 'preview_text',
            'html_content', 'text_content', 'is_ai_generated', 'is_active',
            'created_at', 'updated_at'
        ]


class CampaignSerializer(serializers.ModelSerializer):
    open_rate = serializers.ReadOnlyField()
    click_rate = serializers.ReadOnlyField()
    bounce_rate = serializers.ReadOnlyField()

    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'template', 'subject', 'preview_text',
            'html_content', 'text_content', 'mailing_lists', 'tags', 'exclude_tags',
            'status', 'scheduled_at', 'started_at', 'completed_at',
            'total_recipients', 'emails_sent', 'emails_delivered',
            'emails_opened', 'unique_opens', 'emails_clicked', 'unique_clicks',
            'bounces', 'unsubscribes', 'complaints',
            'open_rate', 'click_rate', 'bounce_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'status', 'started_at', 'completed_at', 'total_recipients',
            'emails_sent', 'emails_delivered', 'emails_opened', 'unique_opens',
            'emails_clicked', 'unique_clicks', 'bounces', 'unsubscribes', 'complaints'
        ]


class CampaignListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    open_rate = serializers.ReadOnlyField()
    click_rate = serializers.ReadOnlyField()

    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'status', 'total_recipients', 'emails_sent',
            'open_rate', 'click_rate', 'scheduled_at', 'created_at'
        ]


class CampaignEmailSerializer(serializers.ModelSerializer):
    subscriber_email = serializers.CharField(source='subscriber.email', read_only=True)

    class Meta:
        model = CampaignEmail
        fields = [
            'id', 'campaign', 'subscriber', 'subscriber_email', 'status',
            'sent_at', 'opened_at', 'clicked_at', 'open_count', 'click_count'
        ]


class AutomationStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationStep
        fields = ['id', 'step_type', 'order', 'config', 'template']


class AutomationWorkflowSerializer(serializers.ModelSerializer):
    steps = AutomationStepSerializer(many=True, read_only=True)

    class Meta:
        model = AutomationWorkflow
        fields = [
            'id', 'name', 'description', 'trigger_type', 'trigger_config',
            'is_active', 'steps', 'total_triggered', 'total_completed', 'created_at'
        ]


class SendCampaignSerializer(serializers.Serializer):
    """Serializer for sending a campaign"""
    campaign_id = serializers.IntegerField()
    send_now = serializers.BooleanField(default=False)
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
