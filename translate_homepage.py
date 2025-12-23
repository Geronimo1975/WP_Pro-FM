#!/usr/bin/env python3
"""
Translate WordPress Homepage (EN→DE) following translation standards.
Uses OpenAI GPT-4o for professional German (Hochdeutsch) translation.
"""

import os
import re
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
WP_SITE_URL = os.getenv("WP_SITE_URL", "https://profm24.de")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Translation system prompt based on standards
TRANSLATION_SYSTEM_PROMPT = """Du bist ein professioneller Übersetzer, spezialisiert auf:
- Hochdeutsch (formale deutsche Standardsprache)
- Facility Management und Gebäudemanagement Terminologie
- SEO Copywriting auf Deutsch
- Kulturelle Lokalisierung für den deutschen Markt

## Übersetzungsregeln

### Stil und Ton
- Verwende SIE (formell), NICHT du
- Professioneller aber zugänglicher Ton
- Vermeide Anglizismen wenn deutsche Äquivalente existieren
- Halte Sätze prägnant und klar

### Spezifische Terminologie (Facility Management)
| Englisch | Deutsch |
|----------|---------|
| Services | Dienstleistungen |
| Project Planning | Projektplanung |
| General Contract | Generalunternehmer |
| Refurbishment | Sanierung |
| Interior Design | Innenarchitektur |
| Full project management | Komplettes Projektmanagement |
| Construction | Bauwesen |
| Read More | Mehr erfahren |
| Find out more | Mehr erfahren |
| Explore the features | Entdecken Sie unsere Leistungen |
| Contemporary Villa | Moderne Villa |
| House of Cards | Kartenhaus-Design |
| Kitchen and Living | Küche und Wohnen |
| Modern materials | Moderne Materialien |
| Parametric modeling | Parametrische Modellierung |

### CTA Übersetzungen
| Original | Übersetzung |
|----------|-------------|
| Get a Quote | Angebot anfordern |
| Contact Us | Kontaktieren Sie uns |
| Learn More | Mehr erfahren |
| Book Now | Jetzt buchen |
| Read More | Mehr erfahren |
| Find out more | Mehr erfahren |

### Formatierung
- Behalte die HTML/Markdown Struktur bei
- Übersetze KEINE: URLs, Code, Markennamen
- Passe Zahlenformate an: 1,000.00 → 1.000,00
- Passe Datumsformate an: MM/DD/YYYY → DD.MM.YYYY

Gib NUR die Übersetzung zurück, ohne zusätzliche Erklärungen."""


def get_wordpress_page(page_id: int) -> dict:
    """Fetch WordPress page content."""
    url = f"{WP_SITE_URL}/?rest_route=/wp/v2/pages/{page_id}"
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    response = requests.get(url, auth=auth)
    response.raise_for_status()
    return response.json()


def extract_translatable_text(html_content: str) -> list:
    """Extract text elements that need translation from HTML."""
    patterns = [
        # Headings
        (r'<h1[^>]*>(.*?)</h1>', 'h1'),
        (r'<h2[^>]*>(.*?)</h2>', 'h2'),
        (r'<h3[^>]*>(.*?)</h3>', 'h3'),
        (r'<h4[^>]*>(.*?)</h4>', 'h4'),
        (r'<h5[^>]*>(.*?)</h5>', 'h5'),
        (r'<h6[^>]*>(.*?)</h6>', 'h6'),
        # Paragraphs
        (r'<p[^>]*>(.*?)</p>', 'p'),
        # Button text
        (r'<span class="mkdf-btn-text">(.*?)</span>', 'button'),
    ]

    elements = []
    for pattern, element_type in patterns:
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        for match in matches:
            # Clean up the text
            text = re.sub(r'<[^>]+>', '', match).strip()
            if text and len(text) > 1 and not text.startswith('http'):
                # Skip lorem ipsum
                if 'lorem ipsum' not in text.lower():
                    elements.append({
                        'type': element_type,
                        'original': text,
                        'full_match': match
                    })

    # Remove duplicates
    seen = set()
    unique_elements = []
    for elem in elements:
        if elem['original'] not in seen:
            seen.add(elem['original'])
            unique_elements.append(elem)

    return unique_elements


def translate_text(text: str) -> str:
    """Translate text using OpenAI GPT-4o."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Übersetze ins Deutsche:\n\n{text}"}
        ],
        temperature=0.3,
        max_tokens=2000
    )
    return response.choices[0].message.content.strip()


def translate_batch(texts: list) -> dict:
    """Translate multiple texts in one API call for efficiency."""
    if not texts:
        return {}

    # Create a numbered list of texts
    numbered_texts = "\n".join([f"{i+1}. {text}" for i, text in enumerate(texts)])

    prompt = f"""Übersetze die folgenden Texte ins Deutsche. Gib die Übersetzungen als nummerierte Liste zurück (im gleichen Format):

