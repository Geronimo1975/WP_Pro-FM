"""
Admin configuration for Front Page management.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    SliderRevolution,
    Slide,
    SlideLayer,
    HomepageSection,
    HomepageSectionItem,
    FrontPageSettings,
)


class SlideLayerInline(admin.TabularInline):
    """Inline admin for slide layers"""
    model = SlideLayer
    extra = 0
    fields = [
        'name', 'layer_type', 'order', 'content', 'position_x', 'position_y',
        'animation_in', 'start_time', 'visible_desktop', 'visible_tablet', 'visible_mobile'
    ]
    ordering = ['order']


class SlideInline(admin.TabularInline):
    """Inline admin for slides"""
    model = Slide
    extra = 0
    fields = ['title', 'order', 'status', 'duration', 'transition']
    ordering = ['order']
    show_change_link = True


@admin.register(SliderRevolution)
class SliderRevolutionAdmin(admin.ModelAdmin):
    """Admin for Slider Revolution"""

    list_display = [
        'name', 'slider_type', 'language', 'is_active',
        'slides_count', 'shortcode_display', 'updated_at'
    ]
    list_filter = ['is_active', 'slider_type', 'language']
    search_fields = ['name', 'wp_alias', 'description']
    readonly_fields = ['shortcode', 'created_at', 'updated_at', 'synced_at']
    inlines = [SlideInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'slider_type', 'is_active')
        }),
        (_('WordPress Sync'), {
            'fields': ('wp_slider_id', 'wp_alias', 'shortcode', 'synced_at'),
            'classes': ('collapse',)
        }),
        (_('Display Settings'), {
            'fields': (
                ('width', 'height'),
                ('autoplay', 'autoplay_delay'),
                ('loop', 'pause_on_hover'),
            )
        }),
        (_('Navigation'), {
            'fields': ('show_navigation', 'show_bullets', 'show_progress')
        }),
        (_('Language'), {
            'fields': ('language', 'translation_of')
        }),
        (_('Custom Code'), {
            'fields': ('custom_css', 'custom_js'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def slides_count(self, obj):
        return obj.slides.count()
    slides_count.short_description = _('Slides')

    def shortcode_display(self, obj):
        if obj.shortcode:
            return format_html(
                '<code style="background:#f4f4f4;padding:2px 6px;">{}</code>',
                obj.shortcode
            )
        return '-'
    shortcode_display.short_description = _('Shortcode')


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    """Admin for Slides"""

    list_display = [
        'title', 'slider', 'order', 'status', 'duration',
        'transition', 'has_cta', 'layers_count', 'updated_at'
    ]
    list_filter = ['status', 'slider', 'transition']
    search_fields = ['title', 'subtitle', 'content_html']
    list_editable = ['order', 'status']
    raw_id_fields = ['slider', 'background_image']
    inlines = [SlideLayerInline]

    fieldsets = (
        (None, {
            'fields': ('slider', 'title', 'subtitle', 'order', 'status')
        }),
        (_('Background'), {
            'fields': (
                'background_image',
                'background_color',
                'background_video_url',
                'overlay_color',
            )
        }),
        (_('Content'), {
            'fields': ('content_html',)
        }),
        (_('Call to Action'), {
            'fields': (
                ('cta_text', 'cta_link', 'cta_style'),
                ('secondary_cta_text', 'secondary_cta_link'),
            )
        }),
        (_('Timing & Transition'), {
            'fields': (
                ('duration', 'transition', 'transition_duration'),
            )
        }),
        (_('Scheduling'), {
            'fields': ('publish_date', 'expire_date'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']

    def has_cta(self, obj):
        return bool(obj.cta_text)
    has_cta.boolean = True
    has_cta.short_description = _('CTA')

    def layers_count(self, obj):
        return obj.layers.count()
    layers_count.short_description = _('Layers')


@admin.register(SlideLayer)
class SlideLayerAdmin(admin.ModelAdmin):
    """Admin for Slide Layers"""

    list_display = [
        'name', 'slide', 'layer_type', 'order',
        'animation_in', 'start_time', 'responsive_display'
    ]
    list_filter = ['layer_type', 'animation_in', 'slide__slider']
    search_fields = ['name', 'content']
    list_editable = ['order']
    raw_id_fields = ['slide', 'media_file']

    fieldsets = (
        (None, {
            'fields': ('slide', 'name', 'layer_type', 'order')
        }),
        (_('Content'), {
            'fields': ('content', 'media_file', 'link_url', 'link_target')
        }),
        (_('Position'), {
            'fields': (
                ('position_x', 'position_y'),
                ('offset_x', 'offset_y'),
                ('width', 'height'),
            )
        }),
        (_('Animation'), {
            'fields': (
                ('animation_in', 'animation_out'),
                ('start_time', 'end_time', 'animation_speed'),
            )
        }),
        (_('Styling'), {
            'fields': ('css_class', 'custom_style')
        }),
        (_('Responsive'), {
            'fields': ('visible_desktop', 'visible_tablet', 'visible_mobile')
        }),
    )

    def responsive_display(self, obj):
        icons = []
        if obj.visible_desktop:
            icons.append('🖥️')
        if obj.visible_tablet:
            icons.append('📱')
        if obj.visible_mobile:
            icons.append('📲')
        return ' '.join(icons) or '-'
    responsive_display.short_description = _('Visible')


class HomepageSectionItemInline(admin.TabularInline):
    """Inline admin for section items"""
    model = HomepageSectionItem
    extra = 0
    fields = ['title', 'order', 'is_active', 'icon_class', 'link_url']
    ordering = ['order']


@admin.register(HomepageSection)
class HomepageSectionAdmin(admin.ModelAdmin):
    """Admin for Homepage Sections"""

    list_display = [
        'name', 'section_type', 'language', 'order',
        'is_active', 'items_count', 'updated_at'
    ]
    list_filter = ['is_active', 'section_type', 'language']
    search_fields = ['name', 'title', 'description']
    list_editable = ['order', 'is_active']
    raw_id_fields = ['slider', 'background_image', 'translation_of']
    inlines = [HomepageSectionItemInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'section_type', 'order', 'is_active')
        }),
        (_('Content'), {
            'fields': ('title', 'subtitle', 'description', 'content_html')
        }),
        (_('Slider'), {
            'fields': ('slider',),
            'classes': ('collapse',)
        }),
        (_('Background'), {
            'fields': (
                'background_image',
                'background_color',
                'background_style',
            )
        }),
        (_('Styling'), {
            'fields': (
                ('css_class', 'css_id'),
                ('padding_top', 'padding_bottom'),
                'text_color',
            )
        }),
        (_('Call to Action'), {
            'fields': ('cta_text', 'cta_link')
        }),
        (_('Language'), {
            'fields': ('language', 'translation_of')
        }),
        (_('Advanced Settings'), {
            'fields': ('settings',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = _('Items')


@admin.register(HomepageSectionItem)
class HomepageSectionItemAdmin(admin.ModelAdmin):
    """Admin for Homepage Section Items"""

    list_display = [
        'title', 'section', 'order', 'is_active',
        'has_image', 'has_link', 'updated_at'
    ]
    list_filter = ['is_active', 'section__section_type', 'section']
    search_fields = ['title', 'subtitle', 'description']
    list_editable = ['order', 'is_active']
    raw_id_fields = ['section', 'image']

    fieldsets = (
        (None, {
            'fields': ('section', 'title', 'subtitle', 'description', 'order', 'is_active')
        }),
        (_('Media'), {
            'fields': ('image', 'icon_class')
        }),
        (_('Link'), {
            'fields': ('link_url', 'link_text')
        }),
        (_('Testimonial Fields'), {
            'fields': ('author_name', 'author_title', 'rating'),
            'classes': ('collapse',)
        }),
        (_('Statistics Fields'), {
            'fields': ('stat_value', 'stat_suffix'),
            'classes': ('collapse',)
        }),
        (_('Custom Data'), {
            'fields': ('custom_data',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = _('Image')

    def has_link(self, obj):
        return bool(obj.link_url)
    has_link.boolean = True
    has_link.short_description = _('Link')


@admin.register(FrontPageSettings)
class FrontPageSettingsAdmin(admin.ModelAdmin):
    """Admin for Front Page Settings"""

    list_display = ['language', 'wp_page_id', 'main_slider', 'header_style', 'updated_at']
    list_filter = ['language', 'header_style']
    raw_id_fields = ['main_slider', 'og_image', 'header_logo_light', 'header_logo_dark']

    fieldsets = (
        (None, {
            'fields': ('language', 'wp_page_id')
        }),
        (_('Main Slider'), {
            'fields': ('main_slider',)
        }),
        (_('SEO / Meta'), {
            'fields': ('meta_title', 'meta_description', 'og_image')
        }),
        (_('Header'), {
            'fields': ('header_style', 'header_logo_light', 'header_logo_dark')
        }),
        (_('Custom Code'), {
            'fields': ('custom_css', 'custom_js_header', 'custom_js_footer'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
