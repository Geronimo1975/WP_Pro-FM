"""
Email Marketing models for newsletters, campaigns, and subscriber management.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Subscriber(models.Model):
    """Email subscriber"""

    class SubscriberStatus(models.TextChoices):
        PENDING = 'pending', _('Pending Confirmation')
        ACTIVE = 'active', _('Active')
        UNSUBSCRIBED = 'unsubscribed', _('Unsubscribed')
        BOUNCED = 'bounced', _('Bounced')
        COMPLAINED = 'complained', _('Complained')

    email = models.EmailField(_('Email'), unique=True)
    first_name = models.CharField(_('First Name'), max_length=100, blank=True)
    last_name = models.CharField(_('Last Name'), max_length=100, blank=True)
    company = models.CharField(_('Company'), max_length=200, blank=True)

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=SubscriberStatus.choices,
        default=SubscriberStatus.PENDING
    )

    # Preferences
    language = models.CharField(_('Language'), max_length=10, default='de')
    lists = models.ManyToManyField('MailingList', related_name='subscribers', blank=True)
    tags = models.ManyToManyField('SubscriberTag', related_name='subscribers', blank=True)

    # Source tracking
    source = models.CharField(_('Source'), max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)

    # Double opt-in
    confirmation_token = models.CharField(_('Confirmation Token'), max_length=100, blank=True)
    confirmed_at = models.DateTimeField(_('Confirmed At'), null=True, blank=True)

    # Engagement metrics
    emails_sent = models.IntegerField(_('Emails Sent'), default=0)
    emails_opened = models.IntegerField(_('Emails Opened'), default=0)
    emails_clicked = models.IntegerField(_('Emails Clicked'), default=0)
    last_opened = models.DateTimeField(_('Last Opened'), null=True, blank=True)
    last_clicked = models.DateTimeField(_('Last Clicked'), null=True, blank=True)

    # Timestamps
    subscribed_at = models.DateTimeField(_('Subscribed At'), auto_now_add=True)
    unsubscribed_at = models.DateTimeField(_('Unsubscribed At'), null=True, blank=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Subscriber')
        verbose_name_plural = _('Subscribers')
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def open_rate(self):
        if self.emails_sent > 0:
            return round((self.emails_opened / self.emails_sent) * 100, 2)
        return 0

    @property
    def click_rate(self):
        if self.emails_sent > 0:
            return round((self.emails_clicked / self.emails_sent) * 100, 2)
        return 0


class SubscriberTag(models.Model):
    """Tags for subscriber segmentation"""

    name = models.CharField(_('Name'), max_length=50, unique=True)
    color = models.CharField(_('Color'), max_length=7, default='#3498db')
    description = models.TextField(_('Description'), blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Subscriber Tag')
        verbose_name_plural = _('Subscriber Tags')
        ordering = ['name']

    def __str__(self):
        return self.name


class MailingList(models.Model):
    """Mailing list for organizing subscribers"""

    name = models.CharField(_('Name'), max_length=100)
    slug = models.SlugField(_('Slug'), unique=True)
    description = models.TextField(_('Description'), blank=True)
    is_public = models.BooleanField(_('Is Public'), default=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Mailing List')
        verbose_name_plural = _('Mailing Lists')
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def subscriber_count(self):
        return self.subscribers.filter(status=Subscriber.SubscriberStatus.ACTIVE).count()


class EmailTemplate(models.Model):
    """Email template for campaigns"""

    class TemplateType(models.TextChoices):
        NEWSLETTER = 'newsletter', _('Newsletter')
        PROMOTIONAL = 'promotional', _('Promotional')
        TRANSACTIONAL = 'transactional', _('Transactional')
        WELCOME = 'welcome', _('Welcome')
        FOLLOW_UP = 'follow_up', _('Follow Up')

    name = models.CharField(_('Name'), max_length=100)
    template_type = models.CharField(
        _('Type'),
        max_length=20,
        choices=TemplateType.choices,
        default=TemplateType.NEWSLETTER
    )
    subject = models.CharField(_('Subject'), max_length=255)
    preview_text = models.CharField(_('Preview Text'), max_length=255, blank=True)
    html_content = models.TextField(_('HTML Content'))
    text_content = models.TextField(_('Plain Text Content'), blank=True)

    # AI generation
    is_ai_generated = models.BooleanField(_('AI Generated'), default=False)

    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Email Template')
        verbose_name_plural = _('Email Templates')
        ordering = ['-updated_at']

    def __str__(self):
        return self.name


class Campaign(models.Model):
    """Email campaign"""

    class CampaignStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        SCHEDULED = 'scheduled', _('Scheduled')
        SENDING = 'sending', _('Sending')
        SENT = 'sent', _('Sent')
        PAUSED = 'paused', _('Paused')
        CANCELLED = 'cancelled', _('Cancelled')

    name = models.CharField(_('Name'), max_length=100)
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='campaigns'
    )

    # Content (can override template)
    subject = models.CharField(_('Subject'), max_length=255)
    preview_text = models.CharField(_('Preview Text'), max_length=255, blank=True)
    html_content = models.TextField(_('HTML Content'))
    text_content = models.TextField(_('Plain Text Content'), blank=True)

    # Recipients
    mailing_lists = models.ManyToManyField(MailingList, related_name='campaigns', blank=True)
    tags = models.ManyToManyField(SubscriberTag, related_name='campaigns', blank=True)
    exclude_tags = models.ManyToManyField(
        SubscriberTag,
        related_name='excluded_campaigns',
        blank=True
    )

    # Status and scheduling
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=CampaignStatus.choices,
        default=CampaignStatus.DRAFT
    )
    scheduled_at = models.DateTimeField(_('Scheduled At'), null=True, blank=True)
    started_at = models.DateTimeField(_('Started At'), null=True, blank=True)
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)

    # Metrics
    total_recipients = models.IntegerField(_('Total Recipients'), default=0)
    emails_sent = models.IntegerField(_('Emails Sent'), default=0)
    emails_delivered = models.IntegerField(_('Emails Delivered'), default=0)
    emails_opened = models.IntegerField(_('Emails Opened'), default=0)
    unique_opens = models.IntegerField(_('Unique Opens'), default=0)
    emails_clicked = models.IntegerField(_('Emails Clicked'), default=0)
    unique_clicks = models.IntegerField(_('Unique Clicks'), default=0)
    bounces = models.IntegerField(_('Bounces'), default=0)
    unsubscribes = models.IntegerField(_('Unsubscribes'), default=0)
    complaints = models.IntegerField(_('Complaints'), default=0)

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Campaign')
        verbose_name_plural = _('Campaigns')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def open_rate(self):
        if self.emails_delivered > 0:
            return round((self.unique_opens / self.emails_delivered) * 100, 2)
        return 0

    @property
    def click_rate(self):
        if self.emails_delivered > 0:
            return round((self.unique_clicks / self.emails_delivered) * 100, 2)
        return 0

    @property
    def bounce_rate(self):
        if self.emails_sent > 0:
            return round((self.bounces / self.emails_sent) * 100, 2)
        return 0


class CampaignEmail(models.Model):
    """Individual email sent as part of a campaign"""

    class EmailStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        SENT = 'sent', _('Sent')
        DELIVERED = 'delivered', _('Delivered')
        OPENED = 'opened', _('Opened')
        CLICKED = 'clicked', _('Clicked')
        BOUNCED = 'bounced', _('Bounced')
        COMPLAINED = 'complained', _('Complained')

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='emails'
    )
    subscriber = models.ForeignKey(
        Subscriber,
        on_delete=models.CASCADE,
        related_name='campaign_emails'
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=EmailStatus.choices,
        default=EmailStatus.PENDING
    )

    # Tracking
    sent_at = models.DateTimeField(_('Sent At'), null=True, blank=True)
    delivered_at = models.DateTimeField(_('Delivered At'), null=True, blank=True)
    opened_at = models.DateTimeField(_('Opened At'), null=True, blank=True)
    clicked_at = models.DateTimeField(_('Clicked At'), null=True, blank=True)
    open_count = models.IntegerField(_('Open Count'), default=0)
    click_count = models.IntegerField(_('Click Count'), default=0)

    # Error tracking
    bounce_type = models.CharField(_('Bounce Type'), max_length=50, blank=True)
    error_message = models.TextField(_('Error Message'), blank=True)

    class Meta:
        verbose_name = _('Campaign Email')
        verbose_name_plural = _('Campaign Emails')
        unique_together = ['campaign', 'subscriber']
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['subscriber', 'sent_at']),
        ]

    def __str__(self):
        return f"{self.campaign.name} -> {self.subscriber.email}"


class AutomationWorkflow(models.Model):
    """Email automation workflow"""

    class TriggerType(models.TextChoices):
        SUBSCRIPTION = 'subscription', _('New Subscription')
        TAG_ADDED = 'tag_added', _('Tag Added')
        DATE = 'date', _('Date Based')
        BEHAVIOR = 'behavior', _('Behavior Based')

    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    trigger_type = models.CharField(
        _('Trigger Type'),
        max_length=20,
        choices=TriggerType.choices
    )
    trigger_config = models.JSONField(_('Trigger Configuration'), default=dict)
    is_active = models.BooleanField(_('Is Active'), default=False)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    # Metrics
    total_triggered = models.IntegerField(_('Total Triggered'), default=0)
    total_completed = models.IntegerField(_('Total Completed'), default=0)

    class Meta:
        verbose_name = _('Automation Workflow')
        verbose_name_plural = _('Automation Workflows')
        ordering = ['name']

    def __str__(self):
        return self.name


class AutomationStep(models.Model):
    """Step in an automation workflow"""

    class StepType(models.TextChoices):
        SEND_EMAIL = 'send_email', _('Send Email')
        WAIT = 'wait', _('Wait')
        CONDITION = 'condition', _('Condition')
        ADD_TAG = 'add_tag', _('Add Tag')
        REMOVE_TAG = 'remove_tag', _('Remove Tag')

    workflow = models.ForeignKey(
        AutomationWorkflow,
        on_delete=models.CASCADE,
        related_name='steps'
    )
    step_type = models.CharField(
        _('Step Type'),
        max_length=20,
        choices=StepType.choices
    )
    order = models.IntegerField(_('Order'), default=0)
    config = models.JSONField(_('Configuration'), default=dict)

    # For email steps
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='automation_steps'
    )

    class Meta:
        verbose_name = _('Automation Step')
        verbose_name_plural = _('Automation Steps')
        ordering = ['workflow', 'order']

    def __str__(self):
        return f"{self.workflow.name} - Step {self.order}"
