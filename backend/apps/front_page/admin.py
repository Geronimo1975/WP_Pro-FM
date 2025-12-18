"""
Admin configuration for Front Page management.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from .models import (
    SliderRevolution,
    Slide,
    SlideLayer,
    HomepageSection,
    HomepageSectionItem,
    FrontPageSettings,
)


class SlideLayerInline(TabularInline):
    """Inline admin for slide layers"""
    model = SlideLayer
    extra = 0
    fields = [
        'name', 'layer_type', 'order', 'content', 'position_x', 'position_y',
        'animation_in', 'start_time', 'visible_desktop', 'visible_tablet', 'visible_mobile'
    ]
    ordering = ['order']
    tab = True


class SlideInline(TabularInline):
    """Inline admin for slides"""
    model = Slide
    extra = 0
    fields = ['title', 'order', 'status', 'duration', 'transition']
    ordering = ['order']
    show_change_link = True
    tab = True


@admin.register(SliderRevolution)
class SliderRevolutionAdmin(ModelAdmin):
    """Admin for Slider Revolution"""

    list_display = [
        'name', 'slider_type_display', 'language_display', 'active_status',
        'slides_count', 'shortcode_display', 'updated_at'
    ]
    list_filter = ['is_active', 'slider_type', 'language']
    list_filter_submit = True
    search_fields = ['name', 'wp_alias', 'description']
    readonly_fields = ['shortcode', 'created_at', 'updated_at', 'synced_at']
    inlines = [SlideInline]
    list_per_page = 25

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
                '<code style="background:#f4f4f4;padding:2px 6px;border-radius:4px;">{}</code>',
                obj.shortcode
            )
        return '-'
    shortcode_display.short_description = _('Shortcode')

    @display(description="Type", ordering="slider_type", label=True)
    def slider_type_display(self, obj):
        return obj.slider_type.title() if obj.slider_type else '-', "secondary"

    @display(description="Lang", ordering="language", label=True)
    def language_display(self, obj):
        return obj.language.upper() if obj.language else '-', "secondary"

    @display(description="Status", label=True)
    def active_status(self, obj):
        if obj.is_active:
            return "Active", "success"
        return "Inactive", "secondary"


@admin.register(Slide)
class SlideAdmin(ModelAdmin):
    """Admin for Slides"""

    list_display = [
        'title', 'slider', 'order', 'status_display', 'duration',
        'transition', 'has_cta', 'layers_count', 'updated_at'
    ]
    list_filter = ['status', 'slider', 'transition']
    list_filter_submit = True
    search_fields = ['title', 'subtitle', 'content_html']
    list_editable = ['order']
    raw_id_fields = ['slider', 'background_image']
    inlines = [SlideLayerInline]
    list_per_page = 25

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

    @display(description="Status", ordering="status", label=True)
    def status_display(self, obj):
        colors = {
            'published': 'success',
            'draft': 'warning',
            'scheduled': 'info',
        }
        return obj.status.title() if obj.status else '-', colors.get(obj.status, 'secondary')

    def has_cta(self, obj):
        return bool(obj.cta_text)
    has_cta.boolean = True
    has_cta.short_description = _('CTA')

    def layers_count(self, obj):
        return obj.layers.count()
    layers_count.short_description = _('Layers')


@admin.register(SlideLayer)
class SlideLayerAdmin(ModelAdmin):
    """Admin for Slide Layers"""

    list_display = [
        'name', 'slide', 'layer_type_display', 'order',
        'animation_in', 'start_time', 'responsive_display'
    ]
    list_filter = ['layer_type', 'animation_in', 'slide__slider']
    list_filter_submit = True
    search_fields = ['name', 'content']
    list_editable = ['order']
    raw_id_fields = ['slide', 'media_file']
    list_per_page = 25

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

    @display(description="Type", ordering="layer_type", label=True)
    def layer_type_display(self, obj):
        return obj.layer_type.title() if obj.layer_type else '-', "secondary"

    def responsive_display(self, obj):
        icons = []
        if obj.visible_desktop:
            icons.append('Desktop')
        if obj.visible_tablet:
            icons.append('Tablet')
        if obj.visible_mobile:
            icons.append('Mobile')
        return ', '.join(icons) or '-'
    responsive_display.short_description = _('Visible')


class HomepageSectionItemInline(TabularInline):
    """Inline admin for section items"""
    model = HomepageSectionItem
    extra = 0
    fields = ['title', 'order', 'is_active', 'icon_class', 'link_url']
    ordering = ['order']
    tab = True


@admin.register(HomepageSection)
class HomepageSectionAdmin(ModelAdmin):
    """Admin for Homepage Sections"""

    list_display = [
        'name', 'section_type_display', 'language_display', 'order',
        'active_status', 'items_count', 'updated_at'
    ]
    list_filter = ['is_active', 'section_type', 'language']
    list_filter_submit = True
    search_fields = ['name', 'title', 'description']
    list_editable = ['order']
    raw_id_fields = ['slider', 'background_image', 'translation_of']
    inlines = [HomepageSectionItemInline]
    list_per_page = 25

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

    @display(description="Type", ordering="section_type", label=True)
    def section_type_display(self, obj):
        return obj.section_type.replace('_', ' ').title() if obj.section_type else '-', "secondary"

    @display(description="Lang", ordering="language", label=True)
    def language_display(self, obj):
        return obj.language.upper() if obj.language else '-', "secondary"

    @display(description="Status", label=True)
    def active_status(self, obj):
        if obj.is_active:
            return "Active", "success"
        return "Inactive", "secondary"

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = _('Items')


@admin.register(HomepageSectionItem)
class HomepageSectionItemAdmin(ModelAdmin):
    """Admin for Homepage Section Items"""

    list_display = [
        'title', 'section', 'order', 'active_status',
        'has_image', 'has_link', 'updated_at'
    ]
    list_filter = ['is_active', 'section__section_type', 'section']
    list_filter_submit = True
    search_fields = ['title', 'subtitle', 'description']
    list_editable = ['order']
    raw_id_fields = ['section', 'image']
    list_per_page = 25

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

    @display(description="Status", label=True)
    def active_status(self, obj):
        if obj.is_active:
            return "Active", "success"
        return "Inactive", "secondary"

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = _('Image')

    def has_link(self, obj):
        return bool(obj.link_url)
    has_link.boolean = True
    has_link.short_description = _('Link')


@admin.register(FrontPageSettings)
class FrontPageSettingsAdmin(ModelAdmin):
    """Admin for Front Page Settings"""

    list_display = ['language_display', 'wp_page_id', 'main_slider', 'header_style', 'updated_at']
    list_filter = ['language', 'header_style']
    list_filter_submit = True
    raw_id_fields = ['main_slider', 'og_image', 'header_logo_light', 'header_logo_dark']
    list_per_page = 25

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

    @display(description="Language", ordering="language", label=True)
    def language_display(self, obj):
        return obj.language.upper() if obj.language else '-', "primary"
