#!/usr/bin/env python3
"""
ProFM24 RankMath SEO Optimizer
Optimizes glossary term pages for maximum RankMath scores.

Features:
- Content enrichment to 600+ words
- Focus keyword optimization
- Meta title and description
- FAQ schema integration
- Internal linking recommendations

Usage:
    python fix_rankmath_seo.py --term-id 123
    python fix_rankmath_seo.py --all
    python fix_rankmath_seo.py --category "Smart Building & IoT"
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
from openai import OpenAI

from config import Config, CATEGORIES

# Initialize clients
client = OpenAI(api_key=Config.OPENAI_API_KEY)
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
        return None


ENRICHMENT_PROMPT = """Du bist ein SEO-Experte für Facility Management Content.
Erstelle erweiterten Content für den Glossar-Begriff "{term}" für maximale RankMath SEO-Scores.

BESTEHENDE INFORMATIONEN:
- Begriff: {term}
- Kategorie: {category}
- Definition: {definition}
- Beispiele: {examples}
- Vorteile: {benefits}
- Verwandte Begriffe: {related_terms}

ANFORDERUNGEN:
1. Gesamtlänge: 600-800 Wörter (KRITISCH für RankMath!)
2. Focus Keyword "{term}" muss erscheinen:
   - Im ersten Absatz (wichtig!)
   - In mindestens einer H2-Überschrift
   - 5-7x natürlich im Text (ca. 1% Dichte)
3. Struktur mit H2-Überschriften
4. Praktischer Nutzen für Zielgruppe

ZIELGRUPPE:
- Unternehmen und Facility Manager
- Immobilieneigentümer
- Hausverwaltungen

AUSGABE-FORMAT (JSON):
{{
  "enriched_content": "HTML-formatierter Content mit H2, H3, Listen, etc. (600-800 Wörter)",

  "meta_title": "SEO-Titel max 60 Zeichen, mit {term} am Anfang",

  "meta_description": "Meta-Beschreibung max 160 Zeichen, mit {term}, Call-to-Action",

  "focus_keyword": "{term}",

  "secondary_keywords": ["keyword1", "keyword2", "keyword3"],

  "faq_schema": [
    {{"question": "Was ist {term}?", "answer": "Detaillierte Antwort 2-3 Sätze"}},
    {{"question": "Welche Vorteile bietet {term}?", "answer": "Antwort mit Vorteilen"}},
    {{"question": "Was kostet {term}?", "answer": "Realistische Kosteneinschätzung"}},
    {{"question": "Wie implementiert man {term}?", "answer": "Praktische Schritte"}}
  ],

  "internal_link_suggestions": [
    {{"anchor": "Ankertext", "target_term": "Verwandter Begriff"}}
  ],

  "word_count": 650
}}

CONTENT-STRUKTUR:
1. Einleitung (80-100 Wörter) - {term} im ersten Satz!
2. H2: Was ist {term}? (100-150 Wörter)
3. H2: Vorteile von {term} für Unternehmen (100-120 Wörter)
4. H2: {term} in der Praxis (100-120 Wörter)
5. H2: Implementierung und Best Practices (80-100 Wörter)
6. H2: {term} mit ProFM24 (60-80 Wörter)
7. FAQ-Sektion wird separat generiert

