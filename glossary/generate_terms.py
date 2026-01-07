#!/usr/bin/env python3
"""
ProFM24 Glossary Term Generator
Generates Facility Management glossary terms using OpenAI GPT-4o.

Usage:
    python generate_terms.py --letter A --count 10
    python generate_terms.py --category "Smart Building & IoT" --count 20
    python generate_terms.py --all
    python generate_terms.py --priority 1
"""

import argparse
import json
import time
import sys
import re
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from config import Config, CATEGORIES, LETTER_TARGETS

# Initialize OpenAI client
client = OpenAI(api_key=Config.OPENAI_API_KEY)


def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(Config.get_db_connection_string())


def generate_slug(term: str) -> str:
    """Generate URL-safe slug from term."""
    slug = term.lower()
    # German character replacements
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'Ä': 'ae', 'Ö': 'oe', 'Ü': 'ue'
    }
    for char, replacement in replacements.items():
        slug = slug.replace(char, replacement)
    # Replace non-alphanumeric with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


def get_existing_terms(conn) -> set:
    """Get all existing terms from database."""
    with conn.cursor() as cur:
        cur.execute("SELECT LOWER(term) FROM fm_glossar_terms")
        return {row[0] for row in cur.fetchall()}


def get_terms_count_by_letter(conn) -> dict:
    """Get term count per letter."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT letter, COUNT(*) as count
            FROM fm_glossar_terms
            GROUP BY letter
            ORDER BY letter
        """)
        return {row[0]: row[1] for row in cur.fetchall()}


def get_terms_count_by_category(conn) -> dict:
    """Get term count per category."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT category, COUNT(*) as count
            FROM fm_glossar_terms
            GROUP BY category
            ORDER BY count DESC
        """)
        return {row[0]: row[1] for row in cur.fetchall()}


GENERATION_PROMPT = """Du bist ein Experte für Facility Management in Deutschland.
Generiere einen Glossar-Eintrag für einen Fachbegriff aus dem Bereich "{category}" der mit dem Buchstaben "{letter}" beginnt.

ZIELGRUPPE:
- Unternehmen (Büro, Industrie, Handel)
- Immobilieneigentümer und Investoren
- Hausverwaltungen und Property Manager

KONTEXT:
- Website: profm24.de (Facility Management Dienstleister)
- Region: Deutschland
- Sprache: Deutsch (formell, "Sie")
- Fokus: Smart Building, IoT, Robotik, Nachhaltigkeit, Digitalisierung

BEREITS EXISTIERENDE BEGRIFFE (NICHT WIEDERHOLEN):
{existing_terms}

AUSGABE-FORMAT (JSON):
{{
  "term": "Exakter Begriff (muss mit '{letter}' beginnen)",
  "term_en": "English term if applicable",
  "abbreviation": "Abkürzung falls vorhanden (z.B. BMS, CAFM)",

  "definition": "Ausführliche Definition (min. 300 Zeichen). Erkläre was es ist, wie es funktioniert und warum es im FM wichtig ist. Bezug auf deutsche Normen/Standards wenn relevant.",

  "definition_short": "Kurze Definition für Snippets (max. 160 Zeichen, mit Keyword am Anfang)",

  "examples": "Konkretes Praxisbeispiel aus dem deutschen FM (min. 150 Zeichen). Z.B. 'In einem Bürogebäude mit 500 Mitarbeitern...' mit konkreten Zahlen und Ergebnissen.",

  "use_cases": "3-4 typische Anwendungsfälle, kommasepariert",

  "benefits": "5 konkrete Vorteile für Unternehmen/Eigentümer mit Zahlen, z.B. 'Kostenreduktion um 15-30%', 'Energieeinsparung von 20%'",

  "synonyms": "Alternative deutsche Bezeichnungen, kommasepariert",

  "related_terms": "4-5 verwandte Glossar-Begriffe aus dem FM, kommasepariert",

  "category": "{category}",

  "subcategory": "Unterkategorie falls sinnvoll",

  "target_audience": ["unternehmen", "immobilieneigentuemer", "hausverwaltungen"],

  "difficulty_level": "beginner | intermediate | advanced",

  "search_volume": "Geschätztes monatliches Suchvolumen in Deutschland (100-5000)",

  "faq_items": [
    {{"question": "Was ist [Begriff]?", "answer": "Antwort in 2-3 Sätzen"}},
    {{"question": "Welche Vorteile bietet [Begriff]?", "answer": "Antwort mit konkreten Vorteilen"}},
    {{"question": "Was kostet [Begriff]?", "answer": "Realistische Kostenangabe oder Faktoren"}},
    {{"question": "Wie implementiert man [Begriff]?", "answer": "Praktische Implementierungsschritte"}}
  ]
}}

QUALITÄTSREGELN:
1. Der Begriff MUSS mit dem Buchstaben '{letter}' beginnen
2. Definition muss min. 300 Zeichen haben
3. Alle Texte auf Deutsch (außer term_en)
4. Fachlich korrekt und aktuell (Stand 2024/2025)
5. Praxisbezogen für deutsche Unternehmen
6. SEO-optimiert (Keyword natürlich einbauen, nicht stuffing)
7. Keine Werbesprache, sachlich informativ
8. Begriff darf NICHT in der Liste existierender Begriffe sein

Antworte NUR mit dem JSON-Objekt, keine zusätzlichen Erklärungen."""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_term_with_ai(letter: str, category: str, existing_terms: list) -> dict:
    """Generate a single term using OpenAI GPT-4o."""
    # Limit existing terms to show (avoid token overflow)
    terms_sample = existing_terms[:50] if len(existing_terms) > 50 else existing_terms

    prompt = GENERATION_PROMPT.format(
        letter=letter,
        category=category,
        existing_terms=", ".join(terms_sample) if terms_sample else "Keine"
    )

    response = client.chat.completions.create(
        model=Config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "Du bist ein Facility Management Experte und generierst präzise, fachlich korrekte Glossar-Einträge im JSON-Format."},
            {"role": "user", "content": prompt}
        ],
        temperature=Config.OPENAI_TEMPERATURE,
        max_tokens=1500
    )

    content = response.choices[0].message.content.strip()

    # Extract JSON from response
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    return json.loads(content.strip())


