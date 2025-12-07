"""
Celery tasks for media management.
"""

from celery import shared_task
from django.conf import settings
from django.utils import timezone
import requests
from requests.auth import HTTPBasicAuth
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def sync_wordpress_media(self):
    """Sync all media from WordPress"""
    from .models import MediaFile, MediaSyncLog

    log = MediaSyncLog.objects.create(status=MediaSyncLog.SyncStatus.STARTED)

    try:
        site_url = settings.WP_SITE_URL.rstrip('/')
        auth = HTTPBasicAuth(settings.WP_USERNAME, settings.WP_APP_PASSWORD)
        headers = {'User-Agent': 'Mozilla/5.0'}

        all_media = []
        page = 1
        per_page = 100

        # Fetch all media from WordPress
        while True:
            url = f"{site_url}/?rest_route=/wp/v2/media&per_page={per_page}&page={page}"
            response = requests.get(url, auth=auth, headers=headers, timeout=30)

            if response.status_code != 200:
                break

            media = response.json()
            if not media:
                break

            all_media.extend(media)
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))

            if page >= total_pages:
                break
            page += 1

        log.total_items = len(all_media)
        synced = 0
        failed = 0

        # Process each media item
        for item in all_media:
            try:
                wp_id = item.get('id')
                source_url = item.get('source_url', '')
                mime_type = item.get('mime_type', '')

                # Determine media type
                if mime_type.startswith('image/'):
                    media_type = MediaFile.MediaType.IMAGE
                elif mime_type.startswith('video/'):
                    media_type = MediaFile.MediaType.VIDEO
                elif mime_type.startswith('audio/'):
                    media_type = MediaFile.MediaType.AUDIO
                elif mime_type in ['application/pdf', 'application/msword']:
                    media_type = MediaFile.MediaType.DOCUMENT
                else:
                    media_type = MediaFile.MediaType.OTHER

                # Get dimensions
                media_details = item.get('media_details', {})
                width = media_details.get('width')
                height = media_details.get('height')
                file_size = media_details.get('filesize', 0)

                # Update or create
                MediaFile.objects.update_or_create(
                    wp_id=wp_id,
                    defaults={
                        'wp_url': source_url,
                        'title': item.get('title', {}).get('rendered', ''),
                        'filename': source_url.split('/')[-1] if source_url else '',
                        'mime_type': mime_type,
                        'media_type': media_type,
                        'alt_text': item.get('alt_text', ''),
                        'caption': item.get('caption', {}).get('rendered', ''),
                        'description': item.get('description', {}).get('rendered', ''),
                        'width': width,
                        'height': height,
                        'file_size': file_size or 0,
                        'wp_created_at': item.get('date'),
                        'is_synced': True,
                        'synced_at': timezone.now(),
                    }
                )
                synced += 1

            except Exception as e:
                logger.error(f"Error syncing media {item.get('id')}: {e}")
                failed += 1

        log.synced_items = synced
        log.failed_items = failed
        log.status = MediaSyncLog.SyncStatus.SUCCESS if failed == 0 else MediaSyncLog.SyncStatus.PARTIAL
        log.completed_at = timezone.now()
        log.save()

        return {
            'total': log.total_items,
            'synced': synced,
            'failed': failed
        }

    except Exception as e:
        log.status = MediaSyncLog.SyncStatus.FAILED
        log.error_message = str(e)
        log.completed_at = timezone.now()
        log.save()
        logger.error(f"Media sync failed: {e}")
        raise


@shared_task
def download_media_file(media_file_id: int):
    """Download a single media file from WordPress"""
    from .models import MediaFile
    from django.core.files.base import ContentFile

    try:
        media_file = MediaFile.objects.get(id=media_file_id)

        if not media_file.wp_url:
            return {'error': 'No WordPress URL'}

        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(media_file.wp_url, headers=headers, timeout=60, stream=True)
        response.raise_for_status()

        content = ContentFile(response.content)
        media_file.file.save(media_file.filename, content, save=True)
        media_file.is_local = True
        media_file.save()

        return {'success': True, 'filename': media_file.filename}

    except MediaFile.DoesNotExist:
        return {'error': 'Media file not found'}
    except Exception as e:
        logger.error(f"Error downloading media file {media_file_id}: {e}")
        return {'error': str(e)}


