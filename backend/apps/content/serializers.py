from rest_framework import serializers
from .models import Post, Category, Tag, ContentTemplate, ContentGenerationJob


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'wp_id', 'name', 'slug', 'description', 'parent', 'language']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'wp_id', 'name', 'slug', 'language']


class PostSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True,
        write_only=True,
        source='categories',
        required=False
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        source='tags',
        required=False
    )

    class Meta:
        model = Post
        fields = [
            'id', 'wp_id', 'wp_link', 'title', 'slug', 'content', 'excerpt',
            'post_type', 'status', 'categories', 'tags', 'category_ids', 'tag_ids',
            'featured_image', 'focus_keyword', 'meta_title', 'meta_description',
            'seo_score', 'language', 'translation_of', 'is_ai_generated',
            'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = ['wp_id', 'wp_link', 'synced_at', 'seo_score']


class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    class Meta:
        model = Post
        fields = [
            'id', 'wp_id', 'title', 'slug', 'post_type', 'status',
            'language', 'is_ai_generated', 'seo_score', 'created_at'
        ]


class ContentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentTemplate
        fields = [
            'id', 'name', 'template_type', 'system_prompt', 'user_prompt_template',
            'variables', 'default_word_count', 'is_active', 'created_at'
        ]


class ContentGenerationJobSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)

    class Meta:
        model = ContentGenerationJob
        fields = [
            'id', 'template', 'template_name', 'variables', 'status',
            'result_post', 'error_message', 'tokens_used', 'cost_usd',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['status', 'result_post', 'error_message', 'tokens_used', 'cost_usd', 'completed_at']


class GenerateContentSerializer(serializers.Serializer):
    """Serializer for content generation request"""
    template_id = serializers.IntegerField()
    variables = serializers.DictField(required=False, default=dict)
    auto_publish = serializers.BooleanField(default=False)
    language = serializers.CharField(default='de', max_length=10)
