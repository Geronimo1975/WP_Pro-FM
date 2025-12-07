"""
Content models for WordPress content management and AI generation.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .wpml import WPMLLanguage


class Post(models.Model):
    """WordPress Post synchronized and managed with WPML multilingual support"""

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

    # WPML Language & Translation fields
    language = models.CharField(
        _('Language'),
        max_length=10,
        choices=WPMLLanguage.get_choices(),
        default=WPMLLanguage.DEFAULT,
        db_index=True
    )
    wpml_trid = models.IntegerField(
        _('WPML Translation ID'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Translation group ID linking all translations together')
    )
    translation_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='translations',
        help_text=_('Original post this is a translation of')
    )
    source_language = models.CharField(
        _('Source Language'),
        max_length=10,
        blank=True,
        help_text=_('Language of the original content (empty if this is the original)')
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
            models.Index(fields=['wpml_trid']),
            models.Index(fields=['language', 'wpml_trid']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_original(self) -> bool:
        """Check if this post is the original (not a translation)"""
        return not self.source_language and not self.translation_of

    @property
    def translation_group(self):
        """Get all posts in the same translation group"""
        if self.wpml_trid:
            return Post.objects.filter(wpml_trid=self.wpml_trid)
        if self.translation_of:
            # Include original and all its translations
            return Post.objects.filter(
                models.Q(id=self.translation_of_id) |
                models.Q(translation_of_id=self.translation_of_id)
            )
        # Return self and any translations of this post
        return Post.objects.filter(
            models.Q(id=self.id) | models.Q(translation_of_id=self.id)
        )

    def get_translation(self, language: str):
        """Get translation of this post in specified language"""
        if self.language == language:
            return self
        return self.translation_group.filter(language=language).first()

    def get_available_translations(self) -> dict:
        """Get dict of language -> post for all translations"""
        translations = {}
        for post in self.translation_group:
            translations[post.language] = post
        return translations

    def get_missing_languages(self) -> list:
        """Get list of languages without translations"""
        available = set(self.get_available_translations().keys())
        return [lang for lang in WPMLLanguage.AVAILABLE if lang not in available]


class Category(models.Model):
    """WordPress Category with WPML multilingual support"""

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

    # WPML fields
    language = models.CharField(
        _('Language'),
        max_length=10,
        choices=WPMLLanguage.get_choices(),
        default=WPMLLanguage.DEFAULT,
        db_index=True
    )
    wpml_trid = models.IntegerField(
        _('WPML Translation ID'),
        null=True,
        blank=True,
        db_index=True
    )
    translation_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='category_translations'
    )

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['name']
        indexes = [
            models.Index(fields=['language']),
            models.Index(fields=['wpml_trid']),
        ]

    def __str__(self):
        return f"{self.name} [{self.language}]"

    def get_translation(self, language: str):
        """Get translation of this category in specified language"""
        if self.language == language:
            return self
        if self.wpml_trid:
            return Category.objects.filter(wpml_trid=self.wpml_trid, language=language).first()
        return None


class Tag(models.Model):
    """WordPress Tag with WPML multilingual support"""

    wp_id = models.IntegerField(_('WordPress ID'), unique=True, null=True, blank=True)
    name = models.CharField(_('Name'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=100)

    # WPML fields
    language = models.CharField(
        _('Language'),
        max_length=10,
        choices=WPMLLanguage.get_choices(),
        default=WPMLLanguage.DEFAULT,
        db_index=True
    )
    wpml_trid = models.IntegerField(
        _('WPML Translation ID'),
        null=True,
        blank=True,
        db_index=True
    )
    translation_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tag_translations'
    )

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        ordering = ['name']
        indexes = [
            models.Index(fields=['language']),
            models.Index(fields=['wpml_trid']),
        ]

    def __str__(self):
        return f"{self.name} [{self.language}]"

    def get_translation(self, language: str):
        """Get translation of this tag in specified language"""
        if self.language == language:
            return self
        if self.wpml_trid:
            return Tag.objects.filter(wpml_trid=self.wpml_trid, language=language).first()
        return None


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