@shared_task(bind=True, max_retries=3)
def upload_media_to_wordpress(self, media_file_id: int):
    """Upload a local media file to WordPress"""
    from .models import MediaFile

    try:
        media_file = MediaFile.objects.get(id=media_file_id)

        if not media_file.file:
            return {'error': 'No local file to upload'}

        if media_file.wp_id:
            return {'error': 'File already exists in WordPress', 'wp_id': media_file.wp_id}

        site_url = settings.WP_SITE_URL.rstrip('/')
        auth = HTTPBasicAuth(settings.WP_USERNAME, settings.WP_APP_PASSWORD)

        # Read file content
        media_file.file.seek(0)
        file_content = media_file.file.read()

        # Prepare headers for upload
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Disposition': f'attachment; filename="{media_file.filename}"',
            'Content-Type': media_file.mime_type or 'application/octet-stream',
        }

        # Upload to WordPress
        url = f"{site_url}/?rest_route=/wp/v2/media"
        response = requests.post(
            url,
            auth=auth,
            headers=headers,
            data=file_content,
            timeout=120
        )
        response.raise_for_status()

        result = response.json()
        wp_id = result.get('id')
        wp_url = result.get('source_url', '')

        # Update database record
        media_file.wp_id = wp_id
        media_file.wp_url = wp_url
        media_file.is_synced = True
        from django.utils import timezone
        media_file.synced_at = timezone.now()
        media_file.save()

        logger.info(f"Uploaded to WordPress: {media_file.filename} -> wp_id={wp_id}")
        return {'success': True, 'wp_id': wp_id, 'wp_url': wp_url}

    except MediaFile.DoesNotExist:
        return {'error': 'Media file not found'}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error uploading media file {media_file_id}: {e}")
        raise self.retry(exc=e, countdown=60)
    except Exception as e:
        logger.error(f"Error uploading media file {media_file_id}: {e}")
        return {'error': str(e)}


@shared_task
def sync_media_file_to_db(file_path: str):
    """Sync a single file from disk to database (used by watcher)"""
    from .models import MediaFile
    from django.core.files import File
    from pathlib import Path
    import mimetypes

    try:
        path = Path(file_path)
        if not path.exists():
            return {'error': 'File does not exist'}

        filename = path.name

        # Check if already exists
        existing = MediaFile.objects.filter(filename=filename).first()
        if existing:
            # Update existing
            stat = path.stat()
            existing.file_size = stat.st_size
            existing.is_local = True
            existing.save()
            return {'updated': True, 'id': existing.id}

        # Get file info
        stat = path.stat()
        mime_type, _ = mimetypes.guess_type(str(path))

        # Determine media type
        if mime_type:
            if mime_type.startswith('image/'):
                media_type = 'image'
            elif mime_type.startswith('video/'):
                media_type = 'video'
            elif mime_type.startswith('audio/'):
                media_type = 'audio'
            elif 'pdf' in mime_type or 'document' in mime_type:
                media_type = 'document'
            else:
                media_type = 'other'
        else:
            media_type = 'other'

        # Create new record
        media_file = MediaFile(
            title=path.stem.replace('_', ' ').replace('-', ' ').title(),
            filename=filename,
            mime_type=mime_type or 'application/octet-stream',
            media_type=media_type,
            file_size=stat.st_size,
            is_local=True,
            is_synced=False,
        )

        with open(path, 'rb') as f:
            media_file.file.save(filename, File(f), save=True)

        logger.info(f"Synced to database: {filename}")
        return {'created': True, 'id': media_file.id}

    except Exception as e:
        logger.error(f"Error syncing file {file_path}: {e}")
        return {'error': str(e)}
