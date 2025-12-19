#!/usr/bin/env python3
"""
Generate Pro-FM Facility Management Glossary Terms using OpenAI GPT-4

This script generates German Facility Management terminology for the Pro-FM website.
Categories include: FM, cleaning, caretaker services, project management, automation,
process optimization, security, energy efficiency, renewable energy, heat pumps,
robotics, and HVAC.

Usage:
    cd /root/WP_Pro-FM/backend
    python generate_glossary.py                    # Generate all terms
    python generate_glossary.py --letter A         # Generate only letter A
    python generate_glossary.py --category "Facility Management"  # Generate for one category
    python generate_glossary.py --count 10         # Generate 10 terms per letter
    python generate_glossary.py --init-categories  # Initialize categories only
"""

import os
import sys
import time
import json
import argparse
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from openai import OpenAI
from django.conf import settings
from apps.glossary.models import GlossaryTerm, GlossaryCategory


# Categories for Pro-FM Facility Management Glossary
FM_CATEGORIES = [
    {
        'name': 'Facility Management',
        'description': 'Allgemeine Begriffe des Facility Managements, Gebäudeverwaltung und -bewirtschaftung',
        'icon_class': 'fa fa-building',
        'order': 1
    },
    {
        'name': 'Gebäudereinigung',
        'description': 'Begriffe zur professionellen Reinigung von Gebäuden und Objekten',
        'icon_class': 'fa fa-broom',
        'order': 2
    },
    {
        'name': 'Hausmeisterdienste',
        'description': 'Hausmeisterservice, Objektbetreuung und technische Dienste',
        'icon_class': 'fa fa-tools',
        'order': 3
    },
    {
        'name': 'Projektmanagement',
        'description': 'Begriffe aus dem Projektmanagement im FM-Kontext',
        'icon_class': 'fa fa-tasks',
        'order': 4
    },
    {
        'name': 'Automatisierung',
        'description': 'Gebäudeautomation, Smart Building und digitale Steuerung',
        'icon_class': 'fa fa-robot',
        'order': 5
    },
    {
        'name': 'Prozessoptimierung',
        'description': 'Optimierung von FM-Prozessen, Lean Management, Effizienzsteigerung',
        'icon_class': 'fa fa-chart-line',
        'order': 6
    },
    {
        'name': 'Sicherheit',
        'description': 'Gebäudesicherheit, Zutrittskontrolle, Brandschutz und Arbeitsschutz',
        'icon_class': 'fa fa-shield-alt',
        'order': 7
    },
    {
        'name': 'Energieeffizienz',
        'description': 'Energiemanagement, Energieeinsparung und Nachhaltigkeit',
        'icon_class': 'fa fa-bolt',
        'order': 8
    },
    {
        'name': 'Erneuerbare Energien',
        'description': 'Grüne Energie, Photovoltaik, nachhaltige Energiequellen',
        'icon_class': 'fa fa-solar-panel',
        'order': 9
    },
    {
        'name': 'Wärmepumpen',
        'description': 'Wärmepumpentechnologie, Heizungstechnik und thermische Systeme',
        'icon_class': 'fa fa-thermometer-half',
        'order': 10
    },
    {
        'name': 'Robotik',
        'description': 'Reinigungsroboter, automatisierte Systeme und KI im FM',
        'icon_class': 'fa fa-android',
        'order': 11
    },
    {
        'name': 'Klimatechnik',
        'description': 'HVAC, Lüftung, Klimaanlagen und Raumlufttechnik (RLT)',
        'icon_class': 'fa fa-wind',
        'order': 12
    },
]

# Letter distribution for ~500 terms total
LETTER_TARGETS = {
    'A': 30, 'B': 25, 'C': 8, 'D': 20, 'E': 25, 'F': 30, 'G': 25,
    'H': 25, 'I': 15, 'J': 5, 'K': 30, 'L': 20, 'M': 20, 'N': 15,
    'O': 10, 'P': 20, 'Q': 3, 'R': 30, 'S': 40, 'T': 25, 'U': 15,
    'V': 15, 'W': 25, 'X': 2, 'Y': 2, 'Z': 15
}


