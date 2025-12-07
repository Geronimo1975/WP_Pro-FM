from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Post, Category, Tag, ContentTemplate, ContentGenerationJob
from .serializers import (
    PostSerializer, PostListSerializer, CategorySerializer, TagSerializer,
    ContentTemplateSerializer, ContentGenerationJobSerializer, GenerateContentSerializer,
    TranslationSerializer, CreateTranslationSerializer, WPMLLanguageSerializer
)
from .tasks import (
    generate_content, publish_to_wordpress, sync_wordpress_posts,
    sync_wpml_translations, create_translation_task
)
from .wpml import WPMLService, WPMLLanguage


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for managing posts with WPML translation support"""
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_fields = ['post_type', 'status', 'language', 'is_ai_generated', 'wpml_trid']
    search_fields = ['title', 'content', 'focus_keyword']
    ordering_fields = ['created_at', 'title', 'seo_score']

    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        return PostSerializer

    def get_queryset(self):
        """Filter by language if specified"""
        queryset = super().get_queryset()
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language=language)
        return queryset

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
        """Sync posts from WordPress for all WPML languages"""
        language = request.data.get('language')  # Optional: sync specific language
        task = sync_wordpress_posts.delay(language=language)
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

    # ==================== WPML Translation Endpoints ====================

    @action(detail=True, methods=['get'])
    def translations(self, request, pk=None):
        """
        Get all translations of a post.

        Returns available translations with their language codes and IDs.
        """
        post = self.get_object()
        translations = post.get_available_translations()

        result = {
            'original': post.id if post.is_original else post.translation_of_id,
            'current_language': post.language,
            'wpml_trid': post.wpml_trid,
            'translations': {
                lang: {
                    'id': p.id,
                    'wp_id': p.wp_id,
                    'title': p.title,
                    'status': p.status,
                    'link': p.wp_link
                }
                for lang, p in translations.items()
            },
            'missing_languages': post.get_missing_languages()
        }

        return Response(result)

    @action(detail=True, methods=['post'])
    def create_translation(self, request, pk=None):
        """
        Create a translation of this post in a new language.

        Required fields:
        - target_language: Language code (e.g., 'en', 'de')

        Optional fields:
        - title: Translated title (defaults to original with language prefix)
        - content: Translated content (defaults to original content)
        - auto_translate: Use AI to translate content (default: False)
        """
        post = self.get_object()
        serializer = CreateTranslationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_language = serializer.validated_data['target_language']

        # Check if translation already exists
        existing = post.get_translation(target_language)
        if existing and existing.id != post.id:
            return Response({
                'error': f'Translation already exists for language {target_language}',
                'existing_id': existing.id
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create translation async if auto_translate is requested
        if serializer.validated_data.get('auto_translate'):
            task = create_translation_task.delay(
                post_id=post.id,
                target_language=target_language
            )
            return Response({
                'message': f'Translation to {target_language} started',
                'task_id': task.id
            }, status=status.HTTP_202_ACCEPTED)

        # Create translation immediately
        title = serializer.validated_data.get('title') or f"[{target_language.upper()}] {post.title}"
        content = serializer.validated_data.get('content') or post.content

        translation = Post.objects.create(
            title=title,
            content=content,
            excerpt=post.excerpt,
            slug=f"{post.slug}-{target_language}" if post.slug else '',
            post_type=post.post_type,
            status=Post.PostStatus.DRAFT,
            language=target_language,
            translation_of=post if post.is_original else post.translation_of,
            source_language=post.language,
            wpml_trid=post.wpml_trid,
            focus_keyword=post.focus_keyword,
            meta_title=serializer.validated_data.get('meta_title', ''),
            meta_description=serializer.validated_data.get('meta_description', ''),
            is_ai_generated=False
        )

        # Copy categories and tags (need to find translated versions)
        for category in post.categories.all():
            translated_cat = category.get_translation(target_language)
            if translated_cat:
                translation.categories.add(translated_cat)
            else:
                translation.categories.add(category)

        for tag in post.tags.all():
            translated_tag = tag.get_translation(target_language)
            if translated_tag:
                translation.tags.add(translated_tag)
            else:
                translation.tags.add(tag)

        return Response(
            PostSerializer(translation).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def sync_translations(self, request, pk=None):
        """Sync translations from WordPress for this post"""
        post = self.get_object()

        if not post.wp_id:
            return Response({
                'error': 'Post is not synced with WordPress yet'
            }, status=status.HTTP_400_BAD_REQUEST)

        task = sync_wpml_translations.delay(post_id=post.id)
        return Response({
            'message': 'Translation sync started',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'])
    def link_translation(self, request, pk=None):
        """
        Link this post as a translation of another post.

        Required fields:
        - original_post_id: ID of the original post
        """
        post = self.get_object()
        original_id = request.data.get('original_post_id')

        if not original_id:
            return Response({
                'error': 'original_post_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            original = Post.objects.get(id=original_id)
        except Post.DoesNotExist:
            return Response({
                'error': f'Post {original_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        if original.language == post.language:
            return Response({
                'error': 'Cannot link posts with the same language'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Link as translation
        post.translation_of = original if original.is_original else original.translation_of
        post.source_language = original.language
        post.wpml_trid = original.wpml_trid
        post.save()

        return Response({
            'message': f'Post linked as {post.language} translation of post {original.id}',
            'wpml_trid': post.wpml_trid
        })


class WPMLViewSet(viewsets.ViewSet):
    """ViewSet for WPML-specific operations"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def languages(self, request):
        """Get available WPML languages"""
        try:
            service = WPMLService()
            languages = service.get_languages()
        except Exception:
            # Fallback to configured languages
            languages = [
                {'code': code, 'name': name, 'active': True}
                for code, name in WPMLLanguage.get_choices()
            ]

        return Response({
            'default_language': WPMLLanguage.DEFAULT,
            'available_languages': WPMLLanguage.AVAILABLE,
            'languages': languages
        })

    @action(detail=False, methods=['post'])
    def sync_all(self, request):
        """Sync all content from all WPML languages"""
        task = sync_wordpress_posts.delay(sync_all_languages=True)
        return Response({
            'message': 'Full WPML sync started for all languages',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['get'])
    def translation_stats(self, request):
        """Get translation statistics"""
        from django.db.models import Count

        stats = {
            'posts': {},
            'categories': {},
            'tags': {}
        }

        # Post stats by language
        post_stats = Post.objects.values('language').annotate(count=Count('id'))
        for stat in post_stats:
            stats['posts'][stat['language']] = stat['count']

        # Category stats by language
        cat_stats = Category.objects.values('language').annotate(count=Count('id'))
        for stat in cat_stats:
            stats['categories'][stat['language']] = stat['count']

        # Tag stats by language
        tag_stats = Tag.objects.values('language').annotate(count=Count('id'))
        for stat in tag_stats:
            stats['tags'][stat['language']] = stat['count']

        # Count posts missing translations
        original_posts = Post.objects.filter(translation_of__isnull=True, source_language='')
        missing_translations = 0
        for post in original_posts:
            missing_translations += len(post.get_missing_languages())

        stats['missing_translations'] = missing_translations
        stats['total_posts'] = Post.objects.count()
        stats['original_posts'] = original_posts.count()

        return Response(stats)


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
