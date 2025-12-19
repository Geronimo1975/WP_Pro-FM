#!/usr/bin/env python3
"""
Import WordPress Pages and Front Page content into Django.

Usage:
    cd /root/WP_Pro-FM/backend
    python import_pages.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from bs4 import BeautifulSoup
import re

from apps.content.models import Post
from apps.media.models import MediaFile
from apps.front_page.models import (
    SliderRevolution, Slide, SlideLayer,
    HomepageSection, HomepageSectionItem, FrontPageSettings
)


# WordPress API configuration
WP_SITE_URL = settings.WP_SITE_URL.rstrip('/')
WP_AUTH = HTTPBasicAuth(settings.WP_USERNAME, settings.WP_APP_PASSWORD)


def get_api_url(endpoint):
    """Generate WordPress REST API URL."""
    return f"{WP_SITE_URL}/?rest_route=/wp/v2/{endpoint}"


def wp_get(endpoint, params=None):
    """Make GET request to WordPress API."""
    url = get_api_url(endpoint)
    response = requests.get(url, params=params, auth=WP_AUTH, timeout=60)
    response.raise_for_status()
    return response.json()


def wp_get_all(endpoint, per_page=100):
    """Get all items from paginated WordPress endpoint."""
    page = 1
    items = []
    while True:
        try:
            batch = wp_get(endpoint, params={"per_page": per_page, "page": page})
            if not batch:
                break
            items.extend(batch)
            print(f"  Fetched page {page} ({len(batch)} items)")
            page += 1
        except requests.exceptions.HTTPError as e:
            if "rest_post_invalid_page_number" in str(e.response.text):
                break
            raise
    return items


def clean_html(html_content):
    """Clean HTML content, removing scripts and unnecessary elements."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove script and style tags
    for tag in soup(['script', 'style']):
        tag.decompose()
    return str(soup)


def import_pages():
    """Import all WordPress pages."""
    print("\n" + "="*60)
    print("IMPORTING WORDPRESS PAGES")
    print("="*60)

    pages = wp_get_all("pages")
    print(f"\nFound {len(pages)} pages to import")

    created = 0
    updated = 0
    skipped = 0

    for wp_page in pages:
        wp_id = wp_page['id']
        title = wp_page['title']['rendered']
        slug = wp_page.get('slug', '')
        content = wp_page['content']['rendered']
        excerpt = wp_page.get('excerpt', {}).get('rendered', '')
        status = wp_page.get('status', 'publish')

        # Get featured image
        featured_media_id = wp_page.get('featured_media')
        featured_image = None
        if featured_media_id:
            try:
                featured_image = MediaFile.objects.get(wp_id=featured_media_id)
            except MediaFile.DoesNotExist:
                pass

        # Check if page exists
        try:
            page = Post.objects.get(wp_id=wp_id, post_type='page')
            # Update existing
            page.title = title
            page.slug = slug
            page.content = clean_html(content)
            page.excerpt = clean_html(excerpt)
            page.status = status
            page.featured_image = featured_image
            page.wp_link = wp_page.get('link', '')
            page.save()
            updated += 1
            print(f"  Updated: {title[:50]}")
        except Post.DoesNotExist:
            # Create new
            page = Post.objects.create(
                wp_id=wp_id,
                post_type='page',
                title=title,
                slug=slug,
                content=clean_html(content),
                excerpt=clean_html(excerpt),
                status=status,
                featured_image=featured_image,
                wp_link=wp_page.get('link', ''),
                language='de',
            )
            created += 1
            print(f"  Created: {title[:50]}")

    print(f"\nPages import complete: {created} created, {updated} updated, {skipped} skipped")
    return created, updated