Antworte NUR mit dem JSON-Objekt."""


def generate_enriched_content(term: dict) -> dict:
    """Generate SEO-enriched content using GPT-4o."""
    prompt = ENRICHMENT_PROMPT.format(
        term=term['term'],
        category=term['category'],
        definition=term.get('definition', ''),
        examples=term.get('examples', ''),
        benefits=term.get('benefits', ''),
        related_terms=term.get('related_terms', '')
    )

    response = client.chat.completions.create(
        model=Config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "Du bist ein SEO-Experte für technischen B2B-Content im Facility Management Bereich."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2500
    )

    content = response.choices[0].message.content.strip()

    # Extract JSON
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    return json.loads(content.strip())


def build_seo_page_content(term: dict, enriched: dict) -> str:
    """Build complete page content with SEO optimization."""
    # FAQ HTML
    faq_html = ""
    faq_schema = enriched.get('faq_schema', [])
    for faq in faq_schema:
        faq_html += f'''
<div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question" style="background:#f8f9fa;padding:15px;margin:10px 0;border-radius:5px;">
    <h3 itemprop="name" style="margin:0 0 10px;color:#0066CC;">{faq['question']}</h3>
    <div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
        <p itemprop="text" style="margin:0;">{faq['answer']}</p>
    </div>
</div>'''

    # Related terms from suggestions
    related_html = ""
    suggestions = enriched.get('internal_link_suggestions', [])
    for link in suggestions[:5]:
        target_slug = link['target_term'].lower().replace(' ', '-').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
        related_html += f'<li><a href="/glossar/{target_slug}/">{link["anchor"]}</a></li>'

    # Build DIVI content
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
    <span style="margin-left:10px;">Suchvolumen: {term.get('search_volume', 0):,}/Monat</span>
</p>
[/et_pb_text]

[et_pb_text _builder_version="4.21.0"]
{enriched['enriched_content']}
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
<div itemscope itemtype="https://schema.org/FAQPage">
{faq_html}
</div>
[/et_pb_text]
[/et_pb_column]
[/et_pb_row]

[et_pb_row _builder_version="4.21.0"]
[et_pb_column type="4_4" _builder_version="4.21.0"]
[et_pb_cta title="{term['term']} mit ProFM24" button_url="/kontakt/" button_text="Kostenlose Beratung" _builder_version="4.21.0" background_color="#0066CC"]
ProFM24 ist Ihr Partner für professionelles Facility Management. Profitieren Sie von unserer Expertise bei {term['term']} und anderen Smart Building Lösungen.
[/et_pb_cta]
[/et_pb_column]
[/et_pb_row]

[/et_pb_section]'''

    return content


def update_wordpress_seo(wp_id: int, content: str, enriched: dict, term: dict) -> bool:
    """Update WordPress page with SEO-optimized content."""
    # Prepare RankMath meta
    data = {
        'content': content,
        'meta': {
            'rank_math_focus_keyword': enriched['focus_keyword'],
            'rank_math_title': enriched['meta_title'],
            'rank_math_description': enriched['meta_description'],
            'rank_math_robots': ['index', 'follow']
        }
    }

    result = wp_request('PUT', f'pages/{wp_id}', data)
    return result is not None


def optimize_term(term_id: int, dry_run: bool = False) -> bool:
    """Optimize a single term."""
    conn = get_db_connection()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM fm_glossar_terms WHERE id = %s", (term_id,))
        term = cur.fetchone()

    if not term:
        print(f"❌ Term ID {term_id} not found")
        conn.close()
        return False

    if not term.get('wordpress_post_id'):
        print(f"❌ Term '{term['term']}' not synced to WordPress")
        conn.close()
        return False

    print(f"\n🔧 Optimizing: {term['term']}")
    print(f"   WordPress ID: {term['wordpress_post_id']}")
    print(f"   Category: {term['category']}")

    try:
        # Generate enriched content
        print("   Generating enriched content...")
        enriched = generate_enriched_content(term)

        print(f"   ✓ Word count: {enriched.get('word_count', 'N/A')}")
        print(f"   ✓ Meta title: {enriched['meta_title'][:50]}...")
        print(f"   ✓ Focus keyword: {enriched['focus_keyword']}")

        if dry_run:
            print("   [DRY RUN] Would update WordPress")
            conn.close()
            return True

        # Build page content
        page_content = build_seo_page_content(term, enriched)

        # Update WordPress
        print("   Updating WordPress...")
        success = update_wordpress_seo(
            term['wordpress_post_id'],
            page_content,
            enriched,
            term
        )

        if success:
            # Update database
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE fm_glossar_terms
                    SET
                        meta_title = %s,
                        meta_description = %s,
                        focus_keyword = %s,
                        secondary_keywords = %s,
                        faq_items = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    enriched['meta_title'],
                    enriched['meta_description'],
                    enriched['focus_keyword'],
                    json.dumps(enriched.get('secondary_keywords', []), ensure_ascii=False),
                    json.dumps(enriched.get('faq_schema', []), ensure_ascii=False),
                    term_id
                ))
                conn.commit()

            print(f"   ✅ Optimization complete!")
        else:
            print(f"   ❌ WordPress update failed")

        conn.close()
        return success

    except Exception as e:
        print(f"   ❌ Error: {e}")
        conn.close()
        return False


def optimize_all(limit: int = None, delay: float = 2.0, dry_run: bool = False):
    """Optimize all terms."""
    conn = get_db_connection()

    query = """
        SELECT id, term FROM fm_glossar_terms
        WHERE wordpress_post_id IS NOT NULL
        ORDER BY priority, search_volume DESC
    """
    if limit:
        query += f" LIMIT {limit}"

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        terms = cur.fetchall()

    conn.close()

    print(f"\n🚀 BATCH SEO OPTIMIZATION")
    print(f"   Terms to optimize: {len(terms)}")
    print(f"   Delay between terms: {delay}s")
    print(f"   Dry run: {dry_run}")
    print("="*50)

    optimized = 0
    failed = 0

    for i, term in enumerate(terms):
        print(f"\n[{i+1}/{len(terms)}] Processing...")

        success = optimize_term(term['id'], dry_run)

        if success:
            optimized += 1
        else:
            failed += 1

        # Progress checkpoint
        if (i + 1) % 10 == 0:
            print(f"\n📊 Progress: {optimized} optimized, {failed} failed")

        # Break every 50 terms
        if (i + 1) % 50 == 0 and i + 1 < len(terms):
            print(f"\n⏸️  Taking a 30 second break...")
            time.sleep(30)
        else:
            time.sleep(delay)

    print("\n" + "="*50)
    print(f"✅ OPTIMIZATION COMPLETE")
    print(f"   Optimized: {optimized}")
    print(f"   Failed: {failed}")
    print("="*50)


def optimize_category(category: str, dry_run: bool = False):
    """Optimize all terms in a category."""
    conn = get_db_connection()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT id, term FROM fm_glossar_terms
            WHERE category = %s AND wordpress_post_id IS NOT NULL
            ORDER BY priority, search_volume DESC
        """, (category,))
        terms = cur.fetchall()

    conn.close()

    print(f"\n📁 Optimizing category: {category}")
    print(f"   Terms: {len(terms)}")

    for i, term in enumerate(terms):
        print(f"\n[{i+1}/{len(terms)}]")
        optimize_term(term['id'], dry_run)
        time.sleep(2.0)


