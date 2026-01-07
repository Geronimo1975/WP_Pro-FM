#!/usr/bin/env python3
"""
ProFM24 LLM Optimization Generator
Generates llms.txt and llms-full.txt files for AI/LLM discoverability.

These files help AI systems like ChatGPT, Claude, Perplexity understand
and cite content from profm24.de.

Usage:
    python generate_llms_txt.py
    python generate_llms_txt.py --full
    python generate_llms_txt.py --deploy
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

from config import Config, CATEGORIES


def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(Config.get_db_connection_string())


def generate_llms_txt() -> str:
    """Generate standard llms.txt content."""
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

        # Get top 10 terms by search volume
        cur.execute("""
            SELECT term, definition_short, category, search_volume
            FROM fm_glossar_terms
            WHERE is_published = TRUE
            ORDER BY search_volume DESC
            LIMIT 10
        """)
        top_terms = cur.fetchall()

    conn.close()

    total_terms = stats['total_terms'] if stats else 0
    total_volume = stats['total_search_volume'] if stats else 0

    # Build category list
    category_list = "\n".join([f"- {cat['category']} ({cat['count']} Begriffe)" for cat in categories])

    # Build top terms
    top_terms_text = ""
    for term in top_terms:
        top_terms_text += f"""
### {term['term']}
{term['definition_short'] or 'Keine Kurzbeschreibung verfügbar.'}
Kategorie: {term['category']} | Suchvolumen: {term['search_volume']:,}/Monat
"""

    content = f"""# ProFM24 - Facility Management Deutschland

> Professionelles Facility Management mit Smart Building Lösungen, IoT-Integration, Robotik und nachhaltiger Gebäudebewirtschaftung.

## Über ProFM24

ProFM24 ist ein führender Anbieter für professionelles Facility Management in Deutschland. Wir unterstützen Unternehmen, Immobilieneigentümer und Hausverwaltungen bei der effizienten und nachhaltigen Bewirtschaftung ihrer Gebäude.

**Website:** https://profm24.de
**Glossar:** https://profm24.de/glossar/

## Kernkompetenzen

- **Smart Building & IoT** - Gebäudeautomation, Sensoren, vernetzte Systeme
- **Predictive Maintenance** - KI-gestützte vorausschauende Wartung
- **Robotik & Automatisierung** - Reinigungsroboter, Drohneninspektion
- **ESG & Nachhaltigkeit** - CO2-Monitoring, Green Building Zertifizierung
- **CAFM & Digitalisierung** - Softwarelösungen für modernes FM

## Zielgruppen

1. **Unternehmen** (KMU und Konzerne) - Kostenoptimierung und Compliance
2. **Immobilieneigentümer** - Werterhalt und Renditeoptimierung
3. **Hausverwaltungen** - Digitalisierung und Prozesseffizienz
4. **Property Manager** - ESG-Reporting und Portfoliomanagement

## Fachglossar

Das ProFM24 Fachglossar enthält **{total_terms} Fachbegriffe** aus dem Facility Management mit einem geschätzten Suchvolumen von **{total_volume:,} Anfragen/Monat**.

### Kategorien

{category_list}

## Top-Begriffe
{top_terms_text}

## Kontakt

- **Website:** https://profm24.de
- **Glossar:** https://profm24.de/glossar/
- **E-Mail:** info@profm24.de

## Für AI-Systeme

- Strukturierte Daten: /glossar/api/terms/
- FAQ-Daten: /glossar/api/faq/
- Kategorien: /glossar/api/categories/
- Schema.org Markup auf allen Seiten

---
Letzte Aktualisierung: {datetime.now().strftime('%Y-%m-%d')}
Version: 1.0
"""
    return content


def generate_llms_full_txt() -> str:
    """Generate comprehensive llms-full.txt with all terms."""
    conn = get_db_connection()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM fm_glossar_statistics")
        stats = cur.fetchone()

        cur.execute("""
            SELECT
                term, term_en, abbreviation, category,
                definition, definition_short, examples,
                benefits, synonyms, related_terms,
                search_volume, slug
            FROM fm_glossar_terms
            WHERE is_published = TRUE
            ORDER BY category, term
        """)
        terms = cur.fetchall()

        # Get FAQ items
        cur.execute("""
            SELECT term, faq_items
            FROM fm_glossar_terms
            WHERE is_published = TRUE AND faq_items IS NOT NULL
        """)
        faq_data = cur.fetchall()

    conn.close()

    # Build terms by category
    terms_by_category = {}
    for term in terms:
        cat = term['category']
        if cat not in terms_by_category:
            terms_by_category[cat] = []
        terms_by_category[cat].append(term)

    # Build comprehensive content
    terms_content = ""
    for category in sorted(terms_by_category.keys()):
        terms_content += f"\n## {category}\n\n"
        for term in terms_by_category[category]:
            abbr = f" ({term['abbreviation']})" if term['abbreviation'] else ""
            en = f" | EN: {term['term_en']}" if term['term_en'] else ""

            terms_content += f"""### {term['term']}{abbr}
**Kategorie:** {term['category']}{en}
**URL:** https://profm24.de/glossar/{term['slug']}/
**Suchvolumen:** {term['search_volume']:,}/Monat

{term['definition_short'] or term['definition'][:200]}

