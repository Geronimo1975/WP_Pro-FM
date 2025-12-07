from rest_framework import serializers
from .models import Post, Category, Tag, ContentTemplate, ContentGenerationJob
from .wpml import WPMLLanguage


class CategorySerializer(serializers.ModelSerializer):
    translation_of_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='translation_of',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Category
        fields = [
            'id', 'wp_id', 'name', 'slug', 'description', 'parent',
            'language', 'wpml_trid', 'translation_of', 'translation_of_id'
        ]
        read_only_fields = ['translation_of']


class TagSerializer(serializers.ModelSerializer):
    translation_of_id = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source='translation_of',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Tag
        fields = [
            'id', 'wp_id', 'name', 'slug',
            'language', 'wpml_trid', 'translation_of', 'translation_of_id'
        ]
        read_only_fields = ['translation_of']


class TranslationInfoSerializer(serializers.Serializer):
    """Serializer for translation information in post responses"""
    id = serializers.IntegerField()
    wp_id = serializers.IntegerField(allow_null=True)
    title = serializers.CharField()
    language = serializers.CharField()
    status = serializers.CharField()


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

    # WPML translation fields
    is_original = serializers.BooleanField(read_only=True)
    translations = serializers.SerializerMethodField()
    missing_languages = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'wp_id', 'wp_link', 'title', 'slug', 'content', 'excerpt',
            'post_type', 'status', 'categories', 'tags', 'category_ids', 'tag_ids',
            'featured_image', 'focus_keyword', 'meta_title', 'meta_description',
            'seo_score', 'language', 'wpml_trid', 'translation_of', 'source_language',
            'is_original', 'translations', 'missing_languages',
            'is_ai_generated', 'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = [
            'wp_id', 'wp_link', 'synced_at', 'seo_score',
            'is_original', 'translations', 'missing_languages'
        ]

    def get_translations(self, obj):
        """Get all translations of this post"""
        translations = obj.get_available_translations()
        return {
            lang: {
                'id': post.id,
                'wp_id': post.wp_id,
                'title': post.title,
                'status': post.status
            }
            for lang, post in translations.items()
            if post.id != obj.id
        }

    def get_missing_languages(self, obj):
        """Get languages without translations"""
        return obj.get_missing_languages()


class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views with translation indicators"""
    is_original = serializers.BooleanField(read_only=True)
    has_translations = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'wp_id', 'title', 'slug', 'post_type', 'status',
            'language', 'wpml_trid', 'is_original', 'has_translations',
            'is_ai_generated', 'seo_score', 'created_at'
        ]

    def get_has_translations(self, obj):
        """Check if post has any translations"""
        return obj.translation_group.count() > 1


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
    language = serializers.ChoiceField(
        choices=WPMLLanguage.get_choices(),
        default=WPMLLanguage.DEFAULT
    )


class TranslationSerializer(serializers.Serializer):
    """Serializer for translation details"""
    language = serializers.CharField()
    id = serializers.IntegerField()
    wp_id = serializers.IntegerField(allow_null=True)
    title = serializers.CharField()
    status = serializers.CharField()
    link = serializers.URLField(allow_blank=True)


class CreateTranslationSerializer(serializers.Serializer):
    """Serializer for creating a new translation"""
    target_language = serializers.ChoiceField(choices=WPMLLanguage.get_choices())
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    content = serializers.CharField(required=False, allow_blank=True)
    excerpt = serializers.CharField(required=False, allow_blank=True)
    meta_title = serializers.CharField(max_length=100, required=False, allow_blank=True)
    meta_description = serializers.CharField(max_length=200, required=False, allow_blank=True)
    auto_translate = serializers.BooleanField(default=False)

    def validate_target_language(self, value):
        """Ensure target language is available"""
        if value not in WPMLLanguage.AVAILABLE:
            raise serializers.ValidationError(
                f"Language '{value}' is not available. Choose from: {WPMLLanguage.AVAILABLE}"
            )
        return value


class WPMLLanguageSerializer(serializers.Serializer):
    """Serializer for WPML language information"""
    code = serializers.CharField()
    name = serializers.CharField()
    native_name = serializers.CharField(required=False)
    active = serializers.BooleanField(default=True)
    default = serializers.BooleanField(default=False)
