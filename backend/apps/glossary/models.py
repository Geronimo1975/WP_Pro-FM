"""
Glossary models for Pro-FM Facility Management terminology.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
import re


class GlossaryCategory(models.Model):
    """Categories for organizing glossary terms"""

    name = models.CharField(_('Name'), max_length=100, unique=True)
    slug = models.SlugField(_('Slug'), max_length=100, unique=True)
    description = models.TextField(_('Description'), blank=True)
    icon_class = models.CharField(_('Icon Class'), max_length=50, blank=True,
                                   help_text=_('FontAwesome or Material icon class'))
    order = models.IntegerField(_('Order'), default=0)
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Glossary Category')
        verbose_name_plural = _('Glossary Categories')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.create_slug(self.name)
        super().save(*args, **kwargs)

    @staticmethod
    def create_slug(text):
        """Create URL-safe slug from German text"""
        slug = text.lower()
        slug = slug.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        return slug.strip('-')


class GlossaryTerm(models.Model):
    """Glossary term for Facility Management terminology"""

    # Core fields
    term = models.CharField(_('Term'), max_length=200, unique=True)
    slug = models.SlugField(_('Slug'), max_length=200, unique=True)
    letter = models.CharField(_('Letter'), max_length=1, db_index=True)

    # Content
    definition = models.TextField(_('Definition'),
                                   help_text=_('Ausführliche Definition (min. 200 Zeichen)'))
    examples = models.TextField(_('Examples'), blank=True,
                                 help_text=_('Praktische Beispiele aus dem FM-Alltag'))
    synonyms = models.CharField(_('Synonyms'), max_length=500, blank=True)
    related_terms = models.CharField(_('Related Terms'), max_length=500, blank=True)

    # Classification
    category = models.ForeignKey(
        GlossaryCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='terms',
        verbose_name=_('Category')
    )

    # SEO
    meta_title = models.CharField(_('Meta Title'), max_length=100, blank=True)
    meta_description = models.CharField(_('Meta Description'), max_length=200, blank=True)
    search_volume = models.IntegerField(_('Search Volume'), default=100,
                                         help_text=_('Geschätztes monatliches Suchvolumen'))
    priority = models.IntegerField(_('Priority'), default=3,
                                    help_text=_('1=highest, 5=lowest'))

    # WordPress sync
    wp_post_id = models.IntegerField(_('WordPress Post ID'), null=True, blank=True)
    is_published = models.BooleanField(_('Published to WordPress'), default=False)
    published_at = models.DateTimeField(_('Published At'), null=True, blank=True)

    # Status
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Glossary Term')
        verbose_name_plural = _('Glossary Terms')
        ordering = ['letter', 'term']
        indexes = [
            models.Index(fields=['letter']),
            models.Index(fields=['category']),
            models.Index(fields=['is_published']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.term

    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug:
            self.slug = GlossaryCategory.create_slug(self.term)

        # Auto-set letter
        if self.term:
            self.letter = self.term[0].upper()

        # Auto-generate meta title
        if not self.meta_title:
            self.meta_title = f"{self.term} | Pro-FM Glossar"

        # Auto-generate meta description
        if not self.meta_description and self.definition:
            self.meta_description = self.definition[:160] if len(self.definition) <= 160 else self.definition[:157] + '...'

        super().save(*args, **kwargs)

    @property
    def definition_preview(self):
        """Return first 200 characters of definition"""
        if self.definition:
            return self.definition[:200] + '...' if len(self.definition) > 200 else self.definition
        return ''

    @property
    def wp_url(self):
        """Get WordPress URL for this term"""
        if self.is_published:
            from django.conf import settings
            return f"{settings.WP_SITE_URL}/{self.slug}/"
        return None


class GlossarySyncLog(models.Model):
    """Log of glossary sync operations to WordPress"""

    class SyncStatus(models.TextChoices):
        STARTED = 'started', _('Started')
        SUCCESS = 'success', _('Success')
        FAILED = 'failed', _('Failed')
        PARTIAL = 'partial', _('Partial')

    class SyncType(models.TextChoices):
        FULL = 'full', _('Full Sync')
        LETTER = 'letter', _('Letter Sync')
        TERM = 'term', _('Term Sync')
        CATEGORY = 'category', _('Category Sync')

    sync_type = models.CharField(
        _('Sync Type'),
        max_length=20,
        choices=SyncType.choices,
        default=SyncType.FULL
    )
    started_at = models.DateTimeField(_('Started At'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=SyncStatus.choices,
        default=SyncStatus.STARTED
    )
    total_items = models.IntegerField(_('Total Items'), default=0)
    synced_items = models.IntegerField(_('Synced Items'), default=0)
    failed_items = models.IntegerField(_('Failed Items'), default=0)
    error_message = models.TextField(_('Error Message'), blank=True)

    class Meta:
        verbose_name = _('Glossary Sync Log')
        verbose_name_plural = _('Glossary Sync Logs')
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.sync_type} - {self.started_at.strftime('%Y-%m-%d %H:%M')} - {self.status}"