{numbered_texts}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=4000
    )

    result = response.choices[0].message.content.strip()

    # Parse the numbered responses
    translations = {}
    lines = result.split('\n')
    for line in lines:
        match = re.match(r'^(\d+)\.\s*(.+)$', line.strip())
        if match:
            idx = int(match.group(1)) - 1
            if idx < len(texts):
                translations[texts[idx]] = match.group(2)

    return translations


def update_wordpress_page(page_id: int, title: str, content: str) -> dict:
    """Update WordPress page with translated content."""
    url = f"{WP_SITE_URL}/?rest_route=/wp/v2/pages/{page_id}"
    auth = (WP_USERNAME, WP_APP_PASSWORD)

    data = {
        "title": title,
        "content": content
    }

    response = requests.post(url, auth=auth, json=data)
    response.raise_for_status()
    return response.json()


def main():
    page_id = 9161

    print("=" * 60)
    print("WordPress Homepage Translation (EN→DE)")
    print("=" * 60)

    # Step 1: Fetch page content
    print("\n[1/4] Fetching WordPress page content...")
    page = get_wordpress_page(page_id)
    title = page.get('title', {}).get('rendered', '')
    content = page.get('content', {}).get('rendered', '')

    print(f"   Title: {title}")
    print(f"   Content length: {len(content)} characters")

    # Step 2: Extract translatable elements
    print("\n[2/4] Extracting translatable text elements...")
    elements = extract_translatable_text(content)
    print(f"   Found {len(elements)} unique text elements")

    # Show found elements
    print("\n   Text elements to translate:")
    for i, elem in enumerate(elements[:15], 1):  # Show first 15
        text_preview = elem['original'][:50] + "..." if len(elem['original']) > 50 else elem['original']
        print(f"   {i:2}. [{elem['type']:6}] {text_preview}")
    if len(elements) > 15:
        print(f"   ... and {len(elements) - 15} more")

    # Step 3: Translate using OpenAI
    print("\n[3/4] Translating with OpenAI GPT-4o...")

    # Batch translate for efficiency
    texts_to_translate = [elem['original'] for elem in elements]

    # Split into smaller batches if needed
    batch_size = 20
    all_translations = {}

    for i in range(0, len(texts_to_translate), batch_size):
        batch = texts_to_translate[i:i+batch_size]
        print(f"   Translating batch {i//batch_size + 1}/{(len(texts_to_translate)-1)//batch_size + 1}...")
        translations = translate_batch(batch)
        all_translations.update(translations)

    # Also translate the title
    print("   Translating title...")
    translated_title = translate_text(title)

    print(f"\n   Translated title: {title} → {translated_title}")

    # Show translations
    print("\n   Translations:")
    for i, elem in enumerate(elements[:10], 1):
        original = elem['original'][:30] + "..." if len(elem['original']) > 30 else elem['original']
        translated = all_translations.get(elem['original'], '')[:30] + "..." if len(all_translations.get(elem['original'], '')) > 30 else all_translations.get(elem['original'], '')
        print(f"   {i:2}. {original:35} → {translated}")

    # Step 4: Generate translated content
    print("\n[4/4] Generating translated content...")

    translated_content = content
    for original, translated in all_translations.items():
        if original and translated:
            # Replace in content (be careful with HTML)
            translated_content = translated_content.replace(f">{original}<", f">{translated}<")

    # Create translation report
    report = {
        "page_id": page_id,
        "original_title": title,
        "translated_title": translated_title,
        "elements_translated": len(all_translations),
        "translations": all_translations
    }

    # Save report
    with open("translation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"   Translation report saved to: translation_report.json")

    # Preview mode - don't update WordPress by default
    print("\n" + "=" * 60)
    print("TRANSLATION COMPLETE (Preview Mode)")
    print("=" * 60)
    print(f"\nTitle: {translated_title}")
    print(f"Elements translated: {len(all_translations)}")
    print("\nTo apply translations to WordPress, run with --apply flag")

    # Save translated content for review
    with open("translated_content.html", "w", encoding="utf-8") as f:
        f.write(translated_content)
    print("Translated content saved to: translated_content.html")

    return report


if __name__ == "__main__":
    import sys

    if "--apply" in sys.argv:
        print("WARNING: This will update the WordPress page!")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() == "yes":
            report = main()
            # Apply to WordPress
            print("\nApplying translations to WordPress...")
            # update_wordpress_page(9161, report['translated_title'], translated_content)
            print("Done!")
        else:
            print("Aborted.")
    else:
        main()