def get_front_page_id():
    """Get the front page ID from WordPress settings."""
    try:
        # Try to get site settings
        response = requests.get(
            f"{WP_SITE_URL}/?rest_route=/",
            auth=WP_AUTH,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            # Check for front page in site info
            return data.get('page_on_front')
    except:
        pass
    return None


def extract_slider_from_page(page_content):
    """Extract slider shortcodes from page content."""
    sliders = []
    # Look for rev_slider shortcodes
    pattern = r'\[rev_slider[^\]]*alias="([^"]+)"[^\]]*\]'
    matches = re.findall(pattern, page_content)
    sliders.extend(matches)

    # Also check for id-based shortcodes
    pattern2 = r'\[rev_slider[^\]]*slidertitle="([^"]+)"[^\]]*\]'
    matches2 = re.findall(pattern2, page_content)
    sliders.extend(matches2)

    return sliders


def import_front_page():
    """Import front page settings and create homepage sections."""
    print("\n" + "="*60)
    print("IMPORTING FRONT PAGE SETTINGS")
    print("="*60)

    # Get or create front page settings for German
    settings_obj, created = FrontPageSettings.objects.get_or_create(
        language='de',
        defaults={
            'meta_title': 'Pro-FM - Facility Management',
            'meta_description': 'Professionelles Facility Management für Ihr Unternehmen',
            'header_style': 'transparent',
        }
    )

    if created:
        print("Created front page settings for German")
    else:
        print("Updated front page settings for German")

    # Try to find the front page
    front_page_id = get_front_page_id()
    if front_page_id:
        settings_obj.wp_page_id = front_page_id
        settings_obj.save()
        print(f"Set front page ID: {front_page_id}")

    # Fetch the actual front page content to analyze
    try:
        response = requests.get(WP_SITE_URL, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract page title
            title_tag = soup.find('title')
            if title_tag:
                settings_obj.meta_title = title_tag.text.strip()[:100]

            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                settings_obj.meta_description = meta_desc['content'][:200]

            settings_obj.save()
            print(f"Updated meta: {settings_obj.meta_title[:50]}...")
    except Exception as e:
        print(f"Warning: Could not fetch front page: {e}")

    return settings_obj


def create_sample_slider():
    """Create a sample slider with slides from imported media."""
    print("\n" + "="*60)
    print("CREATING SAMPLE SLIDER")
    print("="*60)

    # Check if slider already exists
    if SliderRevolution.objects.filter(name="Homepage Slider").exists():
        print("Homepage Slider already exists, skipping...")
        return

    # Get some hero images from media library
    hero_images = MediaFile.objects.filter(
        media_type='image',
        wp_url__icontains='hero'
    )[:3]

    if not hero_images:
        # Try to get any large images
        hero_images = MediaFile.objects.filter(
            media_type='image',
            width__gte=1200
        ).order_by('-width')[:3]

    if not hero_images:
        # Get any images
        hero_images = MediaFile.objects.filter(media_type='image')[:3]

    # Create the slider
    slider = SliderRevolution.objects.create(
        name="Homepage Slider",
        description="Main homepage slider for Pro-FM",
        slider_type='hero',
        is_active=True,
        width=1920,
        height=800,
        autoplay=True,
        autoplay_delay=5000,
        loop=True,
        pause_on_hover=True,
        show_navigation=True,
        show_bullets=True,
        language='de',
        wp_alias='homepage-slider',
    )
    print(f"Created slider: {slider.name}")

    # Create slides
    slide_data = [
        {
            'title': 'Professionelles Facility Management',
            'subtitle': 'Ihr Partner für effiziente Gebäudeverwaltung',
            'cta_text': 'Mehr erfahren',
            'cta_link': '/unsere-services/',
        },
        {
            'title': 'Technisches Gebäudemanagement',
            'subtitle': 'Wartung, Instandhaltung und Optimierung',
            'cta_text': 'Kontakt',
            'cta_link': '/kontakt/',
        },
        {
            'title': 'Kaufmännisches Facility Management',
            'subtitle': 'Kostenoptimierung und Prozessmanagement',
            'cta_text': 'Services ansehen',
            'cta_link': '/leistungen/',
        },
    ]

    for i, data in enumerate(slide_data):
        bg_image = hero_images[i] if i < len(hero_images) else None

        slide = Slide.objects.create(
            slider=slider,
            title=data['title'],
            subtitle=data['subtitle'],
            order=i,
            status='published',
            background_image=bg_image,
            background_color='#1a365d',
            overlay_color='rgba(0, 0, 0, 0.4)',
            cta_text=data['cta_text'],
            cta_link=data['cta_link'],
            duration=5000,
            transition='fade',
        )
        print(f"  Created slide: {slide.title}")

        # Add text layers
        SlideLayer.objects.create(
            slide=slide,
            name='Title',
            layer_type='text',
            order=1,
            content=f'<h1>{data["title"]}</h1>',
            position_x='center',
            position_y='middle',
            offset_y=-50,
            animation_in='fade',
            start_time=500,
            css_class='slider-title',
        )

        SlideLayer.objects.create(
            slide=slide,
            name='Subtitle',
            layer_type='text',
            order=2,
            content=f'<p>{data["subtitle"]}</p>',
            position_x='center',
            position_y='middle',
            offset_y=20,
            animation_in='fade',
            start_time=800,
            css_class='slider-subtitle',
        )

        if data.get('cta_text'):
            SlideLayer.objects.create(
                slide=slide,
                name='CTA Button',
                layer_type='button',
                order=3,
                content=data['cta_text'],
                link_url=data['cta_link'],
                position_x='center',
                position_y='middle',
                offset_y=100,
                animation_in='slide',
                start_time=1100,
                css_class='slider-cta-button',
            )

    # Link slider to front page settings
    try:
        fp_settings = FrontPageSettings.objects.get(language='de')
        fp_settings.main_slider = slider
        fp_settings.save()
        print(f"Linked slider to front page settings")
    except FrontPageSettings.DoesNotExist:
        pass

    return slider


def create_homepage_sections():
    """Create sample homepage sections."""
    print("\n" + "="*60)
    print("CREATING HOMEPAGE SECTIONS")
    print("="*60)

    sections_data = [
        {
            'name': 'Hero Slider',
            'section_type': 'slider',
            'order': 0,
            'title': '',
            'subtitle': '',
        },
        {
            'name': 'Unsere Services',
            'section_type': 'services',
            'order': 1,
            'title': 'Unsere Leistungen',
            'subtitle': 'Professionelles Facility Management aus einer Hand',
            'items': [
                {'title': 'Technisches FM', 'icon_class': 'fa fa-cogs', 'description': 'Wartung und Instandhaltung technischer Anlagen'},
                {'title': 'Kaufmännisches FM', 'icon_class': 'fa fa-chart-line', 'description': 'Kostenmanagement und Vertragsmanagement'},
                {'title': 'Infrastrukturelles FM', 'icon_class': 'fa fa-building', 'description': 'Reinigung, Sicherheit und Empfangsdienste'},
            ]
        },
        {
            'name': 'Über Uns',
            'section_type': 'about',
            'order': 2,
            'title': 'Über Pro-FM',
            'subtitle': 'Ihr erfahrener Partner im Facility Management',
            'description': 'Mit jahrelanger Erfahrung im Facility Management bieten wir Ihnen maßgeschneiderte Lösungen für Ihre Immobilien.',
        },
        {
            'name': 'Statistiken',
            'section_type': 'stats',
            'order': 3,
            'title': 'Pro-FM in Zahlen',
            'items': [
                {'title': 'Zufriedene Kunden', 'stat_value': '500', 'stat_suffix': '+'},
                {'title': 'Jahre Erfahrung', 'stat_value': '25', 'stat_suffix': '+'},
                {'title': 'Mitarbeiter', 'stat_value': '150', 'stat_suffix': '+'},
                {'title': 'Projekte', 'stat_value': '1000', 'stat_suffix': '+'},
            ]
        },
        {
            'name': 'Call to Action',
            'section_type': 'cta',
            'order': 4,
            'title': 'Bereit für professionelles Facility Management?',
            'subtitle': 'Kontaktieren Sie uns für ein unverbindliches Angebot',
            'cta_text': 'Jetzt anfragen',
            'cta_link': '/kontakt/',
            'background_color': '#1a365d',
            'text_color': '#ffffff',
        },
    ]

    created_count = 0
    for section_data in sections_data:
        items = section_data.pop('items', [])

        # Check if section exists
        if HomepageSection.objects.filter(name=section_data['name'], language='de').exists():
            print(f"  Section '{section_data['name']}' already exists, skipping...")
            continue

        section = HomepageSection.objects.create(
            language='de',
            is_active=True,
            **section_data
        )
        print(f"  Created section: {section.name}")
        created_count += 1

        # Link slider if it's a slider section
        if section.section_type == 'slider':
            try:
                slider = SliderRevolution.objects.get(name="Homepage Slider")
                section.slider = slider
                section.save()
            except SliderRevolution.DoesNotExist:
                pass

        # Create items
        for i, item_data in enumerate(items):
            HomepageSectionItem.objects.create(
                section=section,
                order=i,
                is_active=True,
                **item_data
            )

    print(f"\nCreated {created_count} homepage sections")


def main():
    print("="*60)
    print("WORDPRESS PAGES & FRONT PAGE IMPORT")
    print(f"Site: {WP_SITE_URL}")
    print("="*60)

    # Import pages
    pages_created, pages_updated = import_pages()

    # Import front page settings
    import_front_page()

    # Create sample slider
    create_sample_slider()

    # Create homepage sections
    create_homepage_sections()

    print("\n" + "="*60)
    print("IMPORT COMPLETE")
    print("="*60)
    print(f"Pages: {pages_created} created, {pages_updated} updated")
    print(f"Sliders: Check admin at /admin/front_page/sliderrevolution/")
    print(f"Sections: Check admin at /admin/front_page/homepagesection/")


if __name__ == "__main__":
    main()
