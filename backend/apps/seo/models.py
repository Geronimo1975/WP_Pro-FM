"""
SEO models for keyword tracking, analysis, and optimization.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Keyword(models.Model):
    """Target keywords for SEO optimization"""

    class KeywordDifficulty(models.TextChoices):
        EASY = 'easy', _('Easy (0-30)')
        MEDIUM = 'medium', _('Medium (31-60)')
        HARD = 'hard', _('Hard (61-80)')
        VERY_HARD = 'very_hard', _('Very Hard (81-100)')

    keyword = models.CharField(_('Keyword'), max_length=255)
    language = models.CharField(_('Language'), max_length=10, default='de')

    # Search metrics
    search_volume = models.IntegerField(_('Monthly Search Volume'), null=True, blank=True)
    difficulty_score = models.IntegerField(_('Difficulty Score'), null=True, blank=True)
    difficulty = models.CharField(
        _('Difficulty Level'),
        max_length=20,
        choices=KeywordDifficulty.choices,
        blank=True
    )
    cpc = models.DecimalField(_('CPC (EUR)'), max_digits=10, decimal_places=2, null=True, blank=True)
    competition = models.DecimalField(_('Competition'), max_digits=3, decimal_places=2, null=True, blank=True)

    # Ranking
    current_position = models.IntegerField(_('Current Position'), null=True, blank=True)
    previous_position = models.IntegerField(_('Previous Position'), null=True, blank=True)
    best_position = models.IntegerField(_('Best Position'), null=True, blank=True)
    ranking_url = models.URLField(_('Ranking URL'), max_length=500, blank=True)

    # Tracking
    is_primary = models.BooleanField(_('Primary Keyword'), default=False)
    is_tracked = models.BooleanField(_('Is Tracked'), default=True)
    target_position = models.IntegerField(_('Target Position'), default=10)

    # Related content
    posts = models.ManyToManyField(
        'content.Post',
        related_name='target_keywords',
        blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    last_checked = models.DateTimeField(_('Last Checked'), null=True, blank=True)

    class Meta:
        verbose_name = _('Keyword')
        verbose_name_plural = _('Keywords')
        ordering = ['-search_volume', 'keyword']
        unique_together = ['keyword', 'language']
        indexes = [
            models.Index(fields=['keyword']),
            models.Index(fields=['language', 'is_tracked']),
        ]

    def __str__(self):
        return f"{self.keyword} ({self.language})"

    @property
    def position_change(self):
        if self.current_position and self.previous_position:
            return self.previous_position - self.current_position
        return 0


class KeywordRankingHistory(models.Model):
    """Historical ranking data for keywords"""

    keyword = models.ForeignKey(
        Keyword,
        on_delete=models.CASCADE,
        related_name='ranking_history'
    )
    position = models.IntegerField(_('Position'))
    url = models.URLField(_('URL'), max_length=500, blank=True)
    checked_at = models.DateTimeField(_('Checked At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Keyword Ranking History')
        verbose_name_plural = _('Keyword Ranking History')
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['keyword', 'checked_at']),
        ]

    def __str__(self):
        return f"{self.keyword.keyword}: #{self.position} ({self.checked_at.date()})"


class SiteAudit(models.Model):
    """SEO site audit results"""

    class AuditStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        RUNNING = 'running', _('Running')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')

    site_url = models.URLField(_('Site URL'))
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=AuditStatus.choices,
        default=AuditStatus.PENDING
    )

    # Scores
    overall_score = models.IntegerField(_('Overall Score'), null=True, blank=True)
    performance_score = models.IntegerField(_('Performance Score'), null=True, blank=True)
    seo_score = models.IntegerField(_('SEO Score'), null=True, blank=True)
    accessibility_score = models.IntegerField(_('Accessibility Score'), null=True, blank=True)

    # Issues count
    errors_count = models.IntegerField(_('Errors'), default=0)
    warnings_count = models.IntegerField(_('Warnings'), default=0)
    notices_count = models.IntegerField(_('Notices'), default=0)

    # Raw data
    audit_data = models.JSONField(_('Audit Data'), default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)

    class Meta:
        verbose_name = _('Site Audit')
        verbose_name_plural = _('Site Audits')
        ordering = ['-created_at']

    def __str__(self):
        return f"Audit {self.site_url} - {self.created_at.date()}"


class SiteAuditIssue(models.Model):
    """Individual issues found in site audit"""

    class IssueSeverity(models.TextChoices):
        ERROR = 'error', _('Error')
        WARNING = 'warning', _('Warning')
        NOTICE = 'notice', _('Notice')

    class IssueCategory(models.TextChoices):
        INDEXABILITY = 'indexability', _('Indexability')
        CONTENT = 'content', _('Content')
        LINKS = 'links', _('Links')
        IMAGES = 'images', _('Images')
        PERFORMANCE = 'performance', _('Performance')
        MOBILE = 'mobile', _('Mobile')
        SECURITY = 'security', _('Security')
        OTHER = 'other', _('Other')

    audit = models.ForeignKey(
        SiteAudit,
        on_delete=models.CASCADE,
        related_name='issues'
    )
    severity = models.CharField(
        _('Severity'),
        max_length=20,
        choices=IssueSeverity.choices
    )
    category = models.CharField(
        _('Category'),
        max_length=20,
        choices=IssueCategory.choices,
        default=IssueCategory.OTHER
    )
    title = models.CharField(_('Title'), max_length=255)
    description = models.TextField(_('Description'))
    url = models.URLField(_('Affected URL'), max_length=500, blank=True)
    recommendation = models.TextField(_('Recommendation'), blank=True)
    is_resolved = models.BooleanField(_('Is Resolved'), default=False)

    class Meta:
        verbose_name = _('Audit Issue')
        verbose_name_plural = _('Audit Issues')
        ordering = ['severity', 'category']

    def __str__(self):
        return f"[{self.severity}] {self.title}"


class Backlink(models.Model):
    """Backlink tracking"""

    source_url = models.URLField(_('Source URL'), max_length=500)
    source_domain = models.CharField(_('Source Domain'), max_length=255)
    target_url = models.URLField(_('Target URL'), max_length=500)
    anchor_text = models.CharField(_('Anchor Text'), max_length=255, blank=True)

    # Metrics
    domain_authority = models.IntegerField(_('Domain Authority'), null=True, blank=True)
    is_dofollow = models.BooleanField(_('Is DoFollow'), default=True)
    is_active = models.BooleanField(_('Is Active'), default=True)

    # Timestamps
    first_seen = models.DateTimeField(_('First Seen'), auto_now_add=True)
    last_checked = models.DateTimeField(_('Last Checked'), null=True, blank=True)

    class Meta:
        verbose_name = _('Backlink')
        verbose_name_plural = _('Backlinks')
        ordering = ['-domain_authority', '-first_seen']
        unique_together = ['source_url', 'target_url']

    def __str__(self):
        return f"{self.source_domain} -> {self.target_url}"


class IndexNowSubmission(models.Model):
    """IndexNow URL submission tracking"""

    class SubmissionStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        SUBMITTED = 'submitted', _('Submitted')
        ACCEPTED = 'accepted', _('Accepted')
        REJECTED = 'rejected', _('Rejected')

    url = models.URLField(_('URL'), max_length=500)
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.PENDING
    )
    search_engine = models.CharField(_('Search Engine'), max_length=50, default='indexnow')
    response_code = models.IntegerField(_('Response Code'), null=True, blank=True)
    submitted_at = models.DateTimeField(_('Submitted At'), null=True, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('IndexNow Submission')
        verbose_name_plural = _('IndexNow Submissions')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.url} - {self.status}"
