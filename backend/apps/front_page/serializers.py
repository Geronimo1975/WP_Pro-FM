"""
Serializers for Front Page management API.
"""

from rest_framework import serializers

from .models import (
    SliderRevolution,
    Slide,
    SlideLayer,
    HomepageSection,
    HomepageSectionItem,
    FrontPageSettings,
)


class SlideLayerSerializer(serializers.ModelSerializer):
    """Serializer for slide layers"""

    media_url = serializers.SerializerMethodField()

    class Meta:
        model = SlideLayer
        fields = [
            'id',
            'slide',
            'name',
            'layer_type',
            'order',
            'content',
            'media_file',
            'media_url',
            'link_url',
            'link_target',
            'position_x',
            'position_y',
            'offset_x',
            'offset_y',
            'width',
            'height',
            'animation_in',
            'animation_out',
            'start_time',
            'end_time',
            'animation_speed',
            'css_class',
            'custom_style',
            'visible_desktop',
            'visible_tablet',
            'visible_mobile',
        ]
        read_only_fields = ['id']

    def get_media_url(self, obj):
        if obj.media_file:
            return obj.media_file.file_url
        return None


class SlideSerializer(serializers.ModelSerializer):
    """Serializer for slides"""

    layers = SlideLayerSerializer(many=True, read_only=True)
    background_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Slide
        fields = [
            'id',
            'slider',
            'title',
            'subtitle',
            'order',
            'status',
            'background_image',
            'background_image_url',
            'background_color',
            'background_video_url',
            'overlay_color',
            'content_html',
            'cta_text',
            'cta_link',
            'cta_style',
            'secondary_cta_text',
            'secondary_cta_link',
            'duration',
            'transition',
            'transition_duration',
            'publish_date',
            'expire_date',
            'layers',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_background_image_url(self, obj):
        if obj.background_image:
            return obj.background_image.file_url
        return None


class SlideCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating slides"""

    class Meta:
        model = Slide
        fields = [
            'id',
            'slider',
            'title',
            'subtitle',
            'order',
            'status',
            'background_image',
            'background_color',
            'background_video_url',
            'overlay_color',
            'content_html',
            'cta_text',
            'cta_link',
            'cta_style',
            'secondary_cta_text',
            'secondary_cta_link',
            'duration',
            'transition',
            'transition_duration',
            'publish_date',
            'expire_date',
        ]
        read_only_fields = ['id']


class SliderRevolutionSerializer(serializers.ModelSerializer):
    """Serializer for Slider Revolution"""

    slides = SlideSerializer(many=True, read_only=True)
    slides_count = serializers.SerializerMethodField()
    shortcode = serializers.ReadOnlyField()

    class Meta:
        model = SliderRevolution
        fields = [
            'id',
            'wp_slider_id',
            'wp_alias',
            'name',
            'description',
            'slider_type',
            'is_active',
            'width',
            'height',
            'autoplay',
            'autoplay_delay',
            'loop',
            'pause_on_hover',
            'show_navigation',
            'show_bullets',
            'show_progress',
            'language',
            'translation_of',
            'custom_css',
            'custom_js',
            'shortcode',
            'slides',
            'slides_count',
            'created_at',
            'updated_at',
            'synced_at',
        ]
        read_only_fields = ['id', 'shortcode', 'created_at', 'updated_at', 'synced_at']

    def get_slides_count(self, obj):
        return obj.slides.filter(status='published').count()


class SliderRevolutionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for slider listings"""

    slides_count = serializers.SerializerMethodField()
    shortcode = serializers.ReadOnlyField()

    class Meta:
        model = SliderRevolution
        fields = [
            'id',
            'wp_slider_id',
            'wp_alias',
            'name',
            'slider_type',
            'is_active',
            'language',
            'shortcode',
            'slides_count',
            'updated_at',
        ]

    def get_slides_count(self, obj):
        return obj.slides.filter(status='published').count()


class HomepageSectionItemSerializer(serializers.ModelSerializer):
    """Serializer for homepage section items"""

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = HomepageSectionItem
        fields = [
            'id',
            'section',
            'title',
            'subtitle',
            'description',
            'order',
            'is_active',
            'image',
            'image_url',
            'icon_class',
            'link_url',
            'link_text',
            'author_name',
            'author_title',
            'rating',
            'stat_value',
            'stat_suffix',
            'custom_data',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.file_url
        return None


class HomepageSectionSerializer(serializers.ModelSerializer):
    """Serializer for homepage sections"""

    items = HomepageSectionItemSerializer(many=True, read_only=True)
    slider_data = SliderRevolutionListSerializer(source='slider', read_only=True)
    background_image_url = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = HomepageSection
        fields = [
            'id',
            'name',
            'section_type',
            'order',
            'is_active',
            'title',
            'subtitle',
            'description',
            'content_html',
            'slider',
            'slider_data',
            'background_image',
            'background_image_url',
            'background_color',
            'background_style',
            'css_class',
            'css_id',
            'padding_top',
            'padding_bottom',
            'text_color',
            'cta_text',
            'cta_link',
            'language',
            'translation_of',
            'settings',
            'items',
            'items_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_background_image_url(self, obj):
        if obj.background_image:
            return obj.background_image.file_url
        return None

    def get_items_count(self, obj):
        return obj.items.filter(is_active=True).count()


class HomepageSectionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for section listings"""

    items_count = serializers.SerializerMethodField()

    class Meta:
        model = HomepageSection
        fields = [
            'id',
            'name',
            'section_type',
            'order',
            'is_active',
            'title',
            'language',
            'items_count',
            'updated_at',
        ]

    def get_items_count(self, obj):
        return obj.items.filter(is_active=True).count()


class FrontPageSettingsSerializer(serializers.ModelSerializer):
    """Serializer for front page settings"""

    main_slider_data = SliderRevolutionListSerializer(source='main_slider', read_only=True)
    og_image_url = serializers.SerializerMethodField()
    header_logo_light_url = serializers.SerializerMethodField()
    header_logo_dark_url = serializers.SerializerMethodField()

    class Meta:
        model = FrontPageSettings
        fields = [
            'id',
            'language',
            'wp_page_id',
            'main_slider',
            'main_slider_data',
            'meta_title',
            'meta_description',
            'og_image',
            'og_image_url',
            'header_style',
            'header_logo_light',
            'header_logo_light_url',
            'header_logo_dark',
            'header_logo_dark_url',
            'custom_css',
            'custom_js_header',
            'custom_js_footer',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_og_image_url(self, obj):
        if obj.og_image:
            return obj.og_image.file_url
        return None

    def get_header_logo_light_url(self, obj):
        if obj.header_logo_light:
            return obj.header_logo_light.file_url
        return None

    def get_header_logo_dark_url(self, obj):
        if obj.header_logo_dark:
            return obj.header_logo_dark.file_url
        return None


class FrontPageFullSerializer(serializers.Serializer):
    """Serializer for the complete front page data"""

    settings = FrontPageSettingsSerializer()
    main_slider = SliderRevolutionSerializer()
    sections = HomepageSectionSerializer(many=True)

    class Meta:
        fields = ['settings', 'main_slider', 'sections']
