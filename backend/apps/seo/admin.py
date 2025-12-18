from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import (
    Keyword, KeywordRankingHistory, SiteAudit, SiteAuditIssue,
    Backlink, IndexNowSubmission
)


@admin.register(Keyword)
class KeywordAdmin(ModelAdmin):
    list_display = [
        'keyword', 'language_display', 'search_volume', 'difficulty_display',
        'current_position', 'position_change', 'tracking_status', 'last_checked'
    ]
    list_filter = ['language', 'difficulty', 'is_tracked', 'is_primary']
    list_filter_submit = True
    search_fields = ['keyword']
    filter_horizontal = ['posts']
    readonly_fields = ['created_at', 'updated_at', 'last_checked']
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': ('keyword', 'language', 'is_primary', 'is_tracked')
        }),
        ('Search Metrics', {
            'fields': ('search_volume', 'difficulty_score', 'difficulty', 'cpc', 'competition')
        }),
        ('Ranking', {
            'fields': ('current_position', 'previous_position', 'best_position', 'target_position', 'ranking_url')
        }),
        ('Content', {
            'fields': ('posts',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_checked'),
            'classes': ('collapse',)
        }),
    )

    @display(description="Lang", ordering="language", label=True)
    def language_display(self, obj):
        return obj.language.upper(), "secondary"

    @display(description="Difficulty", ordering="difficulty", label=True)
    def difficulty_display(self, obj):
        colors = {
            'easy': 'success',
            'medium': 'warning',
            'hard': 'danger',
        }
        return obj.difficulty.title() if obj.difficulty else '-', colors.get(obj.difficulty, 'secondary')

    @display(description="Tracking", label=True)
    def tracking_status(self, obj):
        if obj.is_tracked:
            return "Active", "success"
        return "Inactive", "secondary"


@admin.register(KeywordRankingHistory)
class KeywordRankingHistoryAdmin(ModelAdmin):
    list_display = ['keyword', 'position', 'url', 'checked_at']
    list_filter = ['checked_at']
    list_filter_submit = True
    search_fields = ['keyword__keyword']
    date_hierarchy = 'checked_at'
    list_per_page = 25


@admin.register(SiteAudit)
class SiteAuditAdmin(ModelAdmin):
    list_display = [
        'site_url', 'status_display', 'overall_score', 'seo_score',
        'errors_count', 'warnings_count', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    list_filter_submit = True
    readonly_fields = ['created_at', 'completed_at', 'audit_data']
    list_per_page = 25

    @display(description="Status", ordering="status", label=True)
    def status_display(self, obj):
        colors = {
            'pending': 'warning',
            'running': 'info',
            'completed': 'success',
            'failed': 'danger',
        }
        return obj.status, colors.get(obj.status, 'secondary')


@admin.register(SiteAuditIssue)
class SiteAuditIssueAdmin(ModelAdmin):
    list_display = ['title', 'audit', 'severity_display', 'category', 'resolution_status']
    list_filter = ['severity', 'category', 'is_resolved']
    list_filter_submit = True
    search_fields = ['title', 'description']
    list_per_page = 25

    @display(description="Severity", ordering="severity", label=True)
    def severity_display(self, obj):
        colors = {
            'critical': 'danger',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info',
        }
        return obj.severity.title() if obj.severity else '-', colors.get(obj.severity, 'secondary')

    @display(description="Status", label=True)
    def resolution_status(self, obj):
        if obj.is_resolved:
            return "Resolved", "success"
        return "Open", "warning"


@admin.register(Backlink)
class BacklinkAdmin(ModelAdmin):
    list_display = [
        'source_domain', 'target_url', 'anchor_text',
        'domain_authority', 'link_type', 'link_status', 'first_seen'
    ]
    list_filter = ['is_dofollow', 'is_active', 'first_seen']
    list_filter_submit = True
    search_fields = ['source_url', 'source_domain', 'anchor_text']
    list_per_page = 25

    @display(description="Type", label=True)
    def link_type(self, obj):
        if obj.is_dofollow:
            return "DoFollow", "success"
        return "NoFollow", "secondary"

    @display(description="Status", label=True)
    def link_status(self, obj):
        if obj.is_active:
            return "Active", "success"
        return "Lost", "danger"


@admin.register(IndexNowSubmission)
class IndexNowSubmissionAdmin(ModelAdmin):
    list_display = ['url', 'status_display', 'search_engine', 'response_code', 'submitted_at']
    list_filter = ['status', 'search_engine', 'created_at']
    list_filter_submit = True
    search_fields = ['url']
    list_per_page = 25

    @display(description="Status", ordering="status", label=True)
    def status_display(self, obj):
        colors = {
            'pending': 'warning',
            'submitted': 'info',
            'accepted': 'success',
            'failed': 'danger',
        }
        return obj.status, colors.get(obj.status, 'secondary')
