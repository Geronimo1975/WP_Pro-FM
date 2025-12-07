from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    Keyword, KeywordRankingHistory, SiteAudit, SiteAuditIssue,
    Backlink, IndexNowSubmission
)
from .serializers import (
    KeywordSerializer, KeywordRankingHistorySerializer,
    SiteAuditSerializer, SiteAuditIssueSerializer,
    BacklinkSerializer, IndexNowSubmissionSerializer, IndexNowBulkSerializer
)
from .tasks import check_keyword_rankings, run_site_audit, submit_to_indexnow


class KeywordViewSet(viewsets.ModelViewSet):
    """ViewSet for managing keywords"""
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['language', 'difficulty', 'is_tracked', 'is_primary']
    search_fields = ['keyword']
    ordering_fields = ['search_volume', 'current_position', 'keyword']

    @action(detail=False, methods=['post'])
    def check_rankings(self, request):
        """Check rankings for all tracked keywords"""
        task = check_keyword_rankings.delay()
        return Response({
            'message': 'Ranking check started',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get ranking history for a keyword"""
        keyword = self.get_object()
        history = keyword.ranking_history.all()[:30]
        serializer = KeywordRankingHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get keyword statistics"""
        total = Keyword.objects.count()
        tracked = Keyword.objects.filter(is_tracked=True).count()
        top_10 = Keyword.objects.filter(current_position__lte=10).count()
        improved = Keyword.objects.filter(
            current_position__lt=models.F('previous_position')
        ).count()

        return Response({
            'total': total,
            'tracked': tracked,
            'top_10': top_10,
            'improved': improved,
        })


class SiteAuditViewSet(viewsets.ModelViewSet):
    """ViewSet for site audits"""
    queryset = SiteAudit.objects.all()
    serializer_class = SiteAuditSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status']

    @action(detail=False, methods=['post'])
    def run_audit(self, request):
        """Run a new site audit"""
        site_url = request.data.get('site_url')
        if not site_url:
            return Response(
                {'error': 'site_url is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        audit = SiteAudit.objects.create(site_url=site_url)
        task = run_site_audit.delay(audit.id)

        return Response({
            'message': 'Audit started',
            'audit_id': audit.id,
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)


class BacklinkViewSet(viewsets.ModelViewSet):
    """ViewSet for managing backlinks"""
    queryset = Backlink.objects.all()
    serializer_class = BacklinkSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_dofollow', 'is_active', 'source_domain']
    search_fields = ['source_url', 'source_domain', 'anchor_text']
    ordering_fields = ['domain_authority', 'first_seen']

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get backlink statistics"""
        total = Backlink.objects.count()
        active = Backlink.objects.filter(is_active=True).count()
        dofollow = Backlink.objects.filter(is_dofollow=True).count()
        unique_domains = Backlink.objects.values('source_domain').distinct().count()

        return Response({
            'total': total,
            'active': active,
            'dofollow': dofollow,
            'unique_domains': unique_domains,
        })


class IndexNowViewSet(viewsets.ModelViewSet):
    """ViewSet for IndexNow submissions"""
    queryset = IndexNowSubmission.objects.all()
    serializer_class = IndexNowSubmissionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'search_engine']

    @action(detail=False, methods=['post'])
    def submit_urls(self, request):
        """Submit URLs to IndexNow"""
        serializer = IndexNowBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        urls = serializer.validated_data['urls']
        task = submit_to_indexnow.delay(urls)

        return Response({
            'message': f'Submitting {len(urls)} URLs to IndexNow',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
