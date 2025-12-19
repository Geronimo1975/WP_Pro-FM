"""
Admin configuration for Front Page management.
"""

from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect
from django.contrib import messages
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.decorators import display, action

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


class SlideInlineWithPreview(StackedInline):
    """Inline admin for slides with preview"""
    model = Slide
    extra = 0
    fields = [
        'slide_preview', 'title', 'subtitle', 'order', 'status',
        'background_image', 'background_color', 'duration', 'transition',
        'cta_text', 'cta_link'
    ]
    readonly_fields = ['slide_preview']
    ordering = ['order']
    show_change_link = True

    def slide_preview(self, obj):
        if not obj.pk:
            return '-'
        if obj.background_image and obj.background_image.wp_url:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 150px; object-fit: cover; border-radius: 4px;" />',
                obj.background_image.wp_url
            )
        elif obj.background_image and obj.background_image.file:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 150px; object-fit: cover; border-radius: 4px;" />',
                obj.background_image.file.url
            )
        elif obj.background_color:
            return format_html(
                '<div style="width: 150px; height: 80px; background: {}; border-radius: 4px;"></div>',
                obj.background_color
            )
        return format_html(
            '<div style="width: 150px; height: 80px; background: #f0f0f0; border-radius: 4px; '
            'display: flex; align-items: center; justify-content: center; color: #999;">'
            '<span class="material-symbols-outlined">image</span></div>'
        )
    slide_preview.short_description = _('Preview')


