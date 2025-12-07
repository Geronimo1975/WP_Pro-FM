from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import MediaFile, MediaCollection, MediaSyncLog
from .serializers import MediaFileSerializer, MediaCollectionSerializer, MediaSyncLogSerializer
from .tasks import sync_wordpress_media


class MediaFileViewSet(viewsets.ModelViewSet):
    """ViewSet for managing media files"""
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['media_type', 'is_synced', 'is_local']
    search_fields = ['title', 'filename', 'alt_text']
    ordering_fields = ['created_at', 'title', 'file_size']

    @action(detail=False, methods=['post'])
    def sync_from_wordpress(self, request):
        """Trigger WordPress media sync"""
        task = sync_wordpress_media.delay()
        return Response({
            'message': 'Media sync started',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get media statistics"""
        total = MediaFile.objects.count()
        by_type = {}
        for media_type in MediaFile.MediaType.choices:
            by_type[media_type[0]] = MediaFile.objects.filter(media_type=media_type[0]).count()

        total_size = sum(m.file_size or 0 for m in MediaFile.objects.all())

        return Response({
            'total_files': total,
            'by_type': by_type,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'synced': MediaFile.objects.filter(is_synced=True).count(),
            'local': MediaFile.objects.filter(is_local=True).count(),
        })


class MediaCollectionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing media collections"""
    queryset = MediaCollection.objects.all()
    serializer_class = MediaCollectionSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def add_files(self, request, pk=None):
        """Add media files to collection"""
        collection = self.get_object()
        file_ids = request.data.get('file_ids', [])
        files = MediaFile.objects.filter(id__in=file_ids)
        collection.media_files.add(*files)
        return Response({'message': f'Added {files.count()} files to collection'})

    @action(detail=True, methods=['post'])
    def remove_files(self, request, pk=None):
        """Remove media files from collection"""
        collection = self.get_object()
        file_ids = request.data.get('file_ids', [])
        files = MediaFile.objects.filter(id__in=file_ids)
        collection.media_files.remove(*files)
        return Response({'message': f'Removed {files.count()} files from collection'})


class MediaSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing sync logs"""
    queryset = MediaSyncLog.objects.all()
    serializer_class = MediaSyncLogSerializer
    permission_classes = [IsAuthenticated]
