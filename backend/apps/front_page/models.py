"""
Models for Front Page management including Slider Revolution.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.content.wpml import WPMLLanguage


class SliderRevolution(models.Model):
    """Slider Revolution slider management"""

    class SliderType(models.TextChoices):
        STANDARD = 'standard', _('Standard Slider')
        HERO = 'hero', _('Hero Scene')
        CAROUSEL = 'carousel', _('Carousel')
        SHOWCASE = 'showcase', _('Showcase')

    # WordPress sync
    wp_slider_id = models.IntegerField(
        _('WordPress Slider ID'),
        unique=True,
        null=True,
        blank=True,
        help_text=_('Slider Revolution slider ID in WordPress')
    )
    wp_alias = models.CharField(
        _('Slider Alias'),
        max_length=100,
        blank=True,
        help_text=_('Shortcode alias for the slider')
    )

    # Basic info
    name = models.CharField(_('Name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    slider_type = models.CharField(
        _('Slider Type'),
        max_length=20,
        choices=SliderType.choices,
        default=SliderType.STANDARD
    )
    is_active = models.BooleanField(_('Active'), default=True)

    # Display settings
    width = models.IntegerField(_('Width'), default=1920)
    height = models.IntegerField(_('Height'), default=800)
    autoplay = models.BooleanField(_('Autoplay'), default=True)
    autoplay_delay = models.IntegerField(
        _('Autoplay Delay (ms)'),
        default=5000,
        help_text=_('Delay between slides in milliseconds')
    )
    loop = models.BooleanField(_('Loop'), default=True)
    pause_on_hover = models.BooleanField(_('Pause on Hover'), default=True)

    # Navigation
    show_navigation = models.BooleanField(_('Show Navigation Arrows'), default=True)
    show_bullets = models.BooleanField(_('Show Bullets'), default=True)
    show_progress = models.BooleanField(_('Show Progress Bar'), default=False)

    # WPML
    language = models.CharField(
        _('Language'),
        max_length=10,
        choices=WPMLLanguage.get_choices(),
        default=WPMLLanguage.DEFAULT,
        db_index=True
    )
    translation_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='translations'
    )

    # Custom CSS/JS
    custom_css = models.TextField(_('Custom CSS'), blank=True)
    custom_js = models.TextField(_('Custom JavaScript'), blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    synced_at = models.DateTimeField(_('Last Synced'), null=True, blank=True)

    class Meta:
        verbose_name = _('Slider Revolution')
        verbose_name_plural = _('Slider Revolutions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wp_slider_id']),
            models.Index(fields=['language']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} [{self.language}]"

    @property
    def shortcode(self):
        """Generate WordPress shortcode for this slider"""
        if self.wp_alias:
            return f'[rev_slider alias="{self.wp_alias}"]'
        return ''


class Slide(models.Model):
    """Individual slide within a Slider Revolution slider"""

    class SlideStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')

    class TransitionType(models.TextChoices):
        FADE = 'fade', _('Fade')
        SLIDE_LEFT = 'slideleft', _('Slide Left')
        SLIDE_RIGHT = 'slideright', _('Slide Right')
        SLIDE_UP = 'slideup', _('Slide Up')
        SLIDE_DOWN = 'slidedown', _('Slide Down')
        ZOOM_IN = 'zoomin', _('Zoom In')
        ZOOM_OUT = 'zoomout', _('Zoom Out')
        ROTATE = 'rotate', _('Rotate')

    slider = models.ForeignKey(
        SliderRevolution,
        on_delete=models.CASCADE,
        related_name='slides'
    )

    # Basic info
    title = models.CharField(_('Title'), max_length=200)
    subtitle = models.CharField(_('Subtitle'), max_length=300, blank=True)
    order = models.PositiveIntegerField(_('Order'), default=0)
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=SlideStatus.choices,
        default=SlideStatus.DRAFT
    )

    # Background
    background_image = models.ForeignKey(
        'media.MediaFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='slide_backgrounds'
    )
    background_color = models.CharField(
        _('Background Color'),
        max_length=20,
        blank=True,
        help_text=_('Hex color code, e.g., #ffffff')
    )
    background_video_url = models.URLField(
        _('Background Video URL'),
        max_length=500,
        blank=True
    )
    overlay_color = models.CharField(
        _('Overlay Color'),
        max_length=20,
        blank=True,
        help_text=_('Overlay color with opacity, e.g., rgba(0,0,0,0.5)')
    )

    # Content
    content_html = models.TextField(
        _('Content HTML'),
        blank=True,
        help_text=_('HTML content for custom layers')
    )

    # Call to Action
    cta_text = models.CharField(_('CTA Button Text'), max_length=100, blank=True)
    cta_link = models.URLField(_('CTA Link'), max_length=500, blank=True)
    cta_style = models.CharField(
        _('CTA Style'),
        max_length=50,
        blank=True,
        help_text=_('CSS class for button styling')
    )
    secondary_cta_text = models.CharField(
        _('Secondary CTA Text'),
        max_length=100,
        blank=True
    )
    secondary_cta_link = models.URLField(
        _('Secondary CTA Link'),
        max_length=500,
        blank=True
    )

    # Timing
    duration = models.IntegerField(
        _('Duration (ms)'),
        default=5000,
        help_text=_('How long this slide is displayed')
    )
    transition = models.CharField(
        _('Transition'),
        max_length=20,
        choices=TransitionType.choices,
        default=TransitionType.FADE
    )
    transition_duration = models.IntegerField(
        _('Transition Duration (ms)'),
        default=1000
    )

    # Scheduling
    publish_date = models.DateTimeField(_('Publish Date'), null=True, blank=True)
    expire_date = models.DateTimeField(_('Expire Date'), null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Slide')
        verbose_name_plural = _('Slides')
        ordering = ['slider', 'order']
        indexes = [
            models.Index(fields=['slider', 'order']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.slider.name} - {self.title}"


class SlideLayer(models.Model):
    """Layer elements within a slide (text, images, buttons, etc.)"""

    class LayerType(models.TextChoices):
        TEXT = 'text', _('Text')
        IMAGE = 'image', _('Image')
        BUTTON = 'button', _('Button')
        VIDEO = 'video', _('Video')
        SHAPE = 'shape', _('Shape')
        ICON = 'icon', _('Icon')

    class AnimationType(models.TextChoices):
        FADE = 'fade', _('Fade')
        SLIDE = 'slide', _('Slide')
        ZOOM = 'zoom', _('Zoom')
        ROTATE = 'rotate', _('Rotate')
        BOUNCE = 'bounce', _('Bounce')
        FLIP = 'flip', _('Flip')

    slide = models.ForeignKey(
        Slide,
        on_delete=models.CASCADE,
        related_name='layers'
    )

    # Basic info
    name = models.CharField(_('Layer Name'), max_length=100)
    layer_type = models.CharField(
        _('Layer Type'),
        max_length=20,
        choices=LayerType.choices
    )
    order = models.PositiveIntegerField(_('Z-Index Order'), default=0)

    # Content
    content = models.TextField(
        _('Content'),
        blank=True,
        help_text=_('Text content or HTML')
    )
    media_file = models.ForeignKey(
        'media.MediaFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='slide_layers'
    )
    link_url = models.URLField(_('Link URL'), max_length=500, blank=True)
    link_target = models.CharField(
        _('Link Target'),
        max_length=20,
        default='_self',
        choices=[('_self', 'Same Window'), ('_blank', 'New Window')]
    )

    # Position (responsive)
    position_x = models.CharField(
        _('X Position'),
        max_length=50,
        default='center',
        help_text=_('left, center, right, or pixel value')
    )
    position_y = models.CharField(
        _('Y Position'),
        max_length=50,
        default='middle',
        help_text=_('top, middle, bottom, or pixel value')
    )
    offset_x = models.IntegerField(_('X Offset (px)'), default=0)
    offset_y = models.IntegerField(_('Y Offset (px)'), default=0)
    width = models.CharField(_('Width'), max_length=50, blank=True)
    height = models.CharField(_('Height'), max_length=50, blank=True)

    # Animation
    animation_in = models.CharField(
        _('Animation In'),
        max_length=20,
        choices=AnimationType.choices,
        default=AnimationType.FADE
    )
    animation_out = models.CharField(
        _('Animation Out'),
        max_length=20,
        choices=AnimationType.choices,
        default=AnimationType.FADE
    )
    start_time = models.IntegerField(
        _('Start Time (ms)'),
        default=0,
        help_text=_('When the layer appears')
    )
    end_time = models.IntegerField(
        _('End Time (ms)'),
        null=True,
        blank=True,
        help_text=_('When the layer disappears (empty = slide end)')
    )
    animation_speed = models.IntegerField(
        _('Animation Speed (ms)'),
        default=500
    )

    # Styling
    css_class = models.CharField(_('CSS Class'), max_length=200, blank=True)
    custom_style = models.TextField(
        _('Custom Style'),
        blank=True,
        help_text=_('Inline CSS styles')
    )

    # Responsive visibility
    visible_desktop = models.BooleanField(_('Visible on Desktop'), default=True)
    visible_tablet = models.BooleanField(_('Visible on Tablet'), default=True)
    visible_mobile = models.BooleanField(_('Visible on Mobile'), default=True)

    class Meta:
        verbose_name = _('Slide Layer')
        verbose_name_plural = _('Slide Layers')
        ordering = ['slide', 'order']

    def __str__(self):
        return f"{self.slide.title} - {self.name}"


class HomepageSection(models.Model):
    """Configurable sections for the homepage"""

    class SectionType(models.TextChoices):
        SLIDER = 'slider', _('Slider Revolution')
        HERO = 'hero', _('Hero Section')
        SERVICES = 'services', _('Services Grid')
        ABOUT = 'about', _('About Us')
        FEATURES = 'features', _('Features List')
        TESTIMONIALS = 'testimonials', _('Testimonials')
        CLIENTS = 'clients', _('Clients/Partners')
        CTA = 'cta', _('Call to Action')
        CONTACT = 'contact', _('Contact Form')
        BLOG = 'blog', _('Latest Blog Posts')
        GALLERY = 'gallery', _('Gallery')
        VIDEO = 'video', _('Video Section')
        STATS = 'stats', _('Statistics/Counters')
        TEAM = 'team', _('Team Members')
        FAQ = 'faq', _('FAQ Section')
        CUSTOM = 'custom', _('Custom HTML')

    # Basic info
    name = models.CharField(_('Section Name'), max_length=100)
    section_type = models.CharField(
        _('Section Type'),
        max_length=20,
        choices=SectionType.choices
    )
    order = models.PositiveIntegerField(_('Display Order'), default=0)
    is_active = models.BooleanField(_('Active'), default=True)

    # Content
    title = models.CharField(_('Title'), max_length=200, blank=True)
    subtitle = models.CharField(_('Subtitle'), max_length=300, blank=True)
    description = models.TextField(_('Description'), blank=True)
    content_html = models.TextField(_('Custom HTML Content'), blank=True)

    # Linked slider (for slider type)
    slider = models.ForeignKey(
        SliderRevolution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='homepage_sections'
    )

    # Background
    background_image = models.ForeignKey(
        'media.MediaFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='section_backgrounds'
    )
    background_color = models.CharField(
        _('Background Color'),
        max_length=20,
        blank=True
    )
    background_style = models.CharField(
        _('Background Style'),
        max_length=50,
        blank=True,
        help_text=_('CSS background-size, background-position, etc.')
    )

    # Styling
    css_class = models.CharField(_('CSS Class'), max_length=200, blank=True)
    css_id = models.CharField(
        _('CSS ID'),
        max_length=100,
        blank=True,
        help_text=_('For anchor links')
    )
    padding_top = models.CharField(_('Padding Top'), max_length=20, default='60px')
    padding_bottom = models.CharField(_('Padding Bottom'), max_length=20, default='60px')
    text_color = models.CharField(_('Text Color'), max_length=20, blank=True)

    # CTA
    cta_text = models.CharField(_('CTA Text'), max_length=100, blank=True)
    cta_link = models.URLField(_('CTA Link'), max_length=500, blank=True)

    # WPML
    language = models.CharField(
        _('Language'),
        max_length=10,
        choices=WPMLLanguage.get_choices(),
        default=WPMLLanguage.DEFAULT,
        db_index=True
    )
    translation_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='translations'
    )

    # Settings (JSON for flexible configuration)
    settings = models.JSONField(
        _('Section Settings'),
        default=dict,
        blank=True,
        help_text=_('Additional configuration options as JSON')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Homepage Section')
        verbose_name_plural = _('Homepage Sections')
        ordering = ['language', 'order']
        indexes = [
            models.Index(fields=['language', 'order']),
            models.Index(fields=['is_active']),
            models.Index(fields=['section_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_section_type_display()}) [{self.language}]"


class HomepageSectionItem(models.Model):
    """Items within a homepage section (services, features, testimonials, etc.)"""

    section = models.ForeignKey(
        HomepageSection,
        on_delete=models.CASCADE,
        related_name='items'
    )

    # Basic info
    title = models.CharField(_('Title'), max_length=200)
    subtitle = models.CharField(_('Subtitle'), max_length=300, blank=True)
    description = models.TextField(_('Description'), blank=True)
    order = models.PositiveIntegerField(_('Order'), default=0)
    is_active = models.BooleanField(_('Active'), default=True)

    # Media
    image = models.ForeignKey(
        'media.MediaFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='section_items'
    )
    icon_class = models.CharField(
        _('Icon Class'),
        max_length=100,
        blank=True,
        help_text=_('FontAwesome or other icon class')
    )

    # Link
    link_url = models.URLField(_('Link URL'), max_length=500, blank=True)
    link_text = models.CharField(_('Link Text'), max_length=100, blank=True)

    # For testimonials
    author_name = models.CharField(_('Author Name'), max_length=100, blank=True)
    author_title = models.CharField(_('Author Title'), max_length=200, blank=True)
    rating = models.PositiveSmallIntegerField(
        _('Rating'),
        null=True,
        blank=True,
        help_text=_('Rating from 1-5')
    )

    # For statistics
    stat_value = models.CharField(
        _('Statistic Value'),
        max_length=50,
        blank=True,
        help_text=_('e.g., 500+, 98%, 24/7')
    )
    stat_suffix = models.CharField(
        _('Statistic Suffix'),
        max_length=20,
        blank=True,
        help_text=_('e.g., +, %, Jahre')
    )

    # Custom data
    custom_data = models.JSONField(
        _('Custom Data'),
        default=dict,
        blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Section Item')
        verbose_name_plural = _('Section Items')
        ordering = ['section', 'order']

    def __str__(self):
        return f"{self.section.name} - {self.title}"


class FrontPageSettings(models.Model):
    """Global settings for the front page"""

    # Page assignment
    language = models.CharField(
        _('Language'),
        max_length=10,
        choices=WPMLLanguage.get_choices(),
        default=WPMLLanguage.DEFAULT,
        unique=True
    )
    wp_page_id = models.IntegerField(
        _('WordPress Page ID'),
        null=True,
        blank=True,
        help_text=_('The WordPress page ID set as front page')
    )

    # Main slider
    main_slider = models.ForeignKey(
        SliderRevolution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='front_page_settings'
    )

    # Meta
    meta_title = models.CharField(_('Meta Title'), max_length=100, blank=True)
    meta_description = models.CharField(_('Meta Description'), max_length=200, blank=True)
    og_image = models.ForeignKey(
        'media.MediaFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='front_page_og'
    )

    # Header settings
    header_style = models.CharField(
        _('Header Style'),
        max_length=50,
        default='transparent',
        choices=[
            ('transparent', _('Transparent')),
            ('solid', _('Solid')),
            ('sticky', _('Sticky')),
        ]
    )
    header_logo_light = models.ForeignKey(
        'media.MediaFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='front_page_logo_light'
    )
    header_logo_dark = models.ForeignKey(
        'media.MediaFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='front_page_logo_dark'
    )

    # Custom code
    custom_css = models.TextField(_('Custom CSS'), blank=True)
    custom_js_header = models.TextField(_('Custom JS (Header)'), blank=True)
    custom_js_footer = models.TextField(_('Custom JS (Footer)'), blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Front Page Settings')
        verbose_name_plural = _('Front Page Settings')

    def __str__(self):
        return f"Front Page Settings [{self.language}]"
