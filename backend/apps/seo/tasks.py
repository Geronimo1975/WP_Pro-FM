"""
Celery tasks for SEO management.
"""

from celery import shared_task
from django.conf import settings
from django.utils import timezone
import requests
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def check_keyword_rankings(self):
    """Check rankings for all tracked keywords"""
    from .models import Keyword, KeywordRankingHistory

    tracked_keywords = Keyword.objects.filter(is_tracked=True)
    results = {'checked': 0, 'updated': 0, 'errors': 0}

    for keyword in tracked_keywords:
        try:
            # Note: In production, integrate with DataForSEO or similar API
            # This is a placeholder implementation
            logger.info(f"Checking ranking for: {keyword.keyword}")

            # Store history
            if keyword.current_position:
                KeywordRankingHistory.objects.create(
                    keyword=keyword,
                    position=keyword.current_position,
                    url=keyword.ranking_url
                )

            keyword.last_checked = timezone.now()
            keyword.save()
            results['checked'] += 1

        except Exception as e:
            logger.error(f"Error checking keyword {keyword.keyword}: {e}")
            results['errors'] += 1

    return results


@shared_task(bind=True)
def run_site_audit(self, audit_id: int):
    """Run SEO site audit"""
    from .models import SiteAudit, SiteAuditIssue

    try:
        audit = SiteAudit.objects.get(id=audit_id)
        audit.status = SiteAudit.AuditStatus.RUNNING
        audit.save()

        # Basic audit checks (placeholder - integrate with real tools)
        issues_found = []

        # Check robots.txt
        try:
            robots_url = f"{audit.site_url.rstrip('/')}/robots.txt"
            response = requests.get(robots_url, timeout=10)
            if response.status_code != 200:
                issues_found.append({
                    'severity': 'warning',
                    'category': 'indexability',
                    'title': 'robots.txt not found',
                    'description': 'No robots.txt file found at the root of your site.',
                    'recommendation': 'Create a robots.txt file to guide search engine crawlers.'
                })
        except Exception as e:
            logger.warning(f"Could not check robots.txt: {e}")

        # Check sitemap
        try:
            sitemap_url = f"{audit.site_url.rstrip('/')}/sitemap.xml"
            response = requests.get(sitemap_url, timeout=10)
            if response.status_code != 200:
                issues_found.append({
                    'severity': 'warning',
                    'category': 'indexability',
                    'title': 'sitemap.xml not found',
                    'description': 'No sitemap.xml found at the root of your site.',
                    'recommendation': 'Generate and submit a sitemap to help search engines discover your pages.'
                })
        except Exception as e:
            logger.warning(f"Could not check sitemap: {e}")

        # Check HTTPS
        if not audit.site_url.startswith('https://'):
            issues_found.append({
                'severity': 'error',
                'category': 'security',
                'title': 'Site not using HTTPS',
                'description': 'Your site is not using HTTPS encryption.',
                'recommendation': 'Install an SSL certificate and redirect all HTTP traffic to HTTPS.'
            })

        # Create issue records
        errors = warnings = notices = 0
        for issue_data in issues_found:
            SiteAuditIssue.objects.create(
                audit=audit,
                **issue_data
            )
            if issue_data['severity'] == 'error':
                errors += 1
            elif issue_data['severity'] == 'warning':
                warnings += 1
            else:
                notices += 1

        # Calculate scores (simplified)
        audit.errors_count = errors
        audit.warnings_count = warnings
        audit.notices_count = notices
        audit.overall_score = max(0, 100 - (errors * 10) - (warnings * 5) - notices)
        audit.seo_score = audit.overall_score
        audit.status = SiteAudit.AuditStatus.COMPLETED
        audit.completed_at = timezone.now()
        audit.save()

        return {
            'audit_id': audit.id,
            'score': audit.overall_score,
            'issues': len(issues_found)
        }

    except SiteAudit.DoesNotExist:
        logger.error(f"Audit {audit_id} not found")
        raise
    except Exception as e:
        if audit:
            audit.status = SiteAudit.AuditStatus.FAILED
            audit.save()
        logger.error(f"Audit failed: {e}")
        raise


@shared_task(bind=True)
def submit_to_indexnow(self, urls: list):
    """Submit URLs to IndexNow"""
    from .models import IndexNowSubmission

    api_key = getattr(settings, 'INDEXNOW_API_KEY', '')
    if not api_key:
        logger.error("INDEXNOW_API_KEY not configured")
        return {'error': 'API key not configured'}

    site_url = settings.WP_SITE_URL.rstrip('/')
    host = site_url.replace('https://', '').replace('http://', '')

    results = {'submitted': 0, 'failed': 0}

    # Create submission records
    submissions = []
    for url in urls:
        submission = IndexNowSubmission.objects.create(
            url=url,
            status=IndexNowSubmission.SubmissionStatus.PENDING
        )
        submissions.append(submission)

    # Submit to IndexNow API
    try:
        payload = {
            'host': host,
            'key': api_key,
            'keyLocation': f"{site_url}/{api_key}.txt",
            'urlList': urls[:10000]  # Max 10000 per request
        }

        response = requests.post(
            'https://api.indexnow.org/indexnow',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        # Update submission records
        for submission in submissions:
            submission.response_code = response.status_code
            submission.submitted_at = timezone.now()

            if response.status_code in [200, 202]:
                submission.status = IndexNowSubmission.SubmissionStatus.ACCEPTED
                results['submitted'] += 1
            else:
                submission.status = IndexNowSubmission.SubmissionStatus.REJECTED
                results['failed'] += 1

            submission.save()

    except Exception as e:
        logger.error(f"IndexNow submission failed: {e}")
        for submission in submissions:
            submission.status = IndexNowSubmission.SubmissionStatus.REJECTED
            submission.save()
        results['failed'] = len(submissions)

    return results


@shared_task
def update_keyword_metrics(keyword_id: int):
    """Update keyword metrics from DataForSEO"""
    from .models import Keyword

    try:
        keyword = Keyword.objects.get(id=keyword_id)

        # Placeholder for DataForSEO integration
        # In production, call DataForSEO API here

        keyword.last_checked = timezone.now()
        keyword.save()

        return {'keyword': keyword.keyword, 'updated': True}

    except Keyword.DoesNotExist:
        return {'error': 'Keyword not found'}
