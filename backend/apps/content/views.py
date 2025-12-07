from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Post, Category, Tag, ContentTemplate, ContentGenerationJob
from .serializers import (
    PostSerializer, PostListSerializer, CategorySerializer, TagSerializer,
    ContentTemplateSerializer, ContentGenerationJobSerializer, GenerateContentSerializer
)
from .tasks import generate_content, publish_to_wordpress, sync_wordpress_posts


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for managing posts"""
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_fields = ['post_type', 'status', 'language', 'is_ai_generated']
    search_fields = ['title', 'content', 'focus_keyword']
    ordering_fields = ['created_at', 'title', 'seo_score']

    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        return PostSerializer

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish post to WordPress"""
        post = self.get_object()
        task = publish_to_wordpress.delay(post.id)
        return Response({
            'message': 'Publishing to WordPress',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'])
    def sync_from_wordpress(self, request):
        """Sync posts from WordPress"""
        task = sync_wordpress_posts.delay()
        return Response({
            'message': 'WordPress sync started',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate new content using AI"""
        serializer = GenerateContentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = generate_content.delay(
            template_id=serializer.validated_data['template_id'],
            variables=serializer.validated_data['variables'],
            auto_publish=serializer.validated_data['auto_publish'],
            language=serializer.validated_data['language']
        )

        return Response({
            'message': 'Content generation started',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing categories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['language', 'parent']
    search_fields = ['name']


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tags"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['language']
    search_fields = ['name']


class ContentTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing content templates"""
    queryset = ContentTemplate.objects.all()
    serializer_class = ContentTemplateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['template_type', 'is_active']


class ContentGenerationJobViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing generation jobs"""
    queryset = ContentGenerationJob.objects.all()
    serializer_class = ContentGenerationJobSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'template']
