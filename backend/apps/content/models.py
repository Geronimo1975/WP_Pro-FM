"""
Content models for WordPress content management and AI generation.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Post(models.Model):
    """WordPress Post synchronized and managed"""

    class PostStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PENDING = 'pending', _('Pending Review')
        PUBLISH = 'publish', _('Published')
        PRIVATE = 'private', _('Private')
        TRASH = 'trash', _('Trash')

    class PostType(models.TextChoices):
        POST = 'post', _('Post')
        PAGE = 'page', _('Page')
        PRODUCT = 'product', _('Product')

    # WordPress sync fields
    wp_id = models.IntegerField(_('WordPress ID'), unique=True, null=True, blank=True)
    wp_link = models.URLField(_('WordPress Link'), max_length=500, blank=True)

    # Content fields
    title = models.CharField(_('Title'), max_length=255)
    slug = models.SlugField(_('Slug'), max_length=255, blank=True)
    content = models.TextField(_('Content'))
    excerpt = models.TextField(_('Excerpt'), blank=True)

    # Type and status
    post_type = models.CharField(
        _('Post Type'),
        max_length=20,
        choices=PostType.choices,
        default=PostType.POST
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=PostStatus.choices,
        default=PostStatus.DRAFT
    )

    # Taxonomy
    categories = models.ManyToManyField('Category', related_name='posts', blank=True)
    tags = models.ManyToManyField('Tag', related_name='posts', blank=True)

    # Featured image
    featured_image = models.ForeignKey(
        'media.MediaFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='featured_posts'
    )

    # SEO fields (Rank Math)
    focus_keyword = models.CharField(_('Focus Keyword'), max_length=255, blank=True)
    meta_title = models.CharField(_('Meta Title'), max_length=100, blank=True)
    meta_description = models.CharField(_('Meta Description'), max_length=200, blank=True)
    seo_score = models.IntegerField(_('SEO Score'), null=True, blank=True)

    # Language (WPML)
    language = models.CharField(_('Language'), max_length=10, default='de')
    translation_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='translations'
    )

    # AI generation tracking
    is_ai_generated = models.BooleanField(_('AI Generated'), default=False)
    ai_prompt = models.TextField(_('AI Prompt Used'), blank=True)
    generation_model = models.CharField(_('Generation Model'), max_length=50, blank=True)

    # Timestamps
    wp_created_at = models.DateTimeField(_('WP Created At'), null=True, blank=True)
    wp_modified_at = models.DateTimeField(_('WP Modified At'), null=True, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    published_at = models.DateTimeField(_('Published At'), null=True, blank=True)
    synced_at = models.DateTimeField(_('Last Synced'), null=True, blank=True)

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wp_id']),
            models.Index(fields=['status', 'post_type']),
            models.Index(fields=['language']),
        ]

    def __str__(self):
        return self.title


class Category(models.Model):
    """WordPress Category"""

    wp_id = models.IntegerField(_('WordPress ID'), unique=True, null=True, blank=True)
    name = models.CharField(_('Name'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    language = models.CharField(_('Language'), max_length=10, default='de')

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    """WordPress Tag"""

    wp_id = models.IntegerField(_('WordPress ID'), unique=True, null=True, blank=True)
    name = models.CharField(_('Name'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=100)
    language = models.CharField(_('Language'), max_length=10, default='de')

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        ordering = ['name']

    def __str__(self):
        return self.name


class ContentTemplate(models.Model):
    """Templates for AI content generation"""

    class TemplateType(models.TextChoices):
        BLOG_POST = 'blog_post', _('Blog Post')
        SERVICE_PAGE = 'service_page', _('Service Page')
        LANDING_PAGE = 'landing_page', _('Landing Page')
        PRODUCT = 'product', _('Product Description')
        FAQ = 'faq', _('FAQ')

    name = models.CharField(_('Name'), max_length=100)
    template_type = models.CharField(
        _('Template Type'),
        max_length=20,
        choices=TemplateType.choices
    )
    system_prompt = models.TextField(_('System Prompt'))
    user_prompt_template = models.TextField(_('User Prompt Template'))
    variables = models.JSONField(_('Variables'), default=list, blank=True)
    default_word_count = models.IntegerField(_('Default Word Count'), default=800)
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Content Template')
        verbose_name_plural = _('Content Templates')
        ordering = ['template_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class ContentGenerationJob(models.Model):
    """Track AI content generation jobs"""

    class JobStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROCESSING = 'processing', _('Processing')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')

    template = models.ForeignKey(
        ContentTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='jobs'
    )
    variables = models.JSONField(_('Variables Used'), default=dict)
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=JobStatus.choices,
        default=JobStatus.PENDING
    )
    result_post = models.ForeignKey(
        Post,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generation_job'
    )
    error_message = models.TextField(_('Error Message'), blank=True)
    tokens_used = models.IntegerField(_('Tokens Used'), default=0)
    cost_usd = models.DecimalField(_('Cost (USD)'), max_digits=10, decimal_places=4, default=0)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)

    class Meta:
        verbose_name = _('Content Generation Job')
        verbose_name_plural = _('Content Generation Jobs')
        ordering = ['-created_at']

    def __str__(self):
        return f"Job {self.id} - {self.status}"