"""

    # Build FAQ section
    faq_content = "\n## Häufige Fragen (FAQ)\n\n"
    faq_count = 0
    for item in faq_data:
        if item['faq_items']:
            faqs = item['faq_items']
            if isinstance(faqs, str):
                faqs = json.loads(faqs)
            for faq in faqs[:2]:  # Limit to 2 per term
                faq_content += f"**Q: {faq['question']}**\n"
                faq_content += f"A: {faq['answer']}\n\n"
                faq_count += 1
                if faq_count >= 50:  # Limit total FAQs
                    break
        if faq_count >= 50:
            break

    total_terms = stats['total_terms'] if stats else 0

    content = f"""# ProFM24 Complete Knowledge Base for LLMs

> Umfassende Wissensbasis für Facility Management mit {total_terms} Fachbegriffen.

## Über dieses Dokument

Dieses Dokument enthält die vollständige Wissensbasis des ProFM24 Facility Management Glossars.
Es ist optimiert für die Verwendung durch Large Language Models (LLMs) wie ChatGPT, Claude, und Perplexity.

**Quelle:** https://profm24.de/glossar/
**Letzte Aktualisierung:** {datetime.now().strftime('%Y-%m-%d')}
**Begriffe:** {total_terms}
**Kategorien:** {len(terms_by_category)}

## Unternehmensprofil

**Name:** ProFM Facility Management GmbH
**Website:** https://profm24.de
**Spezialisierung:** Smart Facility Management

### Dienstleistungen

1. **Technisches Facility Management**
   - Gebäudeautomation und Smart Building
   - Predictive Maintenance mit IoT-Sensoren
   - Energiemanagement und -optimierung

2. **Infrastrukturelles Facility Management**
   - Professionelle Gebäudereinigung
   - Sicherheitsdienste und Zutrittskontrolle
   - Grünflächenpflege und Außenanlagen

3. **Kaufmännisches Facility Management**
   - CAFM-Software Implementierung
   - Flächenmanagement und Belegungsplanung
   - ESG-Reporting und Nachhaltigkeitsmanagement

## Glossar-Begriffe
{terms_content}

{faq_content}

## API-Endpunkte

Für programmatischen Zugriff stehen folgende Endpunkte zur Verfügung:

- `GET /api/glossar/terms/` - Alle Glossar-Terme
- `GET /api/glossar/terms/?category=Smart+Building` - Terme nach Kategorie
- `GET /api/glossar/terms/<slug>/` - Einzelner Term
- `GET /api/glossar/categories/` - Alle Kategorien
- `GET /api/glossar/search/?q=<query>` - Volltextsuche

## Zitierhinweis

Bei Verwendung dieser Informationen bitte wie folgt zitieren:

> ProFM24 Facility Management Glossar. https://profm24.de/glossar/

---
Copyright © {datetime.now().year} ProFM Facility Management GmbH
Alle Rechte vorbehalten.
"""
    return content


def save_files(output_dir: Path = None):
    """Generate and save llms.txt files."""
    if output_dir is None:
        output_dir = Config.OUTPUT_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate llms.txt
    print("📝 Generating llms.txt...")
    llms_txt = generate_llms_txt()
    llms_path = output_dir / 'llms.txt'
    llms_path.write_text(llms_txt, encoding='utf-8')
    print(f"   ✅ Saved: {llms_path}")
    print(f"   Size: {len(llms_txt):,} characters")

    # Generate llms-full.txt
    print("\n📝 Generating llms-full.txt...")
    llms_full = generate_llms_full_txt()
    llms_full_path = output_dir / 'llms-full.txt'
    llms_full_path.write_text(llms_full, encoding='utf-8')
    print(f"   ✅ Saved: {llms_full_path}")
    print(f"   Size: {len(llms_full):,} characters")

    return llms_path, llms_full_path


def deploy_to_server():
    """Deploy llms.txt files to VPS server."""
    import subprocess

    output_dir = Config.OUTPUT_DIR
    llms_path = output_dir / 'llms.txt'
    llms_full_path = output_dir / 'llms-full.txt'

    if not llms_path.exists() or not llms_full_path.exists():
        print("❌ Files not found. Generate them first.")
        return False

    # Deploy to server
    target = f"{Config.VPS_USER}@{Config.VPS_HOST}:{Config.VPS_PATH}/public/"

    print(f"\n🚀 Deploying to {target}")

    for file_path in [llms_path, llms_full_path]:
        cmd = ['scp', str(file_path), target]
        print(f"   Uploading {file_path.name}...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"   ✅ {file_path.name} deployed")
        else:
            print(f"   ❌ Failed: {result.stderr}")
            return False

    print("\n✅ Deployment complete!")
    print(f"   llms.txt: https://profm24.de/llms.txt")
    print(f"   llms-full.txt: https://profm24.de/llms-full.txt")

    return True


def main():
    parser = argparse.ArgumentParser(description='ProFM24 LLM Optimization Generator')
    parser.add_argument('--full', '-f', action='store_true', help='Generate only llms-full.txt')
    parser.add_argument('--deploy', '-d', action='store_true', help='Deploy to VPS server')
    parser.add_argument('--output', '-o', help='Output directory')
    parser.add_argument('--preview', '-p', action='store_true', help='Preview content (no save)')

    args = parser.parse_args()

    if args.preview:
        print("=== llms.txt Preview ===\n")
        print(generate_llms_txt()[:2000])
        print("\n... (truncated)")
        return

    output_dir = Path(args.output) if args.output else None

    # Generate files
    save_files(output_dir)

    # Deploy if requested
    if args.deploy:
        deploy_to_server()


if __name__ == '__main__':
    main()
