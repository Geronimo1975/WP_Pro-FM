#!/usr/bin/env python3
"""
ProFM24 Glossary WordPress Sync
Synchronizes glossary terms to WordPress as pages with DIVI formatting.

Usage:
    python sync_to_wordpress.py --create-hub
    python sync_to_wordpress.py --create-letters
    python sync_to_wordpress.py --create-categories
    python sync_to_wordpress.py --create-terms --batch 50
    python sync_to_wordpress.py --all
"""

import argparse
import json
import time
import sys
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from requests.auth import HTTPBasicAuth

from config import Config, CATEGORIES

# WordPress API setup
WP_AUTH = HTTPBasicAuth(Config.WP_USERNAME, Config.WP_APP_PASSWORD)
WP_HEADERS = {'Content-Type': 'application/json'}


def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(Config.get_db_connection_string())


def wp_request(method: str, endpoint: str, data: dict = None) -> dict:
    """Make WordPress REST API request."""
    url = Config.get_wp_api_url(endpoint)

    try:
        if method == 'GET':
            response = requests.get(url, auth=WP_AUTH, headers=WP_HEADERS, params=data)
        elif method == 'POST':
            response = requests.post(url, auth=WP_AUTH, headers=WP_HEADERS, json=data)
        elif method == 'PUT':
            response = requests.put(url, auth=WP_AUTH, headers=WP_HEADERS, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"❌ WordPress API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text[:500]}")
        return None


def find_page_by_slug(slug: str) -> dict:
    """Find WordPress page by slug."""
    result = wp_request('GET', 'pages', {'slug': slug, 'per_page': 1})
    if result and len(result) > 0:
        return result[0]
    return None


def create_or_update_page(title: str, content: str, slug: str, parent_id: int = 0) -> dict:
    """Create or update WordPress page."""
    existing = find_page_by_slug(slug)

    data = {
        'title': title,
        'content': content,
        'slug': slug,
        'status': 'publish',
        'parent': parent_id
    }

    if existing:
        print(f"  📝 Updating existing page: {slug}")
        return wp_request('PUT', f"pages/{existing['id']}", data)
    else:
        print(f"  ➕ Creating new page: {slug}")
        return wp_request('POST', 'pages', data)


# ============================================================================
# DIVI CONTENT TEMPLATES
# ============================================================================

