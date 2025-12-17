"""
Management command to manage homepage sections.
"""

import json
from django.core.management.base import BaseCommand, CommandError

from apps.front_page.models import (
    HomepageSection,
    HomepageSectionItem,
    FrontPageSettings,
    SliderRevolution,
)


class Command(BaseCommand):
    help = 'Manage homepage sections and settings'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Action to perform')

        # List sections
        list_parser = subparsers.add_parser('list', help='List homepage sections')
        list_parser.add_argument('--language', type=str, default='de')

        # Show section details
        show_parser = subparsers.add_parser('show', help='Show section details')
        show_parser.add_argument('section_id', type=int)

        # Reorder sections
        reorder_parser = subparsers.add_parser('reorder', help='Reorder sections')
        reorder_parser.add_argument('--language', type=str, default='de')
        reorder_parser.add_argument('--order', type=str, help='Comma-separated section IDs in desired order')

        # Toggle section
        toggle_parser = subparsers.add_parser('toggle', help='Toggle section active status')
        toggle_parser.add_argument('section_id', type=int)

        # Export homepage
        export_parser = subparsers.add_parser('export', help='Export homepage configuration')
        export_parser.add_argument('--language', type=str, default='de')
        export_parser.add_argument('--output', type=str, required=True, help='Output JSON file')

        # Import homepage
        import_parser = subparsers.add_parser('import', help='Import homepage configuration')
        import_parser.add_argument('--input', type=str, required=True, help='Input JSON file')

        # Show settings
        settings_parser = subparsers.add_parser('settings', help='Show/edit front page settings')
        settings_parser.add_argument('--language', type=str, default='de')
        settings_parser.add_argument('--set-slider', type=int, help='Set main slider ID')
        settings_parser.add_argument('--set-title', type=str, help='Set meta title')
        settings_parser.add_argument('--set-description', type=str, help='Set meta description')

    def handle(self, *args, **options):
        action = options.get('action')

        if not action:
            self.stdout.write(self.style.ERROR('Please specify an action: list, show, reorder, toggle, export, import, settings'))
            return

        if action == 'list':
            self._list_sections(options['language'])
        elif action == 'show':
            self._show_section(options['section_id'])
        elif action == 'reorder':
            self._reorder_sections(options['language'], options.get('order'))
        elif action == 'toggle':
            self._toggle_section(options['section_id'])
        elif action == 'export':
            self._export_homepage(options['language'], options['output'])
        elif action == 'import':
            self._import_homepage(options['input'])
        elif action == 'settings':
            self._manage_settings(options)

    def _list_sections(self, language):
        """List all homepage sections for a language"""
        sections = HomepageSection.objects.filter(
            language=language
        ).order_by('order')

        if not sections.exists():
            self.stdout.write(self.style.WARNING(f'No sections found for language: {language}'))
            return

        self.stdout.write(f'\nHomepage Sections ({language}):\n' + '-' * 80)

        for section in sections:
            status = '✓' if section.is_active else '✗'
            items_count = section.items.count()

            self.stdout.write(
                f"[{section.id}] {status} Order {section.order}: {section.name} "
                f"({section.get_section_type_display()}) - {items_count} items"
            )

        self.stdout.write('-' * 80)
        self.stdout.write(f'Total: {sections.count()} sections\n')

    def _show_section(self, section_id):
        """Show detailed information about a section"""
        try:
            section = HomepageSection.objects.prefetch_related('items').get(id=section_id)
        except HomepageSection.DoesNotExist:
            raise CommandError(f'Section {section_id} not found')

        self.stdout.write(f'\nSection: {section.name}')
        self.stdout.write('-' * 40)
        self.stdout.write(f'ID: {section.id}')
        self.stdout.write(f'Type: {section.get_section_type_display()}')
        self.stdout.write(f'Language: {section.language}')
        self.stdout.write(f'Order: {section.order}')
        self.stdout.write(f'Active: {section.is_active}')
        self.stdout.write(f'Title: {section.title}')
        self.stdout.write(f'Subtitle: {section.subtitle}')

        if section.slider:
            self.stdout.write(f'Slider: {section.slider.name} (ID: {section.slider.id})')

        if section.cta_text:
            self.stdout.write(f'CTA: {section.cta_text} -> {section.cta_link}')

        if section.items.exists():
            self.stdout.write(f'\nItems ({section.items.count()}):')
            for item in section.items.order_by('order'):
                status = '✓' if item.is_active else '✗'
                self.stdout.write(f"  [{item.id}] {status} {item.title}")

    def _reorder_sections(self, language, order_str):
        """Reorder sections based on provided order"""
        if not order_str:
            # Interactive reordering
            sections = HomepageSection.objects.filter(
                language=language
            ).order_by('order')

            self.stdout.write('Current order:')
            for s in sections:
                self.stdout.write(f"  {s.id}: {s.name}")

            self.stdout.write('\nUse --order=1,3,2,5,4 to specify new order (comma-separated IDs)')
            return

        try:
            ids = [int(x.strip()) for x in order_str.split(',')]
        except ValueError:
            raise CommandError('Invalid order format. Use comma-separated IDs.')

        for i, section_id in enumerate(ids):
            updated = HomepageSection.objects.filter(
                id=section_id,
                language=language
            ).update(order=i)

            if updated:
                self.stdout.write(f'Section {section_id} -> order {i}')
            else:
                self.stdout.write(self.style.WARNING(f'Section {section_id} not found'))

        self.stdout.write(self.style.SUCCESS('Sections reordered'))

    def _toggle_section(self, section_id):
        """Toggle section active status"""
        try:
            section = HomepageSection.objects.get(id=section_id)
        except HomepageSection.DoesNotExist:
            raise CommandError(f'Section {section_id} not found')

        section.is_active = not section.is_active
        section.save(update_fields=['is_active'])

        status = 'activated' if section.is_active else 'deactivated'
        self.stdout.write(self.style.SUCCESS(f'Section "{section.name}" {status}'))

    def _export_homepage(self, language, filepath):
        """Export homepage configuration to JSON"""
        try:
            settings = FrontPageSettings.objects.get(language=language)
        except FrontPageSettings.DoesNotExist:
            settings = None

        sections = HomepageSection.objects.filter(
            language=language
        ).prefetch_related('items').order_by('order')

        data = {
            'language': language,
            'settings': None,
            'sections': []
        }

        if settings:
            data['settings'] = {
                'meta_title': settings.meta_title,
                'meta_description': settings.meta_description,
                'header_style': settings.header_style,
                'custom_css': settings.custom_css,
                'custom_js_header': settings.custom_js_header,
                'custom_js_footer': settings.custom_js_footer,
            }

        for section in sections:
            section_data = {
                'name': section.name,
                'section_type': section.section_type,
                'order': section.order,
                'is_active': section.is_active,
                'title': section.title,
                'subtitle': section.subtitle,
                'description': section.description,
                'content_html': section.content_html,
                'background_color': section.background_color,
                'background_style': section.background_style,
                'css_class': section.css_class,
                'css_id': section.css_id,
                'padding_top': section.padding_top,
                'padding_bottom': section.padding_bottom,
                'text_color': section.text_color,
                'cta_text': section.cta_text,
                'cta_link': section.cta_link,
                'settings': section.settings,
                'items': []
            }

            for item in section.items.order_by('order'):
                item_data = {
                    'title': item.title,
                    'subtitle': item.subtitle,
                    'description': item.description,
                    'order': item.order,
                    'is_active': item.is_active,
                    'icon_class': item.icon_class,
                    'link_url': item.link_url,
                    'link_text': item.link_text,
                    'author_name': item.author_name,
                    'author_title': item.author_title,
                    'rating': item.rating,
                    'stat_value': item.stat_value,
                    'stat_suffix': item.stat_suffix,
                    'custom_data': item.custom_data,
                }
                section_data['items'].append(item_data)

            data['sections'].append(section_data)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(
            f'Exported {len(data["sections"])} sections to {filepath}'
        ))

    def _import_homepage(self, filepath):
        """Import homepage configuration from JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'File not found: {filepath}')
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON: {e}')

        language = data.get('language', 'de')

        # Import settings
        if data.get('settings'):
            settings_data = data['settings']
            settings, created = FrontPageSettings.objects.update_or_create(
                language=language,
                defaults={
                    'meta_title': settings_data.get('meta_title', ''),
                    'meta_description': settings_data.get('meta_description', ''),
                    'header_style': settings_data.get('header_style', 'transparent'),
                    'custom_css': settings_data.get('custom_css', ''),
                    'custom_js_header': settings_data.get('custom_js_header', ''),
                    'custom_js_footer': settings_data.get('custom_js_footer', ''),
                }
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'{action} settings for {language}')

        # Import sections
        for section_data in data.get('sections', []):
            items_data = section_data.pop('items', [])

            section = HomepageSection.objects.create(
                language=language,
                name=section_data.get('name', 'Section'),
                section_type=section_data.get('section_type', 'custom'),
                order=section_data.get('order', 0),
                is_active=section_data.get('is_active', True),
                title=section_data.get('title', ''),
                subtitle=section_data.get('subtitle', ''),
                description=section_data.get('description', ''),
                content_html=section_data.get('content_html', ''),
                background_color=section_data.get('background_color', ''),
                background_style=section_data.get('background_style', ''),
                css_class=section_data.get('css_class', ''),
                css_id=section_data.get('css_id', ''),
                padding_top=section_data.get('padding_top', '60px'),
                padding_bottom=section_data.get('padding_bottom', '60px'),
                text_color=section_data.get('text_color', ''),
                cta_text=section_data.get('cta_text', ''),
                cta_link=section_data.get('cta_link', ''),
                settings=section_data.get('settings', {}),
            )

            for item_data in items_data:
                HomepageSectionItem.objects.create(
                    section=section,
                    title=item_data.get('title', ''),
                    subtitle=item_data.get('subtitle', ''),
                    description=item_data.get('description', ''),
                    order=item_data.get('order', 0),
                    is_active=item_data.get('is_active', True),
                    icon_class=item_data.get('icon_class', ''),
                    link_url=item_data.get('link_url', ''),
                    link_text=item_data.get('link_text', ''),
                    author_name=item_data.get('author_name', ''),
                    author_title=item_data.get('author_title', ''),
                    rating=item_data.get('rating'),
                    stat_value=item_data.get('stat_value', ''),
                    stat_suffix=item_data.get('stat_suffix', ''),
                    custom_data=item_data.get('custom_data', {}),
                )

            self.stdout.write(f'Created section: {section.name}')

        self.stdout.write(self.style.SUCCESS(
            f'Imported {len(data.get("sections", []))} sections'
        ))

    def _manage_settings(self, options):
        """Show or edit front page settings"""
        language = options['language']

        settings, created = FrontPageSettings.objects.get_or_create(
            language=language,
            defaults={'meta_title': 'Pro-FM'}
        )

        # Apply updates if provided
        updated = False
        if options.get('set_slider'):
            try:
                slider = SliderRevolution.objects.get(id=options['set_slider'])
                settings.main_slider = slider
                updated = True
                self.stdout.write(f'Main slider set to: {slider.name}')
            except SliderRevolution.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Slider {options["set_slider"]} not found'))

        if options.get('set_title'):
            settings.meta_title = options['set_title']
            updated = True

        if options.get('set_description'):
            settings.meta_description = options['set_description']
            updated = True

        if updated:
            settings.save()
            self.stdout.write(self.style.SUCCESS('Settings updated'))

        # Display current settings
        self.stdout.write(f'\nFront Page Settings ({language}):')
        self.stdout.write('-' * 40)
        self.stdout.write(f'Meta Title: {settings.meta_title}')
        self.stdout.write(f'Meta Description: {settings.meta_description}')
        self.stdout.write(f'Header Style: {settings.header_style}')
        self.stdout.write(f'WP Page ID: {settings.wp_page_id or "Not set"}')
        self.stdout.write(f'Main Slider: {settings.main_slider.name if settings.main_slider else "Not set"}')
        self.stdout.write(f'Last Updated: {settings.updated_at}')
