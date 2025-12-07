"""
Celery tasks for email marketing.
"""

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_campaign(self, campaign_id: int):
    """Send a campaign to all recipients"""
    from .models import Campaign, CampaignEmail, Subscriber

    try:
        campaign = Campaign.objects.get(id=campaign_id)
        campaign.status = Campaign.CampaignStatus.SENDING
        campaign.started_at = timezone.now()
        campaign.save()

        # Get recipients
        recipients = Subscriber.objects.filter(
            status=Subscriber.SubscriberStatus.ACTIVE
        )

        # Filter by mailing lists
        if campaign.mailing_lists.exists():
            recipients = recipients.filter(lists__in=campaign.mailing_lists.all())

        # Filter by tags
        if campaign.tags.exists():
            recipients = recipients.filter(tags__in=campaign.tags.all())

        # Exclude tags
        if campaign.exclude_tags.exists():
            recipients = recipients.exclude(tags__in=campaign.exclude_tags.all())

        recipients = recipients.distinct()
        campaign.total_recipients = recipients.count()
        campaign.save()

        sent = 0
        errors = 0

        for subscriber in recipients:
            try:
                # Create campaign email record
                campaign_email, created = CampaignEmail.objects.get_or_create(
                    campaign=campaign,
                    subscriber=subscriber,
                    defaults={'status': CampaignEmail.EmailStatus.PENDING}
                )

                if not created and campaign_email.status != CampaignEmail.EmailStatus.PENDING:
                    continue

                # Send email
                result = send_single_email.delay(campaign_email.id)

                sent += 1

            except Exception as e:
                logger.error(f"Error sending to {subscriber.email}: {e}")
                errors += 1

        # Update campaign
        campaign.emails_sent = sent
        campaign.status = Campaign.CampaignStatus.SENT
        campaign.completed_at = timezone.now()
        campaign.save()

        return {
            'campaign_id': campaign_id,
            'total_recipients': campaign.total_recipients,
            'sent': sent,
            'errors': errors
        }

    except Campaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        raise


@shared_task
def send_single_email(campaign_email_id: int):
    """Send a single email"""
    from .models import CampaignEmail

    try:
        campaign_email = CampaignEmail.objects.select_related(
            'campaign', 'subscriber'
        ).get(id=campaign_email_id)

        campaign = campaign_email.campaign
        subscriber = campaign_email.subscriber

        # Personalize content
        html_content = personalize_content(
            campaign.html_content,
            subscriber
        )
        text_content = personalize_content(
            campaign.text_content,
            subscriber
        )
        subject = personalize_content(
            campaign.subject,
            subscriber
        )

        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[subscriber.email]
        )
        email.attach_alternative(html_content, "text/html")

        # Send
        email.send(fail_silently=False)

        # Update status
        campaign_email.status = CampaignEmail.EmailStatus.SENT
        campaign_email.sent_at = timezone.now()
        campaign_email.save()

        # Update subscriber stats
        subscriber.emails_sent += 1
        subscriber.save()

        return {'success': True, 'email': subscriber.email}

    except CampaignEmail.DoesNotExist:
        logger.error(f"CampaignEmail {campaign_email_id} not found")
        return {'success': False, 'error': 'Not found'}
    except Exception as e:
        logger.error(f"Error sending email {campaign_email_id}: {e}")

        # Update status to show error
        try:
            campaign_email = CampaignEmail.objects.get(id=campaign_email_id)
            campaign_email.status = CampaignEmail.EmailStatus.BOUNCED
            campaign_email.error_message = str(e)
            campaign_email.save()
        except:
            pass

        return {'success': False, 'error': str(e)}


def personalize_content(content: str, subscriber) -> str:
    """Replace personalization tags in content"""
    if not content:
        return content

    replacements = {
        '{{email}}': subscriber.email,
        '{{first_name}}': subscriber.first_name or 'Kunde',
        '{{last_name}}': subscriber.last_name or '',
        '{{full_name}}': subscriber.full_name,
        '{{company}}': subscriber.company or '',
    }

    for tag, value in replacements.items():
        content = content.replace(tag, value)

    return content


@shared_task
def process_automation_trigger(workflow_id: int, subscriber_id: int):
    """Process automation workflow for a subscriber"""
    from .models import AutomationWorkflow, AutomationStep, Subscriber

    try:
        workflow = AutomationWorkflow.objects.get(id=workflow_id, is_active=True)
        subscriber = Subscriber.objects.get(id=subscriber_id)

        steps = workflow.steps.order_by('order')

        for step in steps:
            if step.step_type == AutomationStep.StepType.SEND_EMAIL:
                # Queue email
                if step.template:
                    send_automation_email.delay(step.id, subscriber.id)

            elif step.step_type == AutomationStep.StepType.WAIT:
                # Schedule next step
                wait_days = step.config.get('days', 1)
                # In production, use Celery's eta parameter
                pass

            elif step.step_type == AutomationStep.StepType.ADD_TAG:
                tag_id = step.config.get('tag_id')
                if tag_id:
                    subscriber.tags.add(tag_id)

            elif step.step_type == AutomationStep.StepType.REMOVE_TAG:
                tag_id = step.config.get('tag_id')
                if tag_id:
                    subscriber.tags.remove(tag_id)

        workflow.total_triggered += 1
        workflow.save()

        return {'workflow_id': workflow_id, 'subscriber_id': subscriber_id}

    except (AutomationWorkflow.DoesNotExist, Subscriber.DoesNotExist) as e:
        logger.error(f"Automation error: {e}")
        raise


@shared_task
def send_automation_email(step_id: int, subscriber_id: int):
    """Send an automation email"""
    from .models import AutomationStep, Subscriber

    try:
        step = AutomationStep.objects.get(id=step_id)
        subscriber = Subscriber.objects.get(id=subscriber_id)
        template = step.template

        if not template:
            return {'error': 'No template configured'}

        html_content = personalize_content(template.html_content, subscriber)
        text_content = personalize_content(template.text_content, subscriber)
        subject = personalize_content(template.subject, subscriber)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[subscriber.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

        subscriber.emails_sent += 1
        subscriber.save()

        return {'success': True, 'email': subscriber.email}

    except Exception as e:
        logger.error(f"Automation email error: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def sync_mailpoet_subscribers():
    """Sync subscribers from MailPoet (WordPress)"""
    from .models import Subscriber, MailingList
    import requests
    from requests.auth import HTTPBasicAuth

    try:
        site_url = settings.WP_SITE_URL.rstrip('/')
        auth = HTTPBasicAuth(settings.WP_USERNAME, settings.WP_APP_PASSWORD)
        headers = {'User-Agent': 'Mozilla/5.0'}

        # Get MailPoet subscribers via REST API
        url = f"{site_url}/?rest_route=/mailpoet/v1/subscribers"
        response = requests.get(url, auth=auth, headers=headers, timeout=30)

        if response.status_code != 200:
            logger.warning("MailPoet API not available")
            return {'error': 'MailPoet API not available'}

        subscribers_data = response.json()
        synced = 0

        for item in subscribers_data:
            Subscriber.objects.update_or_create(
                email=item.get('email', '').lower(),
                defaults={
                    'first_name': item.get('first_name', ''),
                    'last_name': item.get('last_name', ''),
                    'status': Subscriber.SubscriberStatus.ACTIVE,
                    'source': 'mailpoet',
                }
            )
            synced += 1

        return {'synced': synced}

    except Exception as e:
        logger.error(f"MailPoet sync failed: {e}")
        return {'error': str(e)}
