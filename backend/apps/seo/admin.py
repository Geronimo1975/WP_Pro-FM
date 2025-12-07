from django.contrib import admin
from .models import (
    Keyword, KeywordRankingHistory, SiteAudit, SiteAuditIssue,
    Backlink, IndexNowSubmission
)


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = [
        'keyword', 'language', 'search_volume', 'difficulty',
        'current_position', 'position_change', 'is_tracked', 'last_checked'
    ]
    list_filter = ['language', 'difficulty', 'is_tracked', 'is_primary']
    search_fields = ['keyword']
    filter_horizontal = ['posts']
    readonly_fields = ['created_at', 'updated_at', 'last_checked']

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


@admin.register(KeywordRankingHistory)
class KeywordRankingHistoryAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'position', 'url', 'checked_at']
    list_filter = ['checked_at']
    search_fields = ['keyword__keyword']
    date_hierarchy = 'checked_at'


@admin.register(SiteAudit)
class SiteAuditAdmin(admin.ModelAdmin):
    list_display = [
        'site_url', 'status', 'overall_score', 'seo_score',
        'errors_count', 'warnings_count', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    readonly_fields = ['created_at', 'completed_at', 'audit_data']


@admin.register(SiteAuditIssue)
class SiteAuditIssueAdmin(admin.ModelAdmin):
    list_display = ['title', 'audit', 'severity', 'category', 'is_resolved']
    list_filter = ['severity', 'category', 'is_resolved']
    search_fields = ['title', 'description']


@admin.register(Backlink)
class BacklinkAdmin(admin.ModelAdmin):
    list_display = [
        'source_domain', 'target_url', 'anchor_text',
        'domain_authority', 'is_dofollow', 'is_active', 'first_seen'
    ]
    list_filter = ['is_dofollow', 'is_active', 'first_seen']
    search_fields = ['source_url', 'source_domain', 'anchor_text']


@admin.register(IndexNowSubmission)
class IndexNowSubmissionAdmin(admin.ModelAdmin):
    list_display = ['url', 'status', 'search_engine', 'response_code', 'submitted_at']
    list_filter = ['status', 'search_engine', 'created_at']
    search_fields = ['url']
