"""
Admin interface for Glossary management.
"""
from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.conf import settings
from django.db.models import Count
from unfold.admin import ModelAdmin
from unfold.decorators import display, action
from .models import GlossaryTerm, GlossaryCategory, GlossarySyncLog


@admin.register(GlossaryCategory)
class GlossaryCategoryAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'term_count', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 25

    def term_count(self, obj):
        return obj.terms.count()
    term_count.short_description = 'Terms'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _term_count=Count('terms')
        )


@admin.register(GlossaryTerm)
class GlossaryTermAdmin(ModelAdmin):
    list_display = ['term', 'letter', 'category_display', 'definition_short', 'priority_display', 'sync_status', 'action_buttons']
    list_filter = ['letter', 'category', 'is_published', 'is_active', 'priority']
    list_filter_submit = True
    search_fields = ['term', 'definition', 'synonyms']
    readonly_fields = ['letter', 'wp_post_id', 'published_at', 'created_at', 'updated_at', 'action_buttons_detail']
    ordering = ['letter', 'term']
    list_per_page = 50

    fieldsets = (
        (None, {
            'fields': ('action_buttons_detail',)
        }),
        ('Term Information', {
            'fields': ('term', 'slug', 'letter', 'category')
        }),
        ('Content', {
            'fields': ('definition', 'examples', 'synonyms', 'related_terms')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'search_volume', 'priority')
        }),
        ('WordPress Sync', {
            'fields': ('wp_post_id', 'is_published', 'published_at'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @display(description="Category", label=True)
    def category_display(self, obj):
        if obj.category:
            return obj.category.name, "info"
        return "Uncategorized", "secondary"

    @display(description="Priority", label=True)
    def priority_display(self, obj):
        colors = {1: 'danger', 2: 'warning', 3: 'info', 4: 'secondary', 5: 'secondary'}
        labels = {1: 'Highest', 2: 'High', 3: 'Normal', 4: 'Low', 5: 'Lowest'}
        return labels.get(obj.priority, 'Normal'), colors.get(obj.priority, 'info')

    @display(description="Published", label=True)
    def sync_status(self, obj):
        if obj.is_published:
            return "Published", "success"
        return "Draft", "warning"

    def definition_short(self, obj):
        if obj.definition:
            return obj.definition[:100] + '...' if len(obj.definition) > 100 else obj.definition
        return '-'
    definition_short.short_description = 'Definition'

    def action_buttons(self, obj):
        """Action buttons for list view"""
        buttons = []

        # View on WordPress if published
        if obj.is_published and obj.wp_post_id:
            wp_url = f"{settings.WP_SITE_URL}/{obj.slug}/"
            buttons.append(format_html(
                '<a href="{}" target="_blank" class="button" style="padding: 4px 8px; font-size: 11px; margin-right: 4px;" title="View on WordPress">'
                '<span class="material-symbols-outlined" style="font-size: 14px; vertical-align: middle;">open_in_new</span>'
                '</a>',
                wp_url
            ))

        return format_html(''.join([str(b) for b in buttons])) if buttons else '-'
    action_buttons.short_description = 'Actions'

    def action_buttons_detail(self, obj):
        """Action buttons for detail view"""
        buttons = []

        if obj.is_published and obj.wp_post_id:
            wp_url = f"{settings.WP_SITE_URL}/{obj.slug}/"
            buttons.append(format_html(
                '<a href="{}" target="_blank" class="button" style="margin-right: 8px; padding: 8px 16px;">'
                '<span class="material-symbols-outlined" style="vertical-align: middle; margin-right: 4px;">open_in_new</span>'
                'View on WordPress'
                '</a>',
                wp_url
            ))

        if not buttons:
            return format_html('<p style="color: #666;">Term not yet published to WordPress</p>')

        return format_html(
            '<div style="margin: 16px 0; padding: 16px; background: #f8f9fa; border-radius: 8px;">{}</div>',
            format_html(''.join([str(b) for b in buttons]))
        )
    action_buttons_detail.short_description = 'Quick Actions'

    # Bulk actions
    @action(description="Mark as Published")
    def mark_published(self, request, queryset):
        updated = queryset.update(is_published=True)
        messages.success(request, f'{updated} terms marked as published')

    @action(description="Mark as Draft")
    def mark_draft(self, request, queryset):
        updated = queryset.update(is_published=False)
        messages.success(request, f'{updated} terms marked as draft')

    @action(description="Activate Selected")
    def activate_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        messages.success(request, f'{updated} terms activated')

    @action(description="Deactivate Selected")
    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        messages.success(request, f'{updated} terms deactivated')

    actions = ['mark_published', 'mark_draft', 'activate_selected', 'deactivate_selected']


@admin.register(GlossarySyncLog)
class GlossarySyncLogAdmin(ModelAdmin):
    list_display = ['started_at', 'sync_type', 'status_display', 'total_items', 'synced_items', 'failed_items']
    list_filter = ['status', 'sync_type', 'started_at']
    list_filter_submit = True
    readonly_fields = ['started_at', 'completed_at', 'total_items', 'synced_items', 'failed_items', 'error_message']
    list_per_page = 25

    @display(description="Status", ordering="status", label=True)
    def status_display(self, obj):
        colors = {
            'started': 'info',
            'success': 'success',
            'failed': 'danger',
            'partial': 'warning',
        }
        return obj.status, colors.get(obj.status, 'secondary')
