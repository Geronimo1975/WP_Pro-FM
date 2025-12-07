from rest_framework import serializers
from .models import (
    Keyword, KeywordRankingHistory, SiteAudit, SiteAuditIssue,
    Backlink, IndexNowSubmission
)


class KeywordSerializer(serializers.ModelSerializer):
    position_change = serializers.ReadOnlyField()

    class Meta:
        model = Keyword
        fields = [
            'id', 'keyword', 'language', 'search_volume', 'difficulty_score',
            'difficulty', 'cpc', 'competition', 'current_position', 'previous_position',
            'best_position', 'ranking_url', 'position_change', 'is_primary',
            'is_tracked', 'target_position', 'created_at', 'last_checked'
        ]
        read_only_fields = ['created_at', 'last_checked']


class KeywordRankingHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = KeywordRankingHistory
        fields = ['id', 'keyword', 'position', 'url', 'checked_at']


class SiteAuditIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteAuditIssue
        fields = [
            'id', 'severity', 'category', 'title', 'description',
            'url', 'recommendation', 'is_resolved'
        ]


class SiteAuditSerializer(serializers.ModelSerializer):
    issues = SiteAuditIssueSerializer(many=True, read_only=True)

    class Meta:
        model = SiteAudit
        fields = [
            'id', 'site_url', 'status', 'overall_score', 'performance_score',
            'seo_score', 'accessibility_score', 'errors_count', 'warnings_count',
            'notices_count', 'issues', 'created_at', 'completed_at'
        ]
        read_only_fields = ['status', 'created_at', 'completed_at']


class BacklinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Backlink
        fields = [
            'id', 'source_url', 'source_domain', 'target_url', 'anchor_text',
            'domain_authority', 'is_dofollow', 'is_active', 'first_seen', 'last_checked'
        ]


class IndexNowSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndexNowSubmission
        fields = [
            'id', 'url', 'status', 'search_engine', 'response_code',
            'submitted_at', 'created_at'
        ]
        read_only_fields = ['status', 'response_code', 'submitted_at']


class IndexNowBulkSerializer(serializers.Serializer):
    """Serializer for bulk IndexNow submissions"""
    urls = serializers.ListField(
        child=serializers.URLField(),
        min_length=1,
        max_length=10000
    )