def validate_term(term_data: dict, letter: str, existing_terms: set) -> tuple[bool, str]:
    """Validate generated term data."""
    # Check term exists and starts with correct letter
    term = term_data.get('term', '')
    if not term:
        return False, "Term is empty"

    if not term[0].upper() == letter.upper():
        return False, f"Term '{term}' does not start with '{letter}'"

    # Check if term already exists
    if term.lower() in existing_terms:
        return False, f"Term '{term}' already exists"

    # Check definition length
    definition = term_data.get('definition', '')
    if len(definition) < 200:
        return False, f"Definition too short ({len(definition)} chars, min 200)"

    # Check required fields
    required = ['term', 'definition', 'category', 'examples']
    for field in required:
        if not term_data.get(field):
            return False, f"Missing required field: {field}"

    return True, "Valid"


def insert_term(conn, term_data: dict) -> int:
    """Insert term into database and return ID."""
    slug = generate_slug(term_data['term'])

    # Prepare FAQ items as JSON
    faq_items = term_data.get('faq_items', [])
    if isinstance(faq_items, list):
        faq_items = json.dumps(faq_items, ensure_ascii=False)

    # Prepare target audience as JSON
    target_audience = term_data.get('target_audience', ['unternehmen'])
    if isinstance(target_audience, list):
        target_audience = json.dumps(target_audience, ensure_ascii=False)

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO fm_glossar_terms (
                term, term_en, abbreviation, letter,
                definition, definition_short, examples, use_cases, benefits,
                synonyms, related_terms, category, subcategory,
                target_audience, difficulty_level,
                slug, meta_title, meta_description, focus_keyword,
                search_volume, faq_items, priority
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s
            ) RETURNING id
        """, (
            term_data['term'],
            term_data.get('term_en'),
            term_data.get('abbreviation'),
            term_data['term'][0].upper(),
            term_data['definition'],
            term_data.get('definition_short', term_data['definition'][:160]),
            term_data.get('examples'),
            term_data.get('use_cases'),
            term_data.get('benefits'),
            term_data.get('synonyms'),
            term_data.get('related_terms'),
            term_data['category'],
            term_data.get('subcategory'),
            target_audience,
            term_data.get('difficulty_level', 'intermediate'),
            slug,
            f"{term_data['term']} | Facility Management Glossar | ProFM24"[:70],
            term_data.get('definition_short', term_data['definition'][:160]),
            term_data['term'],
            int(term_data.get('search_volume', 500)),
            faq_items,
            3  # Default priority
        ))
        conn.commit()
        return cur.fetchone()[0]


def generate_terms_for_letter(letter: str, count: int, category: str = None):
    """Generate terms for a specific letter."""
    print(f"\n{'='*60}")
    print(f"Generating {count} terms for letter '{letter}'")
    if category:
        print(f"Category: {category}")
    print('='*60)

    conn = get_db_connection()
    existing_terms = get_existing_terms(conn)
    letter_existing = [t for t in existing_terms if t.startswith(letter.lower())]

    print(f"Existing terms starting with '{letter}': {len(letter_existing)}")

    generated = 0
    attempts = 0
    max_attempts = count * 3  # Allow 3x attempts for failures

    # Select category if not specified
    if not category:
        categories = CATEGORIES.copy()
    else:
        categories = [category]

    while generated < count and attempts < max_attempts:
        attempts += 1
        current_category = categories[generated % len(categories)]

        try:
            print(f"\n[{generated+1}/{count}] Generating term (attempt {attempts})...")
            print(f"  Category: {current_category}")

            term_data = generate_term_with_ai(letter, current_category, list(letter_existing))

            # Validate
            valid, message = validate_term(term_data, letter, existing_terms)
            if not valid:
                print(f"  ❌ Invalid: {message}")
                continue

            # Insert
            term_id = insert_term(conn, term_data)
            existing_terms.add(term_data['term'].lower())
            letter_existing.append(term_data['term'].lower())

            print(f"  ✅ Generated: {term_data['term']}")
            print(f"     ID: {term_id}, Category: {term_data['category']}")
            print(f"     Definition: {term_data['definition'][:80]}...")

            generated += 1

            # Rate limiting
            time.sleep(Config.GENERATION_DELAY)

        except json.JSONDecodeError as e:
            print(f"  ❌ JSON parse error: {e}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            time.sleep(2)  # Extra delay on error

    conn.close()
    print(f"\n{'='*60}")
    print(f"Completed: {generated}/{count} terms generated for '{letter}'")
    print('='*60)

    return generated


def generate_all_terms():
    """Generate terms for all letters based on targets."""
    conn = get_db_connection()
    current_counts = get_terms_count_by_letter(conn)
    conn.close()

    total_generated = 0

    for letter, target in LETTER_TARGETS.items():
        current = current_counts.get(letter, 0)
        needed = target - current

        if needed <= 0:
            print(f"Letter '{letter}': {current}/{target} - Complete ✓")
            continue

        print(f"\nLetter '{letter}': {current}/{target} - Need {needed} more")
        generated = generate_terms_for_letter(letter, needed)
        total_generated += generated

        # Progress break every 50 terms
        if total_generated > 0 and total_generated % 50 == 0:
            print(f"\n{'='*60}")
            print(f"Progress: {total_generated} terms generated")
            print(f"Taking a 10 second break...")
            print('='*60)
            time.sleep(10)

    return total_generated


def generate_priority_terms(priority: int):
    """Generate high-priority terms from predefined list."""
    data_file = Config.DATA_DIR / 'terms_priority_1.json'

    if not data_file.exists():
        print(f"Priority terms file not found: {data_file}")
        return 0

    with open(data_file) as f:
        data = json.load(f)

    priority_terms = data.get('priority_1_terms', [])
    conn = get_db_connection()
    existing_terms = get_existing_terms(conn)

    generated = 0

    for term_info in priority_terms:
        term = term_info['term']
        if term.lower() in existing_terms:
            print(f"⏭️  Skipping existing term: {term}")
            continue

        letter = term[0].upper()
        category = term_info.get('category', 'Smart Building & IoT')

        try:
            print(f"\n🎯 Generating priority term: {term}")
            term_data = generate_term_with_ai(letter, category, list(existing_terms))

            # Override with specific term if AI generated different one
            if term_data['term'].lower() != term.lower():
                print(f"  ⚠️  AI generated '{term_data['term']}' instead of '{term}'")
                # Force the term name
                term_data['term'] = term
                if term_info.get('term_en'):
                    term_data['term_en'] = term_info['term_en']
                if term_info.get('abbreviation'):
                    term_data['abbreviation'] = term_info['abbreviation']

            # Validate
            valid, message = validate_term(term_data, letter, existing_terms)
            if not valid:
                print(f"  ❌ Invalid: {message}")
                continue

            # Insert with high priority
            term_data['priority'] = 1
            term_id = insert_term(conn, term_data)
            existing_terms.add(term.lower())

            print(f"  ✅ Generated: {term} (ID: {term_id})")
            generated += 1

            time.sleep(Config.GENERATION_DELAY)

        except Exception as e:
            print(f"  ❌ Error generating '{term}': {e}")

    conn.close()
    return generated


def show_statistics():
    """Show current glossary statistics."""
    conn = get_db_connection()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM fm_glossar_statistics")
        stats = cur.fetchone()

    letter_counts = get_terms_count_by_letter(conn)
    category_counts = get_terms_count_by_category(conn)
    conn.close()

    print("\n" + "="*60)
    print("ProFM24 GLOSSARY STATISTICS")
    print("="*60)

    if stats:
        print(f"\nTotal Terms:        {stats['total_terms']}")
        print(f"Published:          {stats['published_terms']}")
        print(f"Synced to WP:       {stats['synced_to_wp']}")
        print(f"Letters Covered:    {stats['letters_covered']}/26")
        print(f"Categories:         {stats['categories_count']}/15")
        print(f"Search Volume:      {stats['total_search_volume']:,}/month")
        print(f"Avg Definition:     {stats['avg_definition_length']} chars")

    print("\n📊 Terms by Letter:")
    print("-"*40)
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        current = letter_counts.get(letter, 0)
        target = LETTER_TARGETS.get(letter, 0)
        bar = '█' * min(current, 20) + '░' * max(0, min(target, 20) - current)
        status = '✓' if current >= target else ''
        print(f"  {letter}: {current:3}/{target:3} {bar} {status}")

    print("\n📁 Terms by Category:")
    print("-"*40)
    for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {category}: {count}")

    print("="*60)


def main():
    parser = argparse.ArgumentParser(description='ProFM24 Glossary Term Generator')
    parser.add_argument('--letter', '-l', help='Generate terms for specific letter (A-Z)')
    parser.add_argument('--count', '-c', type=int, default=10, help='Number of terms to generate')
    parser.add_argument('--category', '-cat', help='Specific category to generate for')
    parser.add_argument('--all', '-a', action='store_true', help='Generate all missing terms')
    parser.add_argument('--priority', '-p', type=int, help='Generate priority terms (1=highest)')
    parser.add_argument('--stats', '-s', action='store_true', help='Show statistics only')
    parser.add_argument('--test', '-t', action='store_true', help='Test mode (generate 1 term)')

    args = parser.parse_args()

    # Validate config
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file")
        sys.exit(1)

    if args.stats:
        show_statistics()
        return

    if args.test:
        print("🧪 Test mode: Generating 1 term for letter 'A'")
        generate_terms_for_letter('A', 1, 'Smart Building & IoT')
        return

    if args.priority:
        print(f"🎯 Generating priority {args.priority} terms...")
        generated = generate_priority_terms(args.priority)
        print(f"\n✅ Generated {generated} priority terms")
        show_statistics()
        return

    if args.all:
        print("🚀 Generating all missing terms...")
        generated = generate_all_terms()
        print(f"\n✅ Generated {generated} total terms")
        show_statistics()
        return

    if args.letter:
        letter = args.letter.upper()
        if letter not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            print(f"❌ Invalid letter: {args.letter}")
            sys.exit(1)
        generate_terms_for_letter(letter, args.count, args.category)
        show_statistics()
        return

    # Default: show help
    parser.print_help()


if __name__ == '__main__':
    main()
