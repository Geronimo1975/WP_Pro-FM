#!/usr/bin/env python3
"""
Sync Pro-FM Glossary Terms to WordPress

Creates:
- Main glossary page at /glossar/
- Letter pages at /glossar-a/, /glossar-b/, etc.
- Category pages at /kategorie-facility-management/, etc.
- Individual term pages at /term-slug/

Usage:
    cd /root/WP_Pro-FM/backend
    python sync_glossary_to_wp.py                    # Sync all
    python sync_glossary_to_wp.py --letter A         # Sync only letter A
    python sync_glossary_to_wp.py --main-only        # Create main page only
    python sync_glossary_to_wp.py --categories-only  # Create category pages only
"""

import os
import sys
import time
import argparse
import django
import requests
from requests.auth import HTTPBasicAuth

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.conf import settings
from django.utils import timezone
from django.db.models import Count
from apps.glossary.models import GlossaryTerm, GlossaryCategory, GlossarySyncLog


class GlossaryWordPressSync:
    """Sync glossary terms to WordPress"""

    def __init__(self):
        self.wp_site_url = settings.WP_SITE_URL.rstrip('/')
        self.wp_auth = HTTPBasicAuth(settings.WP_USERNAME, settings.WP_APP_PASSWORD)
        self.session = requests.Session()
        self.session.auth = self.wp_auth

    def get_api_url(self, endpoint):
        """Generate WordPress REST API URL with ?rest_route= format"""
        return f"{self.wp_site_url}/?rest_route=/wp/v2/{endpoint}"

    def wp_get(self, endpoint, params=None):
        """GET request to WordPress API"""
        url = self.get_api_url(endpoint)
        response = self.session.get(url, params=params, timeout=60)
        response.raise_for_status()
        return response.json()

    def wp_post(self, endpoint, data):
        """POST request to WordPress API"""
        url = self.get_api_url(endpoint)
        response = self.session.post(url, json=data, timeout=60)
        response.raise_for_status()
        return response.json()

    def create_or_update_page(self, slug, title, content, parent_id=0):
        """Create or update a WordPress page"""
        # Check if page exists
        try:
            existing = self.wp_get("pages", params={"slug": slug})
            if existing:
                # Update existing page
                page_id = existing[0]['id']
                result = self.wp_post(f"pages/{page_id}", {
                    'title': title,
                    'content': content,
                    'status': 'publish',
                    'parent': parent_id
                })
                print(f"  Updated: {slug} (ID: {page_id})")
                return page_id
        except:
            pass

        # Create new page
        result = self.wp_post("pages", {
            'title': title,
            'content': content,
            'status': 'publish',
            'slug': slug,
            'parent': parent_id
        })
        page_id = result['id']
        print(f"  Created: {slug} (ID: {page_id})")
        return page_id

    def create_main_glossary_page(self):
        """Create main glossary page at /glossar/"""
        print("\nCreating main glossary page...")

        # Get statistics
        total_terms = GlossaryTerm.objects.filter(is_active=True).count()
        letter_data = (GlossaryTerm.objects
                       .filter(is_active=True)
                       .values('letter')
                       .annotate(count=Count('id'))
                       .order_by('letter'))

        category_data = (GlossaryTerm.objects
                         .filter(is_active=True, category__isnull=False)
                         .values('category__name', 'category__slug')
                         .annotate(count=Count('id'))
                         .order_by('-count'))

        # Build A-Z navigation
        az_links = []
        for item in letter_data:
            letter = item['letter']
            count = item['count']
            az_links.append(f'''
<div style="text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
    <a href="/glossar-{letter.lower()}/" style="text-decoration: none;">
        <div style="font-size: 32px; font-weight: 700; color: #1a365d;">{letter}</div>
        <div style="font-size: 12px; color: #666;">{count} Begriffe</div>
    </a>
</div>''')

        # Build category links
        cat_links = []
        for item in category_data:
            cat_name = item['category__name']
            cat_slug = item['category__slug']
            count = item['count']
            cat_links.append(f'''<li><a href="/kategorie-{cat_slug}/" style="color: #1a365d; text-decoration: none; font-weight: 500;">{cat_name}</a> ({count} Begriffe)</li>''')

        content = f'''
<div style="max-width: 1200px; margin: 0 auto; padding: 40px 20px;">

<h1 style="color: #1a365d; font-size: 42px; margin-bottom: 20px;">Glossar Facility Management</h1>
<p style="font-size: 18px; color: #666; line-height: 1.8; margin-bottom: 40px;">
Willkommen im umfassenden Glossar für professionelles Facility Management. Hier finden Sie über <strong>{total_terms} Fachbegriffe</strong> mit detaillierten Erklärungen aus den Bereichen Gebäudemanagement, Reinigung, Hausmeisterdienste, Energieeffizienz, Automatisierung und mehr.
</p>

<!-- Statistics -->
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px;">
    <div style="text-align: center; padding: 30px; background: #f7fafc; border-radius: 10px;">
        <div style="font-size: 36px; font-weight: 700; color: #1a365d;">{total_terms}+</div>
        <div style="color: #666;">Fachbegriffe</div>
    </div>
    <div style="text-align: center; padding: 30px; background: #f7fafc; border-radius: 10px;">
        <div style="font-size: 36px; font-weight: 700; color: #1a365d;">{len(letter_data)}</div>
        <div style="color: #666;">Buchstaben A-Z</div>
    </div>
    <div style="text-align: center; padding: 30px; background: #f7fafc; border-radius: 10px;">
        <div style="font-size: 36px; font-weight: 700; color: #1a365d;">{len(category_data)}</div>
        <div style="color: #666;">Kategorien</div>
    </div>
</div>

<!-- A-Z Navigation -->
<h2 style="color: #1a365d; margin-bottom: 20px;">Begriffe nach Buchstaben</h2>
<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 10px; margin-bottom: 40px;">
{''.join(az_links)}
</div>

<!-- Categories -->
<h2 style="color: #1a365d; margin-bottom: 20px;">Kategorien</h2>
<div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
<ul style="columns: 2; column-gap: 40px; list-style: none; padding: 0; margin: 0;">
{''.join(cat_links)}
</ul>
</div>

<!-- About Section -->
<div style="margin-top: 40px; padding: 30px; background: #edf2f7; border-radius: 10px;">
<h2 style="color: #1a365d; margin-top: 0;">Über dieses Glossar</h2>
<p style="line-height: 1.8; color: #333;">
Dieses Glossar wurde speziell für die professionelle Facility Management Branche in Deutschland entwickelt. Es enthält Fachbegriffe aus allen Bereichen des FM:
</p>
<ul style="line-height: 2; color: #333;">
<li><strong>Technisches FM:</strong> Gebäudetechnik, HVAC, Wärmepumpen, Energiemanagement</li>
<li><strong>Infrastrukturelles FM:</strong> Reinigung, Hausmeisterdienste, Sicherheit</li>
<li><strong>Kaufmännisches FM:</strong> Prozessoptimierung, Projektmanagement</li>
<li><strong>Zukunftsthemen:</strong> Automatisierung, Robotik, erneuerbare Energien</li>
</ul>
</div>

</div>
'''

        return self.create_or_update_page('glossar', 'Glossar Facility Management | Pro-FM', content)

    def create_letter_page(self, letter):
        """Create page for specific letter"""
        terms = GlossaryTerm.objects.filter(
            letter=letter,
            is_active=True
        ).select_related('category').order_by('term')

        if not terms:
            return None

        # Build term list
        terms_html = []
        for term in terms:
            category_name = term.category.name if term.category else 'Allgemein'
            preview = term.definition[:200] + '...' if len(term.definition) > 200 else term.definition
            terms_html.append(f'''
<div style="padding: 25px; background: white; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #1a365d;">
    <h3 style="margin-top: 0; color: #1a365d; font-size: 22px;">
        <a href="/{term.slug}/" style="color: #1a365d; text-decoration: none;">{term.term}</a>
    </h3>
    <p style="color: #666; line-height: 1.8;">{preview}</p>
    <div style="margin-top: 15px;">
        <span style="display: inline-block; padding: 4px 12px; background: #edf2f7; color: #1a365d; border-radius: 4px; font-size: 12px;">{category_name}</span>
    </div>
    <a href="/{term.slug}/" style="display: inline-block; margin-top: 10px; color: #1a365d; text-decoration: none; font-weight: 600;">Mehr lesen &rarr;</a>
</div>''')

        content = f'''
<div style="max-width: 1000px; margin: 0 auto; padding: 40px 20px;">

<h1 style="color: #1a365d; font-size: 42px;">Glossar Buchstabe {letter}</h1>
<p style="font-size: 18px; color: #666; margin-bottom: 30px;">
Fachbegriffe des Facility Managements mit dem Buchstaben <strong>{letter}</strong> ({terms.count()} Begriffe)
</p>

<p style="margin-bottom: 30px;">
<a href="/glossar/" style="display: inline-block; padding: 10px 20px; background: #1a365d; color: white; text-decoration: none; border-radius: 5px; font-weight: 600;">&larr; Zurück zum Glossar</a>
</p>

{''.join(terms_html)}

</div>
'''

        return self.create_or_update_page(
            f'glossar-{letter.lower()}',
            f'Glossar Buchstabe {letter} | Pro-FM',
            content
        )

    def create_category_page(self, category):
        """Create page for specific category"""
        terms = GlossaryTerm.objects.filter(
            category=category,
            is_active=True
        ).order_by('term')

        if not terms:
            return None

        # Build term list
        terms_html = []
        for term in terms:
            preview = term.definition[:150] + '...' if len(term.definition) > 150 else term.definition
            terms_html.append(f'''
<div style="padding: 20px; background: white; margin-bottom: 12px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #1a365d;">
    <h3 style="margin-top: 0; color: #1a365d; font-size: 20px;">
        <a href="/{term.slug}/" style="color: #1a365d; text-decoration: none;">{term.term}</a>
    </h3>
    <p style="color: #666; line-height: 1.6; font-size: 15px;">{preview}</p>
    <a href="/{term.slug}/" style="display: inline-block; margin-top: 8px; color: #1a365d; text-decoration: none; font-weight: 600; font-size: 14px;">Mehr lesen &rarr;</a>
</div>''')

        content = f'''
<div style="max-width: 1000px; margin: 0 auto; padding: 40px 20px;">

<h1 style="color: #1a365d; font-size: 42px;">Kategorie: {category.name}</h1>
<p style="font-size: 18px; color: #666; margin-bottom: 20px;">
{category.description}
</p>
<p style="font-size: 16px; color: #666; margin-bottom: 30px;">
<strong>{terms.count()} Begriffe</strong> in dieser Kategorie
</p>

<p style="margin-bottom: 30px;">
<a href="/glossar/" style="display: inline-block; padding: 10px 20px; background: #1a365d; color: white; text-decoration: none; border-radius: 5px; font-weight: 600;">&larr; Zurück zum Glossar</a>
</p>

{''.join(terms_html)}

</div>
'''

        return self.create_or_update_page(
            f'kategorie-{category.slug}',
            f'Kategorie {category.name} | Pro-FM Glossar',
            content
        )

    def create_term_page(self, term):
        """Create individual page for a term"""
        category_name = term.category.name if term.category else 'Allgemein'
        category_slug = term.category.slug if term.category else 'allgemein'

        # Build examples section
        examples_html = ''
        if term.examples:
            examples_html = f'''
<div style="background: #f7fafc; padding: 25px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #1a365d;">
    <h3 style="color: #1a365d; margin-top: 0;">Praxisbeispiel</h3>
    <p style="line-height: 1.8; color: #333;">{term.examples}</p>
</div>'''

        # Build synonyms section
        synonyms_html = ''
        if term.synonyms:
            synonyms_html = f'''
<div style="margin: 20px 0;">
    <h3 style="color: #1a365d;">Synonyme</h3>
    <p style="color: #666;">{term.synonyms}</p>
</div>'''

        # Build related terms section
        related_html = ''
        if term.related_terms:
            related_html = f'''
<div style="margin: 20px 0;">
    <h3 style="color: #1a365d;">Verwandte Begriffe</h3>
    <p style="color: #666;">{term.related_terms}</p>
</div>'''

        content = f'''
<div style="max-width: 900px; margin: 0 auto; padding: 40px 20px;">

<h1 style="color: #1a365d; font-size: 42px; margin-bottom: 20px;">{term.term}</h1>

<p style="margin-bottom: 25px;">
<a href="/glossar-{term.letter.lower()}/" style="display: inline-block; padding: 8px 16px; background: #edf2f7; color: #1a365d; text-decoration: none; border-radius: 5px; font-weight: 500; margin-right: 10px;">&larr; Buchstabe {term.letter}</a>
<a href="/glossar/" style="display: inline-block; padding: 8px 16px; background: #1a365d; color: white; text-decoration: none; border-radius: 5px; font-weight: 500;">&larr; Zum Glossar</a>
</p>

<div style="background: white; padding: 35px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

<div style="margin-bottom: 25px;">
    <a href="/kategorie-{category_slug}/" style="display: inline-block; padding: 8px 20px; background: #1a365d; color: white; border-radius: 5px; font-size: 14px; font-weight: 600; text-decoration: none;">{category_name}</a>
</div>

<h2 style="color: #1a365d;">Definition</h2>
<p style="font-size: 18px; line-height: 1.9; color: #333;">{term.definition}</p>

{examples_html}

{synonyms_html}

{related_html}

</div>

</div>
'''

        page_id = self.create_or_update_page(
            term.slug,
            f'{term.term} | Pro-FM Glossar',
            content
        )

        if page_id:
            term.wp_post_id = page_id
            term.is_published = True
            term.published_at = timezone.now()
            term.save(update_fields=['wp_post_id', 'is_published', 'published_at'])

        return page_id

    def sync_all(self, letter_filter=None):
        """Main sync function"""
        print("\n" + "="*60)
        print("PRO-FM GLOSSARY WORDPRESS SYNC")
        print("="*60)

        # Create sync log
        sync_log = GlossarySyncLog.objects.create(
            sync_type='full' if not letter_filter else 'letter',
            status='started'
        )

        try:
            # Statistics
            if letter_filter:
                terms_qs = GlossaryTerm.objects.filter(letter=letter_filter.upper(), is_active=True)
            else:
                terms_qs = GlossaryTerm.objects.filter(is_active=True)

            total_terms = terms_qs.count()
            sync_log.total_items = total_terms
            sync_log.save()

            print(f"\nTerms to sync: {total_terms}")

            # Step 1: Main glossary page
            print("\n1. Creating main glossary page...")
            self.create_main_glossary_page()

            # Step 2: Letter pages
            print("\n2. Creating letter pages...")
            if letter_filter:
                letters = [letter_filter.upper()]
            else:
                letters = terms_qs.values_list('letter', flat=True).distinct().order_by('letter')

            for letter in letters:
                self.create_letter_page(letter)
                time.sleep(0.3)

            # Step 3: Category pages
            print("\n3. Creating category pages...")
            categories = GlossaryCategory.objects.filter(is_active=True)
            for category in categories:
                self.create_category_page(category)
                time.sleep(0.3)

            # Step 4: Individual term pages
            print(f"\n4. Creating individual term pages ({total_terms} terms)...")
            synced = 0
            failed = 0

            for term in terms_qs:
                try:
                    page_id = self.create_term_page(term)
                    if page_id:
                        synced += 1
                    else:
                        failed += 1
                except Exception as e:
                    print(f"  Error: {term.term} - {e}")
                    failed += 1
                time.sleep(0.3)

            # Update sync log
            sync_log.synced_items = synced
            sync_log.failed_items = failed
            sync_log.status = 'success' if failed == 0 else 'partial'
            sync_log.completed_at = timezone.now()
            sync_log.save()

            # Summary
            print("\n" + "="*60)
            print("SYNC COMPLETE")
            print("="*60)
            print(f"Main glossary: {self.wp_site_url}/glossar/")
            print(f"Letter pages: {len(list(letters))} created")
            print(f"Category pages: {categories.count()} created")
            print(f"Term pages: {synced} synced, {failed} failed")

        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            raise


def main():
    parser = argparse.ArgumentParser(description="Sync Pro-FM Glossary to WordPress")
    parser.add_argument('--letter', type=str, help='Sync only specific letter (A-Z)')
    parser.add_argument('--main-only', action='store_true', help='Create main page only')
    parser.add_argument('--categories-only', action='store_true', help='Create category pages only')

    args = parser.parse_args()

    syncer = GlossaryWordPressSync()

    if args.main_only:
        syncer.create_main_glossary_page()
    elif args.categories_only:
        for category in GlossaryCategory.objects.filter(is_active=True):
            syncer.create_category_page(category)
    else:
        syncer.sync_all(letter_filter=args.letter)


if __name__ == "__main__":
    main()