def generate_hub_page_content() -> str:
    """Generate main glossary hub page content."""
    conn = get_db_connection()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM fm_glossar_statistics")
        stats = cur.fetchone()

        cur.execute("""
            SELECT category, COUNT(*) as count
            FROM fm_glossar_terms
            WHERE is_published = TRUE
            GROUP BY category
            ORDER BY count DESC
        """)
        categories = cur.fetchall()

    conn.close()

    total_terms = stats['total_terms'] if stats else 0
    total_volume = stats['total_search_volume'] if stats else 0

    # Category list HTML
    category_list = ""
    for cat in categories:
        cat_slug = cat['category'].lower().replace(' ', '-').replace('&', 'und').replace('(', '').replace(')', '')
        category_list += f'''
        <li><a href="/glossar/kategorie/{cat_slug}/">{cat['category']}</a> ({cat['count']} Begriffe)</li>'''

    # A-Z Grid
    az_grid = ""
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        az_grid += f'''
        <a href="/glossar/{letter.lower()}/" class="letter-link" style="display:inline-block;width:40px;height:40px;line-height:40px;text-align:center;margin:5px;background:#0066CC;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;">{letter}</a>'''

    content = f'''[et_pb_section fb_built="1" _builder_version="4.21.0" background_color="#f8f9fa"]
[et_pb_row _builder_version="4.21.0"]
[et_pb_column type="4_4" _builder_version="4.21.0"]

[et_pb_text _builder_version="4.21.0"]
<h1 style="text-align:center;color:#0066CC;">Facility Management Glossar</h1>
<p style="text-align:center;font-size:18px;max-width:800px;margin:0 auto 30px;">
Das umfassende Fachglossar für professionelles Facility Management. Über <strong>{total_terms} Fachbegriffe</strong> zu Smart Building, IoT, Robotik, Nachhaltigkeit und digitaler Gebäudebewirtschaftung.
</p>
[/et_pb_text]

[/et_pb_column]
[/et_pb_row]

[et_pb_row column_structure="1_4,1_4,1_4,1_4" _builder_version="4.21.0"]
[et_pb_column type="1_4" _builder_version="4.21.0"]
[et_pb_blurb title="{total_terms}+" use_icon="on" font_icon="%%72%%" icon_color="#0066CC" _builder_version="4.21.0"]
<p style="text-align:center;">Fachbegriffe</p>
[/et_pb_blurb]
[/et_pb_column]
[et_pb_column type="1_4" _builder_version="4.21.0"]
[et_pb_blurb title="15" use_icon="on" font_icon="%%141%%" icon_color="#00AA55" _builder_version="4.21.0"]
<p style="text-align:center;">Kategorien</p>
[/et_pb_blurb]
[/et_pb_column]
[et_pb_column type="1_4" _builder_version="4.21.0"]
[et_pb_blurb title="A-Z" use_icon="on" font_icon="%%259%%" icon_color="#FF6600" _builder_version="4.21.0"]
<p style="text-align:center;">Alphabetisch</p>
[/et_pb_blurb]
[/et_pb_column]
[et_pb_column type="1_4" _builder_version="4.21.0"]
[et_pb_blurb title="{total_volume:,}" use_icon="on" font_icon="%%101%%" icon_color="#9933FF" _builder_version="4.21.0"]
<p style="text-align:center;">Suchanfragen/Monat</p>
[/et_pb_blurb]
[/et_pb_column]
[/et_pb_row]

[et_pb_row _builder_version="4.21.0"]
[et_pb_column type="4_4" _builder_version="4.21.0"]
[et_pb_text _builder_version="4.21.0"]
<h2 style="text-align:center;">Alphabetische Navigation</h2>
<div style="text-align:center;margin:30px 0;">
{az_grid}
</div>
[/et_pb_text]
[/et_pb_column]
[/et_pb_row]

[et_pb_row _builder_version="4.21.0"]
[et_pb_column type="4_4" _builder_version="4.21.0"]
[et_pb_text _builder_version="4.21.0"]
<h2 style="text-align:center;">Kategorien</h2>
<div style="max-width:800px;margin:0 auto;">
<ul style="column-count:2;column-gap:40px;list-style:none;padding:0;">
{category_list}
</ul>
</div>
[/et_pb_text]
[/et_pb_column]
[/et_pb_row]

[et_pb_row _builder_version="4.21.0"]
[et_pb_column type="4_4" _builder_version="4.21.0"]
[et_pb_cta title="Professionelles Facility Management" button_url="/kontakt/" button_text="Jetzt beraten lassen" _builder_version="4.21.0" background_color="#0066CC"]
ProFM24 bietet Ihnen professionelle Facility Management Lösungen mit modernster Technologie. Kontaktieren Sie uns für eine unverbindliche Beratung.
[/et_pb_cta]
[/et_pb_column]
[/et_pb_row]

[/et_pb_section]'''

    return content