class GlossaryGenerator:
    """Generate Pro-FM Facility Management glossary terms using OpenAI"""

    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.categories = {cat.name: cat for cat in GlossaryCategory.objects.all()}

    def init_categories(self):
        """Initialize all FM categories in the database"""
        print("\n" + "="*60)
        print("INITIALIZING FACILITY MANAGEMENT CATEGORIES")
        print("="*60)

        created = 0
        updated = 0

        for cat_data in FM_CATEGORIES:
            cat, is_new = GlossaryCategory.objects.update_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon_class': cat_data['icon_class'],
                    'order': cat_data['order'],
                    'is_active': True
                }
            )
            if is_new:
                created += 1
                print(f"  Created: {cat.name}")
            else:
                updated += 1
                print(f"  Updated: {cat.name}")

        print(f"\nCategories: {created} created, {updated} updated")

        # Refresh categories dict
        self.categories = {cat.name: cat for cat in GlossaryCategory.objects.all()}
        return created, updated

    def generate_term_with_ai(self, letter: str, category_name: str, existing_terms: list) -> dict:
        """Generate a single term using OpenAI GPT-4"""

        category_descriptions = {
            'Facility Management': 'allgemeines Facility Management, Gebäudeverwaltung, Immobilienbewirtschaftung, FM-Strategien',
            'Gebäudereinigung': 'professionelle Gebäudereinigung, Unterhaltsreinigung, Grundreinigung, Reinigungstechniken',
            'Hausmeisterdienste': 'Hausmeisterservice, Objektbetreuung, technische Hauspflege, Winterdienst',
            'Projektmanagement': 'FM-Projekte, Bauprojekte, Sanierungsmanagement, Terminplanung',
            'Automatisierung': 'Gebäudeautomation, BMS, Smart Building, IoT im FM, digitale Steuerung',
            'Prozessoptimierung': 'Lean FM, KPI-Management, Workflow-Optimierung, Effizienzsteigerung',
            'Sicherheit': 'Gebäudesicherheit, Zutrittskontrolle, Brandschutz, Arbeitsschutz, Notfallmanagement',
            'Energieeffizienz': 'Energiemanagement, Energiemonitoring, CO2-Reduzierung, Nachhaltigkeitszertifizierung',
            'Erneuerbare Energien': 'Photovoltaik, Solarthermie, Windenergie, nachhaltige Energieerzeugung',
            'Wärmepumpen': 'Luft-Wasser-Wärmepumpe, Erdwärme, Heizungstechnik, thermische Systeme',
            'Robotik': 'Reinigungsroboter, Serviceroboter, autonome Systeme, KI im Facility Management',
            'Klimatechnik': 'HVAC, Lüftungsanlagen, Klimaanlagen, RLT-Anlagen, Kältetechnik',
        }

        context = category_descriptions.get(category_name, category_name)

        prompt = f"""Du bist ein Experte für Facility Management in Deutschland.

Generiere einen NEUEN Fachbegriff aus dem Bereich Facility Management, der mit dem Buchstaben '{letter}' beginnt.

KATEGORIE: {category_name}
KONTEXT: {context}

WICHTIG: Der Begriff darf NICHT einer dieser bereits vorhandenen Begriffe sein:
{', '.join(existing_terms[-30:]) if existing_terms else 'keine'}

ANFORDERUNGEN:
1. Begriff muss mit '{letter}' beginnen
2. Muss relevant für {category_name} im Facility Management sein
3. Professioneller Fachbegriff aus der deutschen FM-Branche
4. Kann auch englische Fachbegriffe sein, die in Deutschland verwendet werden (z.B. "Building Management System")

AUSGABEFORMAT (JSON):
{{
  "term": "Der genaue Fachbegriff",
  "definition": "Ausführliche professionelle Definition (MINIMUM 250 Zeichen). Erkläre was der Begriff bedeutet, welche Anwendungen es gibt, welche Normen/Standards relevant sind, wie er im FM-Alltag eingesetzt wird.",
  "examples": "Konkretes Praxisbeispiel aus dem Facility Management (min. 150 Zeichen). Beschreibe eine echte Situation in einem Gebäude oder FM-Projekt.",
  "synonyms": "Synonym1, Synonym2, Synonym3 (falls vorhanden, sonst leer lassen)",
  "related_terms": "Verwandter Begriff1, Verwandter Begriff2, Verwandter Begriff3",
  "search_volume": 50-1500 (geschätztes monatliches Suchvolumen in Deutschland)
}}

Antworte NUR mit dem JSON, ohne zusätzlichen Text oder Markdown."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Du bist ein Experte für Facility Management und generierst hochwertige Glossar-Einträge in perfektem Deutsch. Antworte immer nur mit validem JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1000
            )

            content = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            if content.startswith('```'):
                content = content.split('\n', 1)[1]
                if content.endswith('```'):
                    content = content.rsplit('```', 1)[0]
                content = content.strip()

            term_data = json.loads(content)

            # Validate minimum lengths
            if len(term_data.get('definition', '')) < 200:
                print(f"  Warning: Definition too short ({len(term_data.get('definition', ''))} chars)")
                return None

            return term_data

        except json.JSONDecodeError as e:
            print(f"  Error: JSON parsing failed: {e}")
            return None
        except Exception as e:
            print(f"  Error: OpenAI API error: {e}")
            return None

    def get_existing_terms_for_letter(self, letter: str) -> list:
        """Get list of existing terms for a letter"""
        return list(GlossaryTerm.objects.filter(letter=letter).values_list('term', flat=True))

    def insert_term(self, term_data: dict, letter: str, category_name: str) -> bool:
        """Insert term into database"""
        try:
            category = self.categories.get(category_name)

            term, created = GlossaryTerm.objects.update_or_create(
                term=term_data['term'],
                defaults={
                    'definition': term_data['definition'],
                    'examples': term_data.get('examples', ''),
                    'synonyms': term_data.get('synonyms', ''),
                    'related_terms': term_data.get('related_terms', ''),
                    'category': category,
                    'search_volume': term_data.get('search_volume', 100),
                    'priority': 3,
                    'is_active': True
                }
            )

            return created

        except Exception as e:
            print(f"  Error: Database insert failed: {e}")
            return False

    def generate_terms_for_letter(self, letter: str, target_count: int, category_filter: str = None):
        """Generate all terms for a specific letter"""
        existing_terms = self.get_existing_terms_for_letter(letter)
        current_count = len(existing_terms)

        print(f"\n{'='*60}")
        print(f"Letter {letter}: {current_count} terms exist, target: {target_count}")
        print("="*60)

        if current_count >= target_count:
            print(f"Letter {letter} already complete, skipping...")
            return

        terms_to_generate = target_count - current_count
        success_count = 0
        attempt_count = 0
        max_attempts = terms_to_generate * 3

        # Rotate through categories
        categories = list(self.categories.keys())
        if category_filter:
            categories = [category_filter]

        cat_index = 0

        while success_count < terms_to_generate and attempt_count < max_attempts:
            attempt_count += 1
            category_name = categories[cat_index % len(categories)]
            cat_index += 1

            print(f"\nGenerating term {current_count + success_count + 1}/{target_count} for {letter} ({category_name})...")

            term_data = self.generate_term_with_ai(letter, category_name, existing_terms)

            if term_data:
                # Verify term starts with correct letter
                if term_data['term'][0].upper() != letter:
                    print(f"  Skip: '{term_data['term']}' doesn't start with {letter}")
                    continue

                # Check for duplicates
                if term_data['term'] in existing_terms:
                    print(f"  Skip: '{term_data['term']}' already exists")
                    continue

                if self.insert_term(term_data, letter, category_name):
                    success_count += 1
                    existing_terms.append(term_data['term'])
                    print(f"  Created: {term_data['term']} ({len(term_data['definition'])} chars)")

                # Rate limiting
                time.sleep(0.5)
            else:
                print("  Failed to generate, retrying...")
                time.sleep(1)

        print(f"\nCompleted letter {letter}: {success_count} new terms added")

    def generate_all_terms(self, letter_filter: str = None, category_filter: str = None, count_override: int = None):
        """Generate all glossary terms"""
        # Initialize categories first
        self.init_categories()

        total_target = sum(LETTER_TARGETS.values())
        total_current = GlossaryTerm.objects.count()

        print(f"\n{'='*60}")
        print(f"PRO-FM GLOSSARY TERM GENERATION")
        print("="*60)
        print(f"Target: {total_target} terms across {len(LETTER_TARGETS)} letters")
        print(f"Current: {total_current} terms already in database")
        print(f"To generate: {total_target - total_current} terms")

        if letter_filter:
            letters_to_process = {letter_filter.upper(): count_override or LETTER_TARGETS.get(letter_filter.upper(), 20)}
        else:
            letters_to_process = LETTER_TARGETS

        for letter, target in letters_to_process.items():
            if count_override:
                target = count_override
            try:
                self.generate_terms_for_letter(letter, target, category_filter)
            except KeyboardInterrupt:
                print("\n\nGeneration interrupted. Progress saved.")
                break
            except Exception as e:
                print(f"Error processing letter {letter}: {e}")
                continue

        # Final statistics
        final_count = GlossaryTerm.objects.count()
        print(f"\n{'='*60}")
        print(f"GENERATION COMPLETE")
        print("="*60)
        print(f"Total terms in database: {final_count}")

        # Category breakdown
        print("\nTerms by category:")
        for cat in GlossaryCategory.objects.all():
            cat_count = GlossaryTerm.objects.filter(category=cat).count()
            print(f"  {cat.name}: {cat_count}")

        # Letter breakdown
        print("\nTerms by letter:")
        for letter in sorted(LETTER_TARGETS.keys()):
            letter_count = GlossaryTerm.objects.filter(letter=letter).count()
            target = LETTER_TARGETS[letter]
            status = "OK" if letter_count >= target else f"need {target - letter_count} more"
            print(f"  {letter}: {letter_count}/{target} ({status})")


def main():
    parser = argparse.ArgumentParser(description="Generate Pro-FM Facility Management Glossary")
    parser.add_argument('--letter', type=str, help='Generate only for specific letter (A-Z)')
    parser.add_argument('--category', type=str, help='Generate only for specific category')
    parser.add_argument('--count', type=int, help='Override number of terms per letter')
    parser.add_argument('--init-categories', action='store_true', help='Initialize categories only')

    args = parser.parse_args()

    generator = GlossaryGenerator()

    if args.init_categories:
        generator.init_categories()
    else:
        generator.generate_all_terms(
            letter_filter=args.letter,
            category_filter=args.category,
            count_override=args.count
        )


if __name__ == "__main__":
    main()