@admin.register(SliderRevolution)
class SliderRevolutionAdmin(ModelAdmin):
    """Admin for Slider Revolution"""

    list_display = [
        'slider_preview', 'name', 'slider_type_display', 'language_display', 'active_status',
        'slides_count', 'dimensions_display', 'shortcode_display', 'action_buttons'
    ]
    list_filter = ['is_active', 'slider_type', 'language']
    list_filter_submit = True
    search_fields = ['name', 'wp_alias', 'description']
    readonly_fields = ['slider_preview_large', 'shortcode', 'created_at', 'updated_at', 'synced_at']
    inlines = [SlideInlineWithPreview]
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': ('slider_preview_large', 'name', 'description', 'slider_type', 'is_active')
        }),
        (_('WordPress Sync'), {
            'fields': ('wp_slider_id', 'wp_alias', 'shortcode', 'synced_at'),
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

    def slider_preview(self, obj):
        """Small preview for list view - shows first slide's background"""
        first_slide = obj.slides.filter(status='published').order_by('order').first()
        if first_slide and first_slide.background_image:
            url = first_slide.background_image.wp_url or (first_slide.background_image.file.url if first_slide.background_image.file else None)
            if url:
                return format_html(
                    '<img src="{}" style="max-height: 50px; max-width: 90px; object-fit: cover; border-radius: 4px;" loading="lazy" />',
                    url
                )
        return format_html(
            '<div style="width: 90px; height: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
            'border-radius: 4px; display: flex; align-items: center; justify-content: center;">'
            '<span class="material-symbols-outlined" style="color: white;">slideshow</span></div>'
        )
    slider_preview.short_description = ''

    def slider_preview_large(self, obj):
        """Large preview for detail view"""
        slides = obj.slides.filter(status='published').order_by('order')[:5]
        if not slides:
            slides = obj.slides.order_by('order')[:5]

        if not slides:
            return format_html(
                '<div style="text-align: center; padding: 40px; background: #f5f5f5; border-radius: 8px;">'
                '<span class="material-symbols-outlined" style="font-size: 48px; color: #999;">slideshow</span>'
                '<p style="margin-top: 16px; color: #666;">No slides yet. Add slides below.</p>'
                '</div>'
            )

        html = '<div style="display: flex; gap: 10px; flex-wrap: wrap; padding: 16px; background: #f8f9fa; border-radius: 8px;">'
        for i, slide in enumerate(slides):
            bg_style = 'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);'
            if slide.background_image:
                url = slide.background_image.wp_url or (slide.background_image.file.url if slide.background_image.file else None)
                if url:
                    bg_style = f'background-image: url({url}); background-size: cover; background-position: center;'
            elif slide.background_color:
                bg_style = f'background: {slide.background_color};'

            status_color = '#4CAF50' if slide.status == 'published' else '#ff9800'
            html += f'''
                <div style="position: relative; width: 180px;">
                    <div style="{bg_style} height: 100px; border-radius: 8px; position: relative;">
                        <span style="position: absolute; top: 4px; left: 4px; background: {status_color}; color: white;
                              padding: 2px 6px; border-radius: 4px; font-size: 10px;">{i+1}</span>
                    </div>
                    <p style="margin: 4px 0 0; font-size: 12px; color: #666; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        {slide.title or "Untitled"}
                    </p>
                </div>
            '''
        html += '</div>'

        total = obj.slides.count()
        if total > 5:
            html += f'<p style="margin-top: 8px; color: #666; font-size: 12px;">Showing 5 of {total} slides</p>'

        return format_html(html)
    slider_preview_large.short_description = _('Slider Preview')

    def slides_count(self, obj):
        total = obj.slides.count()
        published = obj.slides.filter(status='published').count()
        if total == 0:
            return format_html('<span style="color: #999;">0</span>')
        return format_html(
            '<span title="{} published">{} <span style="color: #999;">({} active)</span></span>',
            published, total, published
        )
    slides_count.short_description = _('Slides')

    def dimensions_display(self, obj):
        return format_html(
            '<span style="font-family: monospace; color: #666;">{} × {}</span>',
            obj.width, obj.height
        )
    dimensions_display.short_description = _('Size')

    def shortcode_display(self, obj):
        if obj.shortcode:
            return format_html(
                '<code style="background:#e8f4fc;padding:4px 8px;border-radius:4px;font-size:11px;cursor:pointer;" '
                'onclick="navigator.clipboard.writeText(this.innerText)" title="Click to copy">{}</code>',
                obj.shortcode
            )
        return format_html('<span style="color:#999;">-</span>')
    shortcode_display.short_description = _('Shortcode')

    def action_buttons(self, obj):
        buttons = []

        # Duplicate slider button
        duplicate_url = reverse('admin:front_page_sliderrevolution_duplicate', args=[obj.pk])
        buttons.append(format_html(
            '<a href="{}" class="button" style="padding: 4px 8px; font-size: 11px; margin-right: 4px;" title="Duplicate Slider">'
            '<span class="material-symbols-outlined" style="font-size: 14px; vertical-align: middle;">content_copy</span>'
            '</a>',
            duplicate_url
        ))

        # Preview button (generates preview HTML)
        if obj.slides.exists():
            preview_url = reverse('admin:front_page_sliderrevolution_preview', args=[obj.pk])
            buttons.append(format_html(
                '<a href="{}" target="_blank" class="button" style="padding: 4px 8px; font-size: 11px; background: #2196F3; color: white;" title="Preview Slider">'
                '<span class="material-symbols-outlined" style="font-size: 14px; vertical-align: middle;">visibility</span>'
                '</a>',
                preview_url
            ))

        return format_html(''.join([str(b) for b in buttons])) if buttons else '-'
    action_buttons.short_description = _('Actions')

    @display(description="Type", ordering="slider_type", label=True)
    def slider_type_display(self, obj):
        colors = {
            'standard': 'secondary',
            'hero': 'primary',
            'carousel': 'info',
            'showcase': 'warning',
        }
        return obj.slider_type.title() if obj.slider_type else '-', colors.get(obj.slider_type, 'secondary')

    @display(description="Lang", ordering="language", label=True)
    def language_display(self, obj):
        colors = {'de': 'primary', 'en': 'info', 'fr': 'warning', 'es': 'success'}
        return obj.language.upper() if obj.language else '-', colors.get(obj.language, 'secondary')

    @display(description="Status", label=True)
    def active_status(self, obj):
        if obj.is_active:
            return "Active", "success"
        return "Inactive", "secondary"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/duplicate/', self.admin_site.admin_view(self.duplicate_slider), name='front_page_sliderrevolution_duplicate'),
            path('<int:pk>/preview/', self.admin_site.admin_view(self.preview_slider), name='front_page_sliderrevolution_preview'),
        ]
        return custom_urls + urls

    def duplicate_slider(self, request, pk):
        """Duplicate a slider with all its slides and layers"""
        from django.utils import timezone

        original = self.get_object(request, pk)
        if not original:
            messages.error(request, 'Slider not found.')
            return HttpResponseRedirect(reverse('admin:front_page_sliderrevolution_changelist'))

        # Create new slider
        new_slider = SliderRevolution.objects.create(
            name=f"{original.name} (Copy)",
            description=original.description,
            slider_type=original.slider_type,
            is_active=False,
            width=original.width,
            height=original.height,
            autoplay=original.autoplay,
            autoplay_delay=original.autoplay_delay,
            loop=original.loop,
            pause_on_hover=original.pause_on_hover,
            show_navigation=original.show_navigation,
            show_bullets=original.show_bullets,
            show_progress=original.show_progress,
            language=original.language,
            custom_css=original.custom_css,
            custom_js=original.custom_js,
        )

        # Duplicate slides
        for slide in original.slides.all():
            new_slide = Slide.objects.create(
                slider=new_slider,
                title=slide.title,
                subtitle=slide.subtitle,
                order=slide.order,
                status='draft',
                background_image=slide.background_image,
                background_color=slide.background_color,
                background_video_url=slide.background_video_url,
                overlay_color=slide.overlay_color,
                content_html=slide.content_html,
                cta_text=slide.cta_text,
                cta_link=slide.cta_link,
                cta_style=slide.cta_style,
                secondary_cta_text=slide.secondary_cta_text,
                secondary_cta_link=slide.secondary_cta_link,
                duration=slide.duration,
                transition=slide.transition,
                transition_duration=slide.transition_duration,
            )

            # Duplicate layers
            for layer in slide.layers.all():
                SlideLayer.objects.create(
                    slide=new_slide,
                    name=layer.name,
                    layer_type=layer.layer_type,
                    order=layer.order,
                    content=layer.content,
                    media_file=layer.media_file,
                    link_url=layer.link_url,
                    link_target=layer.link_target,
                    position_x=layer.position_x,
                    position_y=layer.position_y,
                    offset_x=layer.offset_x,
                    offset_y=layer.offset_y,
                    width=layer.width,
                    height=layer.height,
                    animation_in=layer.animation_in,
                    animation_out=layer.animation_out,
                    start_time=layer.start_time,
                    end_time=layer.end_time,
                    animation_speed=layer.animation_speed,
                    css_class=layer.css_class,
                    custom_style=layer.custom_style,
                    visible_desktop=layer.visible_desktop,
                    visible_tablet=layer.visible_tablet,
                    visible_mobile=layer.visible_mobile,
                )

        messages.success(request, f'Slider duplicated successfully: "{new_slider.name}"')
        return HttpResponseRedirect(reverse('admin:front_page_sliderrevolution_change', args=[new_slider.pk]))

    def preview_slider(self, request, pk):
        """Generate preview HTML for slider"""
        from django.http import HttpResponse

        slider = self.get_object(request, pk)
        if not slider:
            return HttpResponse('Slider not found', status=404)

        slides_html = ''
        for slide in slider.slides.filter(status='published').order_by('order'):
            bg_style = ''
            if slide.background_image:
                url = slide.background_image.wp_url or (slide.background_image.file.url if slide.background_image.file else None)
                if url:
                    bg_style = f'background-image: url({url}); background-size: cover; background-position: center;'
            if slide.background_color:
                bg_style += f' background-color: {slide.background_color};'
            if slide.overlay_color:
                overlay = f'<div style="position:absolute;top:0;left:0;right:0;bottom:0;background:{slide.overlay_color};"></div>'
            else:
                overlay = ''

            cta_html = ''
            if slide.cta_text and slide.cta_link:
                cta_html = f'<a href="{slide.cta_link}" style="display:inline-block;padding:12px 24px;background:#4CAF50;color:white;text-decoration:none;border-radius:4px;margin-top:20px;">{slide.cta_text}</a>'

            slides_html += f'''
            <div class="slide" style="{bg_style} width:100%; height:100%; position:relative;">
                {overlay}
                <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;color:white;text-shadow:0 2px 4px rgba(0,0,0,0.5);z-index:1;">
                    <h2 style="font-size:48px;margin:0;">{slide.title}</h2>
                    <p style="font-size:24px;margin:16px 0;">{slide.subtitle}</p>
                    {cta_html}
                </div>
            </div>
            '''

        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Preview: {slider.name}</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: system-ui, -apple-system, sans-serif; background: #1a1a1a; }}
                .slider-container {{ width: {slider.width}px; height: {slider.height}px; max-width: 100%; margin: 40px auto; overflow: hidden; position: relative; }}
                .slide {{ display: none; }}
                .slide.active {{ display: block; }}
                .nav-buttons {{ position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 10; }}
                .nav-buttons button {{ background: rgba(255,255,255,0.3); border: none; color: white; padding: 8px 16px; margin: 0 4px; cursor: pointer; border-radius: 4px; }}
                .nav-buttons button:hover {{ background: rgba(255,255,255,0.5); }}
                .info {{ text-align: center; color: #666; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="info">
                <h1 style="color:#fff;margin-bottom:10px;">Slider Preview: {slider.name}</h1>
                <p>Size: {slider.width} × {slider.height}px | Slides: {slider.slides.filter(status='published').count()}</p>
            </div>
            <div class="slider-container">
                {slides_html}
                <div class="nav-buttons">
                    <button onclick="prevSlide()">← Prev</button>
                    <button onclick="nextSlide()">Next →</button>
                </div>
            </div>
            <script>
                let current = 0;
                const slides = document.querySelectorAll('.slide');
                if (slides.length) slides[0].classList.add('active');

                function showSlide(n) {{
                    slides[current].classList.remove('active');
                    current = (n + slides.length) % slides.length;
                    slides[current].classList.add('active');
                }}
                function nextSlide() {{ showSlide(current + 1); }}
                function prevSlide() {{ showSlide(current - 1); }}

                {"setInterval(nextSlide, " + str(slider.autoplay_delay) + ");" if slider.autoplay else ""}
            </script>
        </body>
        </html>
        '''
        return HttpResponse(html)

    # Bulk actions
    @action(description="Activate selected sliders")
    def activate_sliders(self, request, queryset):
        count = queryset.update(is_active=True)
        messages.success(request, f'Activated {count} sliders.')

    @action(description="Deactivate selected sliders")
    def deactivate_sliders(self, request, queryset):
        count = queryset.update(is_active=False)
        messages.success(request, f'Deactivated {count} sliders.')

    actions = ['activate_sliders', 'deactivate_sliders']


@admin.register(Slide)
class SlideAdmin(ModelAdmin):
    """Admin for Slides"""

    list_display = [
        'slide_preview', 'title', 'slider', 'order', 'status_display', 'duration',
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
            'fields': ('slide_preview_large', 'slider', 'title', 'subtitle', 'order', 'status')
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
    readonly_fields = ['slide_preview_large', 'created_at', 'updated_at']

    def slide_preview(self, obj):
        """Small preview for list view"""
        if obj.background_image:
            url = obj.background_image.wp_url or (obj.background_image.file.url if obj.background_image.file else None)
            if url:
                return format_html(
                    '<img src="{}" style="max-height: 50px; max-width: 90px; object-fit: cover; border-radius: 4px;" loading="lazy" />',
                    url
                )
        if obj.background_color:
            return format_html(
                '<div style="width: 90px; height: 50px; background: {}; border-radius: 4px;"></div>',
                obj.background_color
            )
        return format_html(
            '<div style="width: 90px; height: 50px; background: #f0f0f0; border-radius: 4px; '
            'display: flex; align-items: center; justify-content: center;">'
            '<span class="material-symbols-outlined" style="color: #999;">image</span></div>'
        )
    slide_preview.short_description = ''

    def slide_preview_large(self, obj):
        """Large preview for detail view"""
        if not obj.pk:
            return '-'

        bg_style = 'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);'
        if obj.background_image:
            url = obj.background_image.wp_url or (obj.background_image.file.url if obj.background_image.file else None)
            if url:
                bg_style = f'background-image: url({url}); background-size: cover; background-position: center;'
        elif obj.background_color:
            bg_style = f'background: {obj.background_color};'

        overlay_html = ''
        if obj.overlay_color:
            overlay_html = f'<div style="position:absolute;top:0;left:0;right:0;bottom:0;background:{obj.overlay_color};"></div>'

        return format_html(
            '<div style="position: relative; width: 100%; max-width: 800px; height: 300px; {}; border-radius: 8px; overflow: hidden;">'
            '{}'
            '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;color:white;text-shadow:0 2px 4px rgba(0,0,0,0.5);z-index:1;">'
            '<h3 style="font-size:24px;margin:0;">{}</h3>'
            '<p style="font-size:14px;margin:8px 0;">{}</p>'
            '</div></div>',
            bg_style, overlay_html, obj.title or 'No Title', obj.subtitle or ''
        )
    slide_preview_large.short_description = _('Preview')

    @display(description="Status", ordering="status", label=True)
    def status_display(self, obj):
        colors = {
            'published': 'success',
            'draft': 'warning',
        }
        return obj.status.title() if obj.status else '-', colors.get(obj.status, 'secondary')

    def has_cta(self, obj):
        return bool(obj.cta_text)
    has_cta.boolean = True
    has_cta.short_description = _('CTA')

    def layers_count(self, obj):
        count = obj.layers.count()
        if count == 0:
            return format_html('<span style="color: #999;">0</span>')
        return count
    layers_count.short_description = _('Layers')

    # Bulk actions
    @action(description="Publish selected slides")
    def publish_slides(self, request, queryset):
        count = queryset.update(status='published')
        messages.success(request, f'Published {count} slides.')

    @action(description="Set to draft")
    def draft_slides(self, request, queryset):
        count = queryset.update(status='draft')
        messages.success(request, f'Set {count} slides to draft.')

    actions = ['publish_slides', 'draft_slides']


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
        colors = {
            'text': 'primary',
            'image': 'success',
            'button': 'warning',
            'video': 'info',
            'shape': 'secondary',
            'icon': 'secondary',
        }
        return obj.layer_type.title() if obj.layer_type else '-', colors.get(obj.layer_type, 'secondary')

    def responsive_display(self, obj):
        icons = []
        if obj.visible_desktop:
            icons.append('🖥️')
        if obj.visible_tablet:
            icons.append('📱')
        if obj.visible_mobile:
            icons.append('📲')
        return ' '.join(icons) or '-'
    responsive_display.short_description = _('Devices')


class HomepageSectionItemInline(TabularInline):
    """Inline admin for section items"""
    model = HomepageSectionItem
    extra = 0
    fields = ['title', 'order', 'is_active', 'icon_class', 'image', 'link_url']
    ordering = ['order']
    raw_id_fields = ['image']
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
        colors = {
            'slider': 'primary',
            'hero': 'success',
            'services': 'info',
            'testimonials': 'warning',
            'cta': 'danger',
        }
        label = obj.section_type.replace('_', ' ').title() if obj.section_type else '-'
        return label, colors.get(obj.section_type, 'secondary')

    @display(description="Lang", ordering="language", label=True)
    def language_display(self, obj):
        colors = {'de': 'primary', 'en': 'info', 'fr': 'warning', 'es': 'success'}
        return obj.language.upper() if obj.language else '-', colors.get(obj.language, 'secondary')

    @display(description="Status", label=True)
    def active_status(self, obj):
        if obj.is_active:
            return "Active", "success"
        return "Inactive", "secondary"

    def items_count(self, obj):
        count = obj.items.count()
        if count == 0:
            return format_html('<span style="color: #999;">0</span>')
        return count
    items_count.short_description = _('Items')


@admin.register(HomepageSectionItem)
class HomepageSectionItemAdmin(ModelAdmin):
    """Admin for Homepage Section Items"""

    list_display = [
        'item_preview', 'title', 'section', 'order', 'active_status',
        'has_link', 'updated_at'
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

    def item_preview(self, obj):
        if obj.image:
            url = obj.image.wp_url or (obj.image.file.url if obj.image.file else None)
            if url:
                return format_html(
                    '<img src="{}" style="max-height: 40px; max-width: 60px; object-fit: cover; border-radius: 4px;" />',
                    url
                )
        if obj.icon_class:
            return format_html(
                '<span style="font-size: 24px; color: #667eea;"><i class="{}"></i></span>',
                obj.icon_class
            )
        return format_html('<span class="material-symbols-outlined" style="color: #999;">category</span>')
    item_preview.short_description = ''

    @display(description="Status", label=True)
    def active_status(self, obj):
        if obj.is_active:
            return "Active", "success"
        return "Inactive", "secondary"

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
        colors = {'de': 'primary', 'en': 'info', 'fr': 'warning', 'es': 'success'}
        return obj.language.upper() if obj.language else '-', colors.get(obj.language, 'primary')
