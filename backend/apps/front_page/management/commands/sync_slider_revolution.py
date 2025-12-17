"""
Management command to sync Slider Revolution with WordPress.
"""

import json
from django.core.management.base import BaseCommand, CommandError

from apps.front_page.models import SliderRevolution, Slide, SlideLayer
from apps.front_page.tasks import sync_slider_revolution_from_wp, publish_slider_to_wp


class Command(BaseCommand):
    help = 'Sync Slider Revolution sliders with WordPress'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slider-id',
            type=int,
            help='Specific slider ID to sync'
        )
        parser.add_argument(
            '--direction',
            type=str,
            choices=['from-wp', 'to-wp'],
            default='from-wp',
            help='Sync direction: from-wp (import) or to-wp (export)'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            dest='run_async',
            help='Run sync as Celery task'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            dest='list_sliders',
            help='List all sliders'
        )
        parser.add_argument(
            '--export-json',
            type=str,
            help='Export slider configuration to JSON file'
        )
        parser.add_argument(
            '--import-json',
            type=str,
            help='Import slider configuration from JSON file'
        )

    def handle(self, *args, **options):
        if options['list_sliders']:
            self._list_sliders()
            return

        if options['export_json']:
            self._export_json(options['slider_id'], options['export_json'])
            return

        if options['import_json']:
            self._import_json(options['import_json'])
            return

        slider_id = options['slider_id']
        direction = options['direction']
        run_async = options['run_async']

        if direction == 'from-wp':
            self._sync_from_wp(slider_id, run_async)
        else:
            self._sync_to_wp(slider_id, run_async)

    def _list_sliders(self):
        """List all sliders with their details"""
        sliders = SliderRevolution.objects.all().order_by('language', 'name')

        if not sliders.exists():
            self.stdout.write(self.style.WARNING('No sliders found.'))
            return

        self.stdout.write('\nSliders:\n' + '-' * 80)
        for slider in sliders:
            slides_count = slider.slides.count()
            status = '✓' if slider.is_active else '✗'

            self.stdout.write(
                f"[{slider.id}] {status} {slider.name} ({slider.language}) - "
                f"{slider.get_slider_type_display()} - {slides_count} slides"
            )
            if slider.wp_slider_id:
                self.stdout.write(f"     WP ID: {slider.wp_slider_id}, Alias: {slider.wp_alias}")
            if slider.synced_at:
                self.stdout.write(f"     Last synced: {slider.synced_at}")

        self.stdout.write('-' * 80)
        self.stdout.write(f'Total: {sliders.count()} sliders\n')

    def _sync_from_wp(self, slider_id, run_async):
        """Sync sliders from WordPress"""
        self.stdout.write('Syncing sliders from WordPress...')

        if run_async:
            task = sync_slider_revolution_from_wp.delay(slider_id)
            self.stdout.write(self.style.SUCCESS(f'Sync task queued: {task.id}'))
        else:
            result = sync_slider_revolution_from_wp(slider_id)
            self.stdout.write(self.style.SUCCESS(f'Sync completed: {result}'))

    def _sync_to_wp(self, slider_id, run_async):
        """Publish slider to WordPress"""
        if not slider_id:
            raise CommandError('--slider-id is required for to-wp sync')

        self.stdout.write(f'Publishing slider {slider_id} to WordPress...')

        if run_async:
            task = publish_slider_to_wp.delay(slider_id)
            self.stdout.write(self.style.SUCCESS(f'Publish task queued: {task.id}'))
        else:
            result = publish_slider_to_wp(slider_id)
            self.stdout.write(self.style.SUCCESS(f'Publish completed: {result}'))

    def _export_json(self, slider_id, filepath):
        """Export slider configuration to JSON"""
        if not slider_id:
            raise CommandError('--slider-id is required for export')

        try:
            slider = SliderRevolution.objects.prefetch_related(
                'slides', 'slides__layers'
            ).get(id=slider_id)
        except SliderRevolution.DoesNotExist:
            raise CommandError(f'Slider {slider_id} not found')

        data = {
            'name': slider.name,
            'description': slider.description,
            'slider_type': slider.slider_type,
            'language': slider.language,
            'settings': {
                'width': slider.width,
                'height': slider.height,
                'autoplay': slider.autoplay,
                'autoplay_delay': slider.autoplay_delay,
                'loop': slider.loop,
                'pause_on_hover': slider.pause_on_hover,
                'show_navigation': slider.show_navigation,
                'show_bullets': slider.show_bullets,
                'show_progress': slider.show_progress,
            },
            'custom_css': slider.custom_css,
            'custom_js': slider.custom_js,
            'slides': []
        }

        for slide in slider.slides.order_by('order'):
            slide_data = {
                'title': slide.title,
                'subtitle': slide.subtitle,
                'order': slide.order,
                'status': slide.status,
                'background_color': slide.background_color,
                'background_video_url': slide.background_video_url,
                'overlay_color': slide.overlay_color,
                'content_html': slide.content_html,
                'cta_text': slide.cta_text,
                'cta_link': slide.cta_link,
                'cta_style': slide.cta_style,
                'secondary_cta_text': slide.secondary_cta_text,
                'secondary_cta_link': slide.secondary_cta_link,
                'duration': slide.duration,
                'transition': slide.transition,
                'transition_duration': slide.transition_duration,
                'layers': []
            }

            for layer in slide.layers.order_by('order'):
                layer_data = {
                    'name': layer.name,
                    'layer_type': layer.layer_type,
                    'order': layer.order,
                    'content': layer.content,
                    'link_url': layer.link_url,
                    'link_target': layer.link_target,
                    'position_x': layer.position_x,
                    'position_y': layer.position_y,
                    'offset_x': layer.offset_x,
                    'offset_y': layer.offset_y,
                    'width': layer.width,
                    'height': layer.height,
                    'animation_in': layer.animation_in,
                    'animation_out': layer.animation_out,
                    'start_time': layer.start_time,
                    'end_time': layer.end_time,
                    'animation_speed': layer.animation_speed,
                    'css_class': layer.css_class,
                    'custom_style': layer.custom_style,
                    'visible_desktop': layer.visible_desktop,
                    'visible_tablet': layer.visible_tablet,
                    'visible_mobile': layer.visible_mobile,
                }
                slide_data['layers'].append(layer_data)

            data['slides'].append(slide_data)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f'Exported slider to {filepath}'))

    def _import_json(self, filepath):
        """Import slider configuration from JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'File not found: {filepath}')
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON: {e}')

        settings = data.get('settings', {})

        slider = SliderRevolution.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            slider_type=data.get('slider_type', 'standard'),
            language=data.get('language', 'de'),
            is_active=False,  # Start inactive
            width=settings.get('width', 1920),
            height=settings.get('height', 800),
            autoplay=settings.get('autoplay', True),
            autoplay_delay=settings.get('autoplay_delay', 5000),
            loop=settings.get('loop', True),
            pause_on_hover=settings.get('pause_on_hover', True),
            show_navigation=settings.get('show_navigation', True),
            show_bullets=settings.get('show_bullets', True),
            show_progress=settings.get('show_progress', False),
            custom_css=data.get('custom_css', ''),
            custom_js=data.get('custom_js', ''),
        )

        for slide_data in data.get('slides', []):
            layers_data = slide_data.pop('layers', [])

            slide = Slide.objects.create(
                slider=slider,
                title=slide_data.get('title', ''),
                subtitle=slide_data.get('subtitle', ''),
                order=slide_data.get('order', 0),
                status=slide_data.get('status', 'draft'),
                background_color=slide_data.get('background_color', ''),
                background_video_url=slide_data.get('background_video_url', ''),
                overlay_color=slide_data.get('overlay_color', ''),
                content_html=slide_data.get('content_html', ''),
                cta_text=slide_data.get('cta_text', ''),
                cta_link=slide_data.get('cta_link', ''),
                cta_style=slide_data.get('cta_style', ''),
                secondary_cta_text=slide_data.get('secondary_cta_text', ''),
                secondary_cta_link=slide_data.get('secondary_cta_link', ''),
                duration=slide_data.get('duration', 5000),
                transition=slide_data.get('transition', 'fade'),
                transition_duration=slide_data.get('transition_duration', 1000),
            )

            for layer_data in layers_data:
                SlideLayer.objects.create(
                    slide=slide,
                    name=layer_data.get('name', 'Layer'),
                    layer_type=layer_data.get('layer_type', 'text'),
                    order=layer_data.get('order', 0),
                    content=layer_data.get('content', ''),
                    link_url=layer_data.get('link_url', ''),
                    link_target=layer_data.get('link_target', '_self'),
                    position_x=layer_data.get('position_x', 'center'),
                    position_y=layer_data.get('position_y', 'middle'),
                    offset_x=layer_data.get('offset_x', 0),
                    offset_y=layer_data.get('offset_y', 0),
                    width=layer_data.get('width', ''),
                    height=layer_data.get('height', ''),
                    animation_in=layer_data.get('animation_in', 'fade'),
                    animation_out=layer_data.get('animation_out', 'fade'),
                    start_time=layer_data.get('start_time', 0),
                    end_time=layer_data.get('end_time'),
                    animation_speed=layer_data.get('animation_speed', 500),
                    css_class=layer_data.get('css_class', ''),
                    custom_style=layer_data.get('custom_style', ''),
                    visible_desktop=layer_data.get('visible_desktop', True),
                    visible_tablet=layer_data.get('visible_tablet', True),
                    visible_mobile=layer_data.get('visible_mobile', True),
                )

        slides_count = slider.slides.count()
        self.stdout.write(self.style.SUCCESS(
            f'Imported slider "{slider.name}" (ID: {slider.id}) with {slides_count} slides'
        ))