def generate_letter_page_content(letter: str) -> str:
    """Generate letter page content."""
    conn = get_db_connection()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT term, slug, definition_short, category
            FROM fm_glossar_terms
            WHERE letter = %s AND is_published = TRUE
            ORDER BY term
        """, (letter,))
        terms = cur.fetchall()

    conn.close()

    # Terms list HTML
    terms_html = ""
    for term in terms:
        terms_html += f'''
<div style="background:#fff;padding:20px;margin:15px 0;border-radius:8px;box-shadow:0 2px 5px rgba(0,0,0,0.1);">
    <h3 style="margin:0 0 10px;"><a href="/glossar/{term['slug']}/" style="color:#0066CC;text-decoration:none;">{term['term']}</a></h3>
    <p style="margin:0 0 10px;color:#666;font-size:14px;">{term['category']}</p>
    <p style="margin:0;">{term['definition_short'] or ''}</p>
    <a href="/glossar/{term['slug']}/" style="color:#0066CC;font-weight:bold;">Mehr erfahren →</a>
</div>'''

    if not terms:
        terms_html = '<p style="text-align:center;color:#666;">Keine Begriffe für diesen Buchstaben gefunden.</p>'

    # A-Z Navigation
    az_nav = ""
    for l in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        active_style = "background:#0066CC;color:#fff;" if l == letter else "background:#e0e0e0;color:#333;"
        az_nav += f'<a href="/glossar/{l.lower()}/" style="display:inline-block;width:35px;height:35px;line-height:35px;text-align:center;margin:3px;{active_style}text-decoration:none;border-radius:5px;font-weight:bold;">{l}</a>'

    content = f'''[et_pb_section fb_built="1" _builder_version="4.21.0" background_color="#f8f9fa"]
[et_pb_row _builder_version="4.21.0"]
[et_pb_column type="4_4" _builder_version="4.21.0"]

[et_pb_text _builder_version="4.21.0"]
<nav style="margin-bottom:20px;">
    <a href="/glossar/" style="color:#0066CC;">← Zurück zum Glossar</a>
</nav>
<h1 style="text-align:center;color:#0066CC;">Glossar: Buchstabe {letter}</h1>
<p style="text-align:center;font-size:16px;color:#666;">{len(terms)} Fachbegriffe</p>
[/et_pb_text]

[et_pb_text _builder_version="4.21.0"]
<div style="text-align:center;margin:20px 0;">
{az_nav}
</div>
[/et_pb_text]

[et_pb_text _builder_version="4.21.0"]
{terms_html}
[/et_pb_text]

[/et_pb_column]
[/et_pb_row]
[/et_pb_section]'''

    return content


def generate_category_page_content(category: str) -> str:
    """Generate category page content."""
    conn = get_db_connection()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT term, slug, definition_short, letter
            FROM fm_glossar_terms
            WHERE category = %s AND is_published = TRUE
            ORDER BY term
        """, (category,))
        terms = cur.fetchall()

    conn.close()

    # Terms list HTML
    terms_html = ""
    current_letter = None
    for term in terms:
        if term['letter'] != current_letter:
            if current_letter:
                terms_html += '</div>'
            current_letter = term['letter']
            terms_html += f'<h3 style="margin-top:30px;color:#0066CC;border-bottom:2px solid #0066CC;padding-bottom:5px;">{current_letter}</h3><div>'

        terms_html += f'''
<div style="background:#fff;padding:15px;margin:10px 0;border-radius:5px;border-left:4px solid #0066CC;">
    <a href="/glossar/{term['slug']}/" style="color:#333;text-decoration:none;font-weight:bold;">{term['term']}</a>
    <p style="margin:5px 0 0;font-size:14px;color:#666;">{term['definition_short'] or ''}</p>
</div>'''

    if current_letter:
        terms_html += '</div>'

    content = f'''[et_pb_section fb_built="1" _builder_version="4.21.0" background_color="#f8f9fa"]
[et_pb_row _builder_version="4.21.0"]
[et_pb_column type="4_4" _builder_version="4.21.0"]

[et_pb_text _builder_version="4.21.0"]
<nav style="margin-bottom:20px;">
    <a href="/glossar/" style="color:#0066CC;">← Zurück zum Glossar</a>
</nav>
<h1 style="text-align:center;color:#0066CC;">{category}</h1>
<p style="text-align:center;font-size:16px;color:#666;">{len(terms)} Fachbegriffe in dieser Kategorie</p>
[/et_pb_text]

[et_pb_text _builder_version="4.21.0"]
{terms_html}
[/et_pb_text]

[et_pb_cta title="Beratung zu {category}" button_url="/kontakt/" button_text="Kontakt aufnehmen" _builder_version="4.21.0" background_color="#0066CC"]
Benötigen Sie Unterstützung im Bereich {category}? Unsere Experten beraten Sie gerne.
[/et_pb_cta]

[/et_pb_column]
[/et_pb_row]
[/et_pb_section]'''

    return content


