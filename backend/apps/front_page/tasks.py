"""
Celery tasks for Front Page management.
"""

import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_slider_revolution_from_wp(self, slider_id=None):
    """
    Sync Slider Revolution data from WordPress.

    If slider_id is provided, syncs only that slider.
    Otherwise, syncs all sliders.
    """
    from .models import SliderRevolution
    from wpml.wp_client import WordPressClient

    try:
        client = WordPressClient()

        # Note: Slider Revolution doesn't have a standard REST API
        # This is a placeholder for custom implementation
        # You may need to create a custom WordPress plugin/endpoint

        if slider_id:
            sliders = SliderRevolution.objects.filter(id=slider_id)
        else:
            sliders = SliderRevolution.objects.filter(wp_slider_id__isnull=False)

        synced_count = 0
        for slider in sliders:
            try:
                # Placeholder: Implement actual sync logic
                # This requires a custom WordPress REST endpoint for Slider Revolution
                slider.synced_at = timezone.now()
                slider.save(update_fields=['synced_at'])
                synced_count += 1

            except Exception as e:
                logger.error(f"Error syncing slider {slider.id}: {e}")

        logger.info(f"Synced {synced_count} sliders from WordPress")
        return {'synced': synced_count}

    except Exception as exc:
        logger.error(f"Slider sync failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def publish_slider_to_wp(self, slider_id):
    """
    Publish/update a slider to WordPress via REST API.

    Note: Requires custom WordPress endpoint for Slider Revolution.
    """
    from .models import SliderRevolution
    from wpml.wp_client import WordPressClient

    try:
        slider = SliderRevolution.objects.prefetch_related(
            'slides', 'slides__layers'
        ).get(id=slider_id)

        client = WordPressClient()

        # Build slider data for WordPress
        slider_data = {
            'title': slider.name,
            'alias': slider.wp_alias or slider.name.lower().replace(' ', '-'),
            'settings': {
                'type': slider.slider_type,
                'width': slider.width,
                'height': slider.height,
                'autoplay': slider.autoplay,
                'autoplayDelay': slider.autoplay_delay,
                'loop': slider.loop,
                'pauseOnHover': slider.pause_on_hover,
                'navigation': slider.show_navigation,
                'bullets': slider.show_bullets,
                'progress': slider.show_progress,
            },
            'slides': []
        }

        # Add slides
        for slide in slider.slides.filter(status='published').order_by('order'):
            slide_data = {
                'title': slide.title,
                'subtitle': slide.subtitle,
                'order': slide.order,
                'duration': slide.duration,
                'transition': slide.transition,
                'transitionDuration': slide.transition_duration,
                'background': {
                    'color': slide.background_color,
                    'videoUrl': slide.background_video_url,
                    'overlay': slide.overlay_color,
                },
                'cta': {
                    'text': slide.cta_text,
                    'link': slide.cta_link,
                    'style': slide.cta_style,
                },
                'layers': []
            }

            # Add background image URL if exists
            if slide.background_image:
                slide_data['background']['image'] = slide.background_image.file_url

            # Add layers
            for layer in slide.layers.order_by('order'):
                layer_data = {
                    'name': layer.name,
                    'type': layer.layer_type,
                    'order': layer.order,
                    'content': layer.content,
                    'link': layer.link_url,
                    'linkTarget': layer.link_target,
                    'position': {
                        'x': layer.position_x,
                        'y': layer.position_y,
                        'offsetX': layer.offset_x,
                        'offsetY': layer.offset_y,
                    },
                    'size': {
                        'width': layer.width,
                        'height': layer.height,
                    },
                    'animation': {
                        'in': layer.animation_in,
                        'out': layer.animation_out,
                        'startTime': layer.start_time,
                        'endTime': layer.end_time,
                        'speed': layer.animation_speed,
                    },
                    'style': {
                        'cssClass': layer.css_class,
                        'customStyle': layer.custom_style,
                    },
                    'responsive': {
                        'desktop': layer.visible_desktop,
                        'tablet': layer.visible_tablet,
                        'mobile': layer.visible_mobile,
                    }
                }

                if layer.media_file:
                    layer_data['mediaUrl'] = layer.media_file.file_url

                slide_data['layers'].append(layer_data)

            slider_data['slides'].append(slide_data)

        # Note: This requires a custom WordPress REST endpoint
        # Example: POST /wp-json/revslider/v1/sliders
        # You need to create a WordPress plugin that exposes this endpoint

        logger.info(f"Slider {slider_id} data prepared for publishing")
        logger.info(f"Slider data: {slider_data}")

        # Placeholder for actual API call
        # response = client.post('revslider/v1/sliders', slider_data)

        slider.synced_at = timezone.now()
        slider.save(update_fields=['synced_at'])

        return {
            'slider_id': slider_id,
            'status': 'prepared',
            'slides_count': len(slider_data['slides'])
        }

    except SliderRevolution.DoesNotExist:
        logger.error(f"Slider {slider_id} not found")
        return {'error': 'Slider not found'}

    except Exception as exc:
        logger.error(f"Error publishing slider {slider_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def sync_front_page_settings(language='de'):
    """
    Sync front page settings with WordPress.
    """
    from .models import FrontPageSettings
    from wpml.wp_client import WordPressClient

    try:
        settings = FrontPageSettings.objects.get(language=language)
        client = WordPressClient()

        # Get WordPress front page ID
        # This uses the standard WordPress REST API
        site_settings = client.get('settings')

        if site_settings:
            wp_front_page_id = site_settings.get('page_on_front')
            if wp_front_page_id and wp_front_page_id != settings.wp_page_id:
                settings.wp_page_id = wp_front_page_id
                settings.save(update_fields=['wp_page_id'])
                logger.info(f"Updated front page ID to {wp_front_page_id}")

        return {'language': language, 'wp_page_id': settings.wp_page_id}

    except FrontPageSettings.DoesNotExist:
        logger.warning(f"Front page settings for {language} not found")
        return {'error': 'Settings not found'}

    except Exception as e:
        logger.error(f"Error syncing front page settings: {e}")
        return {'error': str(e)}


@shared_task
def generate_slider_preview(slider_id):
    """
    Generate a preview image/HTML for a slider.
    """
    from .models import SliderRevolution

    try:
        slider = SliderRevolution.objects.prefetch_related(
            'slides', 'slides__layers', 'slides__background_image'
        ).get(id=slider_id)

        # Generate preview HTML
        preview_html = f"""
        <div class="slider-preview" style="width:{slider.width}px; height:{slider.height}px; position:relative; overflow:hidden;">
        """

        for slide in slider.slides.filter(status='published').order_by('order')[:1]:
            bg_style = ''
            if slide.background_color:
                bg_style += f'background-color: {slide.background_color};'
            if slide.background_image:
                bg_style += f'background-image: url({slide.background_image.file_url}); background-size: cover;'

            preview_html += f"""
            <div class="slide" style="{bg_style} width:100%; height:100%; position:absolute;">
                <div class="slide-content" style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center;">
                    <h2>{slide.title}</h2>
                    <p>{slide.subtitle}</p>
                </div>
            </div>
            """

        preview_html += "</div>"

        return {
            'slider_id': slider_id,
            'preview_html': preview_html
        }

    except SliderRevolution.DoesNotExist:
        return {'error': 'Slider not found'}


@shared_task
def cleanup_expired_slides():
    """
    Deactivate slides that have passed their expire_date.
    """
    from .models import Slide

    now = timezone.now()
    expired = Slide.objects.filter(
        expire_date__lt=now,
        status='published'
    )

    count = expired.update(status='draft')

    if count > 0:
        logger.info(f"Deactivated {count} expired slides")

    return {'deactivated': count}


@shared_task
def activate_scheduled_slides():
    """
    Activate slides that have reached their publish_date.
    """
    from .models import Slide

    now = timezone.now()
    scheduled = Slide.objects.filter(
        publish_date__lte=now,
        status='draft',
        expire_date__gt=now
    ) | Slide.objects.filter(
        publish_date__lte=now,
        status='draft',
        expire_date__isnull=True
    )

    count = scheduled.update(status='published')

    if count > 0:
        logger.info(f"Activated {count} scheduled slides")

    return {'activated': count}
