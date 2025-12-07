from django.contrib import admin
from .models import (
    Subscriber, SubscriberTag, MailingList, EmailTemplate,
    Campaign, CampaignEmail, AutomationWorkflow, AutomationStep
)


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = [
        'email', 'full_name', 'status', 'language',
        'emails_sent', 'open_rate', 'subscribed_at'
    ]
    list_filter = ['status', 'language', 'lists', 'tags', 'subscribed_at']
    search_fields = ['email', 'first_name', 'last_name', 'company']
    filter_horizontal = ['lists', 'tags']
    readonly_fields = [
        'emails_sent', 'emails_opened', 'emails_clicked',
        'last_opened', 'last_clicked', 'subscribed_at', 'confirmed_at'
    ]

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


@admin.register(SubscriberTag)
class SubscriberTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'created_at']
    search_fields = ['name']


@admin.register(MailingList)
class MailingListAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'subscriber_count', 'is_public', 'is_active']
    list_filter = ['is_public', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'subject', 'is_active', 'updated_at']
    list_filter = ['template_type', 'is_active', 'is_ai_generated']
    search_fields = ['name', 'subject']


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'status', 'total_recipients', 'emails_sent',
        'open_rate', 'click_rate', 'scheduled_at'
    ]
    list_filter = ['status', 'mailing_lists', 'created_at']
    search_fields = ['name', 'subject']
    filter_horizontal = ['mailing_lists', 'tags', 'exclude_tags']
    readonly_fields = [
        'total_recipients', 'emails_sent', 'emails_delivered',
        'emails_opened', 'unique_opens', 'emails_clicked', 'unique_clicks',
        'bounces', 'unsubscribes', 'complaints', 'started_at', 'completed_at'
    ]

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


@admin.register(CampaignEmail)
class CampaignEmailAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'subscriber', 'status', 'sent_at', 'opened_at']
    list_filter = ['status', 'campaign', 'sent_at']
    search_fields = ['subscriber__email']
    readonly_fields = ['sent_at', 'delivered_at', 'opened_at', 'clicked_at']


class AutomationStepInline(admin.TabularInline):
    model = AutomationStep
    extra = 1
    ordering = ['order']


@admin.register(AutomationWorkflow)
class AutomationWorkflowAdmin(admin.ModelAdmin):
    list_display = ['name', 'trigger_type', 'is_active', 'total_triggered', 'total_completed']
    list_filter = ['trigger_type', 'is_active']
    search_fields = ['name']
    inlines = [AutomationStepInline]