def generate_term_page_content(term: dict) -> str:
    """Generate individual term page content."""
    # Parse FAQ items
    faq_html = ""
    faq_items = term.get('faq_items')
    if faq_items:
        if isinstance(faq_items, str):
            faq_items = json.loads(faq_items)
        for faq in faq_items:
            faq_html += f'''
[et_pb_accordion_item title="{faq['question']}" open="off" _builder_version="4.21.0"]
{faq['answer']}
[/et_pb_accordion_item]'''

    # Related terms links
    related_html = ""
    if term.get('related_terms'):
        related_list = [t.strip() for t in term['related_terms'].split(',')]
        for rt in related_list[:5]:
            rt_slug = rt.lower().replace(' ', '-').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
            related_html += f'<li><a href="/glossar/{rt_slug}/">{rt}</a></li>'

    # Synonyms
    synonyms_html = ""
    if term.get('synonyms'):
        synonyms_html = f"<p><strong>Synonyme:</strong> {term['synonyms']}</p>"

    # Benefits list
    benefits_html = ""
    if term.get('benefits'):
        benefits_list = term['benefits'].split(',')
        for benefit in benefits_list:
            benefits_html += f"<li>{benefit.strip()}</li>"

    # Abbreviation display
    abbr = f" ({term['abbreviation']})" if term.get('abbreviation') else ""

    content = f'''[et_pb_section fb_built="1" _builder_version="4.21.0" background_color="#f8f9fa"]
[et_pb_row _builder_version="4.21.0"]
[et_pb_column type="4_4" _builder_version="4.21.0"]

[et_pb_text _builder_version="4.21.0"]
<nav style="margin-bottom:20px;font-size:14px;">
    <a href="/glossar/" style="color:#0066CC;">Glossar</a> ›
    <a href="/glossar/{term['letter'].lower()}/" style="color:#0066CC;">{term['letter']}</a> ›
    <span>{term['term']}</span>
</nav>
[/et_pb_text]

[et_pb_text _builder_version="4.21.0"]
<h1 style="color:#0066CC;margin-bottom:10px;">{term['term']}{abbr}</h1>
<p style="color:#666;font-size:14px;margin-bottom:20px;">
    <span style="background:#e3f2fd;padding:3px 10px;border-radius:15px;">{term['category']}</span>
    <span style="margin-left:10px;">{term.get('difficulty_level', 'intermediate').title()}</span>
</p>
[/et_pb_text]

[et_pb_blurb title="Definition" use_icon="on" font_icon="%%45%%" icon_color="#0066CC" _builder_version="4.21.0" background_color="#e3f2fd" custom_padding="20px|20px|20px|20px"]
<p style="font-size:16px;line-height:1.7;">{term['definition']}</p>
{synonyms_html}
[/et_pb_blurb]

[/et_pb_column]
[/et_pb_row]

[et_pb_row _builder_version="4.21.0"]
[et_pb_column type="4_4" _builder_version="4.21.0"]

[et_pb_text _builder_version="4.21.0"]
<h2>Praxisbeispiel</h2>
<div style="background:#fff;padding:20px;border-left:4px solid #00AA55;margin:20px 0;">
{term.get('examples', '')}
</div>
[/et_pb_text]

[et_pb_text _builder_version="4.21.0"]
<h2>Anwendungsbereiche</h2>
<p>{term.get('use_cases', '')}</p>
[/et_pb_text]

[et_pb_text _builder_version="4.21.0"]
<h2>Vorteile für Ihr Unternehmen</h2>
<ul style="list-style:none;padding:0;">
{benefits_html}
</ul>
[/et_pb_text]

[/et_pb_column]
[/et_pb_row]

[et_pb_row _builder_version="4.21.0" background_color="#e3f2fd" custom_padding="20px|20px|20px|20px" border_radii="on|8px|8px|8px|8px"]
[et_pb_column type="4_4" _builder_version="4.21.0"]
[et_pb_text _builder_version="4.21.0"]
<h3 style="margin-top:0;">🔗 Verwandte Fachbegriffe</h3>
<ul>
{related_html}
</ul>
[/et_pb_text]
[/et_pb_column]
[/et_pb_row]

[et_pb_row _builder_version="4.21.0"]
[et_pb_column type="4_4" _builder_version="4.21.0"]
[et_pb_text _builder_version="4.21.0"]
<h2>Häufige Fragen zu {term['term']}</h2>
[/et_pb_text]
[et_pb_accordion _builder_version="4.21.0"]
{faq_html}
[/et_pb_accordion]
[/et_pb_column]
[/et_pb_row]

[et_pb_row _builder_version="4.21.0"]
[et_pb_column type="4_4" _builder_version="4.21.0"]
[et_pb_cta title="{term['term']} mit ProFM24" button_url="/kontakt/" button_text="Jetzt beraten lassen" _builder_version="4.21.0" background_color="#0066CC"]
ProFM24 unterstützt Sie bei der Implementierung von {term['term']} in Ihrem Gebäudemanagement. Profitieren Sie von unserer Expertise.
[/et_pb_cta]
[/et_pb_column]
[/et_pb_row]

[/et_pb_section]'''

    return content


