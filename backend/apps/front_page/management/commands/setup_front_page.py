"""
Management command to setup initial front page configuration.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.front_page.models import (
    SliderRevolution,
    Slide,
    HomepageSection,
    HomepageSectionItem,
    FrontPageSettings,
)
from apps.content.wpml import WPMLLanguage


class Command(BaseCommand):
    help = 'Setup initial front page configuration with default sections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--language',
            type=str,
            default='de',
            help='Language code (default: de)'
        )
        parser.add_argument(
            '--with-demo',
            action='store_true',
            help='Create demo content for testing'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation even if data exists'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        language = options['language']
        with_demo = options['with_demo']
        force = options['force']

        self.stdout.write(f'Setting up front page for language: {language}')

        # Check if settings already exist
        settings_exist = FrontPageSettings.objects.filter(language=language).exists()
        if settings_exist and not force:
            self.stdout.write(
                self.style.WARNING(f'Front page settings for {language} already exist. Use --force to recreate.')
            )
            return

        if force and settings_exist:
            self.stdout.write('Removing existing configuration...')
            FrontPageSettings.objects.filter(language=language).delete()
            HomepageSection.objects.filter(language=language).delete()

        # Create front page settings
        settings = FrontPageSettings.objects.create(
            language=language,
            meta_title='Pro-FM Facility Management',
            meta_description='Professionelles Facility Management für Ihr Unternehmen. Gebäudemanagement, Reinigung, Sicherheit und mehr.',
            header_style='transparent',
        )
        self.stdout.write(self.style.SUCCESS(f'Created FrontPageSettings for {language}'))

        if with_demo:
            self._create_demo_content(language, settings)

        self.stdout.write(self.style.SUCCESS('Front page setup completed!'))

    def _create_demo_content(self, language, settings):
        """Create demo content for testing"""

        # Create main slider
        self.stdout.write('Creating demo slider...')
        slider = SliderRevolution.objects.create(
            name='Hero Slider',
            description='Hauptslider für die Startseite',
            slider_type='hero',
            is_active=True,
            language=language,
            width=1920,
            height=800,
            autoplay=True,
            autoplay_delay=5000,
        )

        # Create demo slides
        slides_data = [
            {
                'title': 'Professionelles Facility Management',
                'subtitle': 'Kompetenz in Gebäudemanagement seit über 20 Jahren',
                'cta_text': 'Mehr erfahren',
                'cta_link': '/leistungen/',
            },
            {
                'title': 'Reinigungsservice',
                'subtitle': 'Sauberkeit auf höchstem Niveau',
                'cta_text': 'Kontakt aufnehmen',
                'cta_link': '/kontakt/',
            },
            {
                'title': 'Sicherheitsdienste',
                'subtitle': '24/7 Schutz für Ihr Unternehmen',
                'cta_text': 'Jetzt anfragen',
                'cta_link': '/sicherheit/',
            },
        ]

        for i, slide_data in enumerate(slides_data):
            Slide.objects.create(
                slider=slider,
                title=slide_data['title'],
                subtitle=slide_data['subtitle'],
                order=i,
                status='published',
                cta_text=slide_data['cta_text'],
                cta_link=slide_data['cta_link'],
                duration=5000,
                transition='fade',
            )

        settings.main_slider = slider
        settings.save()
        self.stdout.write(self.style.SUCCESS(f'Created slider with {len(slides_data)} slides'))

        # Create homepage sections
        self.stdout.write('Creating homepage sections...')

        sections_data = [
            {
                'name': 'Slider Section',
                'section_type': 'slider',
                'order': 0,
                'title': '',
                'slider': slider,
            },
            {
                'name': 'Services',
                'section_type': 'services',
                'order': 1,
                'title': 'Unsere Leistungen',
                'subtitle': 'Umfassende Facility Management Lösungen',
                'items': [
                    {
                        'title': 'Gebäudereinigung',
                        'description': 'Professionelle Reinigung für Büros, Praxen und Gewerbeflächen.',
                        'icon_class': 'fa fa-building',
                    },
                    {
                        'title': 'Hausmeisterservice',
                        'description': 'Zuverlässige Hausmeisterdienste für Ihre Immobilie.',
                        'icon_class': 'fa fa-tools',
                    },
                    {
                        'title': 'Sicherheitsdienst',
                        'description': 'Professioneller Objektschutz und Sicherheitspersonal.',
                        'icon_class': 'fa fa-shield-alt',
                    },
                    {
                        'title': 'Grünanlagenpflege',
                        'description': 'Gartenpflege und Außenanlagenbetreuung.',
                        'icon_class': 'fa fa-leaf',
                    },
                ]
            },
            {
                'name': 'About Us',
                'section_type': 'about',
                'order': 2,
                'title': 'Über Pro-FM',
                'subtitle': 'Ihr Partner für Facility Management',
                'description': '''Pro-FM ist Ihr kompetenter Partner für professionelles Facility Management.
Mit über 20 Jahren Erfahrung bieten wir maßgeschneiderte Lösungen für Unternehmen jeder Größe.
Unser Team aus qualifizierten Fachkräften sorgt für den reibungslosen Betrieb Ihrer Immobilien.''',
            },
            {
                'name': 'Statistics',
                'section_type': 'stats',
                'order': 3,
                'title': 'Pro-FM in Zahlen',
                'items': [
                    {'title': 'Jahre Erfahrung', 'stat_value': '20', 'stat_suffix': '+'},
                    {'title': 'Zufriedene Kunden', 'stat_value': '500', 'stat_suffix': '+'},
                    {'title': 'Mitarbeiter', 'stat_value': '150', 'stat_suffix': ''},
                    {'title': 'Betreute Objekte', 'stat_value': '1000', 'stat_suffix': '+'},
                ]
            },
            {
                'name': 'Testimonials',
                'section_type': 'testimonials',
                'order': 4,
                'title': 'Das sagen unsere Kunden',
                'items': [
                    {
                        'title': 'Hervorragende Zusammenarbeit',
                        'description': 'Die Zusammenarbeit mit Pro-FM ist seit Jahren ausgezeichnet. Zuverlässig und professionell.',
                        'author_name': 'Thomas Müller',
                        'author_title': 'Geschäftsführer, ABC GmbH',
                        'rating': 5,
                    },
                    {
                        'title': 'Beste Qualität',
                        'description': 'Pro-FM liefert konstant hohe Qualität. Wir sind sehr zufrieden mit dem Service.',
                        'author_name': 'Anna Schmidt',
                        'author_title': 'Facility Manager, XYZ AG',
                        'rating': 5,
                    },
                ]
            },
            {
                'name': 'CTA Section',
                'section_type': 'cta',
                'order': 5,
                'title': 'Starten Sie jetzt!',
                'subtitle': 'Kontaktieren Sie uns für ein unverbindliches Angebot',
                'cta_text': 'Kontakt aufnehmen',
                'cta_link': '/kontakt/',
                'background_color': '#0066cc',
                'text_color': '#ffffff',
            },
        ]

        for section_data in sections_data:
            items_data = section_data.pop('items', [])
            slider_ref = section_data.pop('slider', None)

            section = HomepageSection.objects.create(
                language=language,
                is_active=True,
                **section_data
            )

            if slider_ref:
                section.slider = slider_ref
                section.save()

            for i, item_data in enumerate(items_data):
                HomepageSectionItem.objects.create(
                    section=section,
                    order=i,
                    is_active=True,
                    **item_data
                )

        self.stdout.write(self.style.SUCCESS(f'Created {len(sections_data)} homepage sections'))
