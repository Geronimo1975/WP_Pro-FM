from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from .models import (
    Subscriber, SubscriberTag, MailingList, EmailTemplate,
    Campaign, CampaignEmail, AutomationWorkflow, AutomationStep
)


@admin.register(Subscriber)
class SubscriberAdmin(ModelAdmin):
    list_display = [
        'email', 'full_name', 'status_display', 'language_display',
        'emails_sent', 'open_rate', 'subscribed_at'
    ]
    list_filter = ['status', 'language', 'lists', 'tags', 'subscribed_at']
    list_filter_submit = True
    search_fields = ['email', 'first_name', 'last_name', 'company']
    filter_horizontal = ['lists', 'tags']
    readonly_fields = [
        'emails_sent', 'emails_opened', 'emails_clicked',
        'last_opened', 'last_clicked', 'subscribed_at', 'confirmed_at'
    ]
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': ('email', 'first_name', 'last_name', 'company', 'status')
        }),
        ('Preferences', {
            'fields': ('language', 'lists', 'tags')
        }),
        ('Engagement', {
            'fields': (
                'emails_sent', 'emails_opened', 'emails_clicked',
                'last_opened', 'last_clicked'
            ),
            'classes': ('collapse',)
        }),
        ('Source & Tracking', {
            'fields': ('source', 'ip_address', 'subscribed_at', 'confirmed_at'),
            'classes': ('collapse',)
        }),
    )

    @display(description="Status", ordering="status", label=True)
    def status_display(self, obj):
        colors = {
            'subscribed': 'success',
            'unsubscribed': 'danger',
            'pending': 'warning',
            'bounced': 'danger',
        }
        return obj.status.title() if obj.status else '-', colors.get(obj.status, 'secondary')

    @display(description="Lang", ordering="language", label=True)
    def language_display(self, obj):
        return obj.language.upper() if obj.language else '-', "secondary"


@admin.register(SubscriberTag)
class SubscriberTagAdmin(ModelAdmin):
    list_display = ['name', 'color', 'created_at']
    search_fields = ['name']
    list_per_page = 25


@admin.register(MailingList)
class MailingListAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'subscriber_count', 'visibility_status', 'active_status']
    list_filter = ['is_public', 'is_active']
    list_filter_submit = True
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 25

    @display(description="Visibility", label=True)
    def visibility_status(self, obj):
        if obj.is_public:
            return "Public", "info"
        return "Private", "secondary"

    @display(description="Active", label=True)
    def active_status(self, obj):
        if obj.is_active:
            return "Active", "success"
        return "Inactive", "secondary"


@admin.register(EmailTemplate)
class EmailTemplateAdmin(ModelAdmin):
    list_display = ['name', 'template_type_display', 'subject', 'active_status', 'updated_at']
    list_filter = ['template_type', 'is_active', 'is_ai_generated']
    list_filter_submit = True
    search_fields = ['name', 'subject']
    list_per_page = 25

    @display(description="Type", ordering="template_type", label=True)
    def template_type_display(self, obj):
        return obj.template_type.title() if obj.template_type else '-', "secondary"

    @display(description="Status", label=True)
    def active_status(self, obj):
        if obj.is_active:
            return "Active", "success"
        return "Inactive", "secondary"


@admin.register(Campaign)
class CampaignAdmin(ModelAdmin):
    list_display = [
        'name', 'status_display', 'total_recipients', 'emails_sent',
        'open_rate', 'click_rate', 'scheduled_at'
    ]
    list_filter = ['status', 'mailing_lists', 'created_at']
    list_filter_submit = True
    search_fields = ['name', 'subject']
    filter_horizontal = ['mailing_lists', 'tags', 'exclude_tags']
    readonly_fields = [
        'total_recipients', 'emails_sent', 'emails_delivered',
        'emails_opened', 'unique_opens', 'emails_clicked', 'unique_clicks',
        'bounces', 'unsubscribes', 'complaints', 'started_at', 'completed_at'
    ]
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': ('name', 'template', 'status')
        }),
        ('Content', {
            'fields': ('subject', 'preview_text', 'html_content', 'text_content')
        }),
        ('Recipients', {
            'fields': ('mailing_lists', 'tags', 'exclude_tags')
        }),
        ('Schedule', {
            'fields': ('scheduled_at', 'started_at', 'completed_at')
        }),
        ('Metrics', {
            'fields': (
                'total_recipients', 'emails_sent', 'emails_delivered',
                'emails_opened', 'unique_opens', 'emails_clicked', 'unique_clicks',
                'bounces', 'unsubscribes', 'complaints'
            ),
            'classes': ('collapse',)
        }),
    )

    @display(description="Status", ordering="status", label=True)
    def status_display(self, obj):
        colors = {
            'draft': 'secondary',
            'scheduled': 'warning',
            'sending': 'info',
            'sent': 'success',
            'paused': 'warning',
            'cancelled': 'danger',
        }
        return obj.status.title() if obj.status else '-', colors.get(obj.status, 'secondary')


@admin.register(CampaignEmail)
class CampaignEmailAdmin(ModelAdmin):
    list_display = ['campaign', 'subscriber', 'status_display', 'sent_at', 'opened_at']
    list_filter = ['status', 'campaign', 'sent_at']
    list_filter_submit = True
    search_fields = ['subscriber__email']
    readonly_fields = ['sent_at', 'delivered_at', 'opened_at', 'clicked_at']
    list_per_page = 25

    @display(description="Status", ordering="status", label=True)
    def status_display(self, obj):
        colors = {
            'pending': 'warning',
            'sent': 'info',
            'delivered': 'success',
            'opened': 'success',
            'clicked': 'success',
            'bounced': 'danger',
            'failed': 'danger',
        }
        return obj.status.title() if obj.status else '-', colors.get(obj.status, 'secondary')


class AutomationStepInline(TabularInline):
    model = AutomationStep
    extra = 1
    ordering = ['order']
    tab = True


@admin.register(AutomationWorkflow)
class AutomationWorkflowAdmin(ModelAdmin):
    list_display = ['name', 'trigger_type_display', 'active_status', 'total_triggered', 'total_completed']
    list_filter = ['trigger_type', 'is_active']
    list_filter_submit = True
    search_fields = ['name']
    inlines = [AutomationStepInline]
    list_per_page = 25

    @display(description="Trigger", ordering="trigger_type", label=True)
    def trigger_type_display(self, obj):
        return obj.trigger_type.replace('_', ' ').title() if obj.trigger_type else '-', "info"

    @display(description="Status", label=True)
    def active_status(self, obj):
        if obj.is_active:
            return "Active", "success"
        return "Inactive", "secondary"