# ============================================================================
# SYNC FUNCTIONS
# ============================================================================

def create_hub_page():
    """Create or update main glossary hub page."""
    print("\n📚 Creating Glossary Hub Page...")

    content = generate_hub_page_content()
    result = create_or_update_page(
        title="Facility Management Glossar",
        content=content,
        slug="glossar"
    )

    if result:
        print(f"  ✅ Hub page created/updated: ID {result['id']}")
        return result['id']
    return None


def create_letter_pages(hub_id: int = 0):
    """Create pages for each letter A-Z."""
    print("\n🔤 Creating Letter Pages...")

    created = 0
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        content = generate_letter_page_content(letter)
        result = create_or_update_page(
            title=f"Glossar: Buchstabe {letter}",
            content=content,
            slug=f"glossar-{letter.lower()}",
            parent_id=hub_id
        )

        if result:
            created += 1
            print(f"  ✅ Letter {letter}: ID {result['id']}")

        time.sleep(0.5)  # Rate limiting

    print(f"\n✅ Created {created}/26 letter pages")
    return created


def create_category_pages(hub_id: int = 0):
    """Create pages for each category."""
    print("\n📁 Creating Category Pages...")

    created = 0
    for category in CATEGORIES:
        cat_slug = category.lower().replace(' ', '-').replace('&', 'und').replace('(', '').replace(')', '')

        content = generate_category_page_content(category)
        result = create_or_update_page(
            title=f"Glossar: {category}",
            content=content,
            slug=f"glossar-kategorie-{cat_slug}",
            parent_id=hub_id
        )

        if result:
            created += 1
            print(f"  ✅ {category}: ID {result['id']}")

        time.sleep(0.5)

    print(f"\n✅ Created {created}/{len(CATEGORIES)} category pages")
    return created