def analyze_seo_status():
    """Analyze current SEO status of glossary."""
    conn = get_db_connection()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Overall stats
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE wordpress_post_id IS NOT NULL) as synced,
                COUNT(*) FILTER (WHERE meta_title IS NOT NULL) as has_meta_title,
                COUNT(*) FILTER (WHERE focus_keyword IS NOT NULL) as has_focus_keyword,
                COUNT(*) FILTER (WHERE LENGTH(definition) >= 300) as good_definition
            FROM fm_glossar_terms
        """)
        stats = cur.fetchone()

        # Category breakdown
        cur.execute("""
            SELECT
                category,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE wordpress_post_id IS NOT NULL) as synced,
                COUNT(*) FILTER (WHERE focus_keyword IS NOT NULL) as optimized
            FROM fm_glossar_terms
            GROUP BY category
            ORDER BY total DESC
        """)
        categories = cur.fetchall()

    conn.close()

    print("\n📊 SEO STATUS ANALYSIS")
    print("="*60)
    print(f"\nOverall:")
    print(f"  Total terms:        {stats['total']}")
    print(f"  Synced to WP:       {stats['synced']}")
    print(f"  Has meta title:     {stats['has_meta_title']}")
    print(f"  Has focus keyword:  {stats['has_focus_keyword']}")
    print(f"  Good definition:    {stats['good_definition']} (300+ chars)")

    print(f"\nBy Category:")
    print("-"*60)
    for cat in categories:
        pct = (cat['optimized'] / cat['total'] * 100) if cat['total'] > 0 else 0
        bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
        print(f"  {cat['category'][:30]:30} {cat['optimized']:3}/{cat['total']:3} {bar} {pct:.0f}%")

    print("="*60)


def main():
    parser = argparse.ArgumentParser(description='ProFM24 RankMath SEO Optimizer')
    parser.add_argument('--term-id', '-t', type=int, help='Optimize specific term by ID')
    parser.add_argument('--all', '-a', action='store_true', help='Optimize all terms')
    parser.add_argument('--category', '-c', help='Optimize all terms in category')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of terms')
    parser.add_argument('--delay', '-d', type=float, default=2.0, help='Delay between terms (seconds)')
    parser.add_argument('--dry-run', action='store_true', help='Generate content but don\'t update WordPress')
    parser.add_argument('--status', '-s', action='store_true', help='Show SEO status analysis')

    args = parser.parse_args()

    if args.status:
        analyze_seo_status()
        return

    if args.term_id:
        optimize_term(args.term_id, args.dry_run)
        return

    if args.category:
        if args.category not in CATEGORIES:
            print(f"❌ Invalid category: {args.category}")
            print(f"   Valid categories: {', '.join(CATEGORIES)}")
            return
        optimize_category(args.category, args.dry_run)
        return

    if args.all:
        optimize_all(args.limit, args.delay, args.dry_run)
        return

    parser.print_help()


if __name__ == '__main__':
    main()
