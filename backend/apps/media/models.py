"""
Media models for WordPress media management.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class MediaFile(models.Model):
    """WordPress media file synchronized from WP"""

    class MediaType(models.TextChoices):
        IMAGE = 'image', _('Image')
        VIDEO = 'video', _('Video')
        AUDIO = 'audio', _('Audio')
        DOCUMENT = 'document', _('Document')
        OTHER = 'other', _('Other')

    # WordPress sync fields
    wp_id = models.IntegerField(_('WordPress ID'), unique=True, null=True, blank=True)
    wp_url = models.URLField(_('WordPress URL'), max_length=500, blank=True)

    # File info
    title = models.CharField(_('Title'), max_length=255)
    filename = models.CharField(_('Filename'), max_length=255)
    file = models.FileField(_('Local File'), upload_to='wp_media/%Y/%m/', blank=True)
    mime_type = models.CharField(_('MIME Type'), max_length=100, blank=True)
    media_type = models.CharField(
        _('Media Type'),
        max_length=20,
        choices=MediaType.choices,
        default=MediaType.IMAGE
    )
    file_size = models.BigIntegerField(_('File Size (bytes)'), default=0)

    # Metadata
    alt_text = models.CharField(_('Alt Text'), max_length=255, blank=True)
    caption = models.TextField(_('Caption'), blank=True)
    description = models.TextField(_('Description'), blank=True)

    # Image dimensions
    width = models.IntegerField(_('Width'), null=True, blank=True)
    height = models.IntegerField(_('Height'), null=True, blank=True)

    # Timestamps
    wp_created_at = models.DateTimeField(_('WP Created At'), null=True, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    synced_at = models.DateTimeField(_('Last Synced'), null=True, blank=True)

    # Status
    is_synced = models.BooleanField(_('Is Synced'), default=False)
    is_local = models.BooleanField(_('Local Copy Exists'), default=False)

    class Meta:
        verbose_name = _('Media File')
        verbose_name_plural = _('Media Files')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wp_id']),
            models.Index(fields=['media_type']),
            models.Index(fields=['filename']),
        ]

    def __str__(self):
        return self.title or self.filename

    def save(self, *args, **kwargs):
        # Track if file changed
        if self.pk:
            try:
                old = MediaFile.objects.get(pk=self.pk)
                if old.file != self.file and self.file:
                    # New file uploaded - mark as needing sync
                    self.is_local = True
                    self.is_synced = False
            except MediaFile.DoesNotExist:
                pass

        # Set is_local if file exists
        if self.file:
            self.is_local = True

        # Update file_size if file exists
        if self.file and hasattr(self.file, 'size'):
            try:
                self.file_size = self.file.size
            except:
                pass

        super().save(*args, **kwargs)

    @property
    def is_image(self):
        return self.media_type == self.MediaType.IMAGE

    @property
    def file_size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0


class MediaCollection(models.Model):
    """Collection/folder for organizing media"""

    name = models.CharField(_('Name'), max_length=100)
    slug = models.SlugField(_('Slug'), unique=True)
    description = models.TextField(_('Description'), blank=True)
    media_files = models.ManyToManyField(
        MediaFile,
        related_name='collections',
        blank=True
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Media Collection')
        verbose_name_plural = _('Media Collections')
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def file_count(self):
        return self.media_files.count()


class MediaSyncLog(models.Model):
    """Log of media sync operations"""

    class SyncStatus(models.TextChoices):
        STARTED = 'started', _('Started')
        SUCCESS = 'success', _('Success')
        FAILED = 'failed', _('Failed')
        PARTIAL = 'partial', _('Partial')

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
        verbose_name = _('Media Sync Log')
        verbose_name_plural = _('Media Sync Logs')
        ordering = ['-started_at']

    def __str__(self):
        return f"Sync {self.started_at.strftime('%Y-%m-%d %H:%M')} - {self.status}"