def create_term_pages(batch_size: int = 50, offset: int = 0):
    """Create individual term pages."""
    print(f"\n📄 Creating Term Pages (batch {batch_size}, offset {offset})...")

    conn = get_db_connection()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT * FROM fm_glossar_terms
            WHERE is_published = TRUE AND wordpress_post_id IS NULL
            ORDER BY priority, search_volume DESC
            LIMIT %s OFFSET %s
        """, (batch_size, offset))
        terms = cur.fetchall()

    if not terms:
        print("  No terms to sync")
        conn.close()
        return 0

    created = 0
    for term in terms:
        content = generate_term_page_content(term)
        result = create_or_update_page(
            title=term['term'],
            content=content,
            slug=f"glossar-{term['slug']}"
        )

        if result:
            # Update database with WordPress ID
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE fm_glossar_terms
                    SET wordpress_post_id = %s, published_at = NOW()
                    WHERE id = %s
                """, (result['id'], term['id']))
                conn.commit()

            created += 1
            print(f"  ✅ {term['term']}: WP ID {result['id']}")

        time.sleep(1.0)  # Rate limiting for terms

    conn.close()
    print(f"\n✅ Created {created}/{len(terms)} term pages")
    return created


def sync_all():
    """Full sync: hub, letters, categories, and all terms."""
    print("\n🚀 FULL GLOSSARY SYNC")
    print("="*60)

    # Publish all terms first
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("UPDATE fm_glossar_terms SET is_published = TRUE WHERE definition IS NOT NULL AND LENGTH(definition) >= 200")
        conn.commit()
    conn.close()

    # Create hub
    hub_id = create_hub_page() or 0

    # Create structure
    create_letter_pages(hub_id)
    create_category_pages(hub_id)

    # Create all terms in batches
    offset = 0
    total_created = 0
    while True:
        created = create_term_pages(batch_size=50, offset=0)  # Always offset 0 since we filter by wordpress_post_id IS NULL
        if created == 0:
            break
        total_created += created

        print(f"\n📊 Progress: {total_created} terms synced")
        print("Taking a 10 second break...")
        time.sleep(10)

    print("\n" + "="*60)
    print(f"✅ SYNC COMPLETE: {total_created} terms synced to WordPress")
    print("="*60)


def show_sync_status():
    """Show current sync status."""
    conn = get_db_connection()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_published) as published,
                COUNT(*) FILTER (WHERE wordpress_post_id IS NOT NULL) as synced
            FROM fm_glossar_terms
        """)
        stats = cur.fetchone()

    conn.close()

    print("\n📊 SYNC STATUS")
    print("="*40)
    print(f"Total terms:     {stats['total']}")
    print(f"Published:       {stats['published']}")
    print(f"Synced to WP:    {stats['synced']}")
    print(f"Pending sync:    {stats['published'] - stats['synced']}")
    print("="*40)


def main():
    parser = argparse.ArgumentParser(description='ProFM24 Glossary WordPress Sync')
    parser.add_argument('--create-hub', action='store_true', help='Create/update hub page')
    parser.add_argument('--create-letters', action='store_true', help='Create letter pages')
    parser.add_argument('--create-categories', action='store_true', help='Create category pages')
    parser.add_argument('--create-terms', action='store_true', help='Create term pages')
    parser.add_argument('--batch', type=int, default=50, help='Batch size for terms')
    parser.add_argument('--offset', type=int, default=0, help='Offset for terms')
    parser.add_argument('--all', action='store_true', help='Full sync')
    parser.add_argument('--status', action='store_true', help='Show sync status')
    parser.add_argument('--test', action='store_true', help='Test WordPress connection')

    args = parser.parse_args()

    if args.test:
        print("🧪 Testing WordPress connection...")
        result = wp_request('GET', 'pages', {'per_page': 1})
        if result is not None:
            print("✅ WordPress connection successful!")
        else:
            print("❌ WordPress connection failed")
        return

    if args.status:
        show_sync_status()
        return

    if args.all:
        sync_all()
        return

    if args.create_hub:
        create_hub_page()

    if args.create_letters:
        create_letter_pages()

    if args.create_categories:
        create_category_pages()

    if args.create_terms:
        create_term_pages(args.batch, args.offset)

    if not any([args.create_hub, args.create_letters, args.create_categories, args.create_terms, args.all]):
        parser.print_help()


if __name__ == '__main__':
    main()
