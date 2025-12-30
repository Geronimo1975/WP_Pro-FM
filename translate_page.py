#!/usr/bin/env python3
"""
Interactive WordPress Page Translator
Translates page content with SEO optimization while preserving HTML structure.

Usage:
    python translate_page.py

Author: Claude Code
"""

import os
import re
import json
from bs4 import BeautifulSoup, NavigableString
from openai import OpenAI
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

# Load environment variables
load_dotenv('.env')


class InteractiveTranslator:
    """Interactive CLI translator for WordPress pages"""

    LANGUAGES = {
        'de': 'Deutsch (German)',
        'en': 'English',
        'ro': 'Română (Romanian)',
        'fr': 'Français (French)',
        'es': 'Español (Spanish)',
        'it': 'Italiano (Italian)',
        'pl': 'Polski (Polish)',
        'nl': 'Nederlands (Dutch)',
    }

    SEO_KEYWORDS = {
        'de': [
            "Facility Management", "Gebäudemanagement", "Gebäudewartung",
            "Brandschutzsicherheit", "Brandschutz", "Gebäudereinigung",
            "Sanitär- und Wasserinstallationen", "Energieeinsparung",
            "Energieeffizienz", "Workflow-Optimierung", "Gebäudeautomation"
        ],
        'en': [
            "Facility Management", "Building Maintenance", "Fire Safety",
            "Building Cleaning", "Plumbing Services", "Energy Efficiency",
            "Workflow Optimization", "Building Automation"
        ],
    }

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.wp_url = os.getenv('WP_SITE_URL')
        self.wp_user = os.getenv('WP_USERNAME')
        self.wp_password = os.getenv('WP_APP_PASSWORD', '').replace(' ', '')

        if not all([self.wp_url, self.wp_user, self.wp_password]):
            raise ValueError("Missing WordPress credentials in .env")

    def list_pages(self) -> list:
        """Get list of pages from WordPress"""
        url = f'{self.wp_url}/?rest_route=/wp/v2/pages&per_page=50'
        response = requests.get(
            url,
            auth=HTTPBasicAuth(self.wp_user, self.wp_password),
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def get_page(self, page_id: int) -> dict:
        """Get page content from WordPress"""
        url = f'{self.wp_url}/?rest_route=/wp/v2/pages/{page_id}&context=edit'
        response = requests.get(
            url,
            auth=HTTPBasicAuth(self.wp_user, self.wp_password),
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def update_page(self, page_id: int, content: str, title: str = None) -> dict:
        """Update page on WordPress"""
        url = f'{self.wp_url}/?rest_route=/wp/v2/pages/{page_id}'
        data = {"content": content}
        if title:
            data["title"] = title

        response = requests.post(
            url,
            auth=HTTPBasicAuth(self.wp_user, self.wp_password),
            json=data,
            timeout=60
        )
        response.raise_for_status()
        return response.json()

    def extract_text_nodes(self, html: str) -> tuple:
        """Extract text nodes from HTML, return (modified_html, text_nodes)"""
        soup = BeautifulSoup(html, 'html.parser')
        text_nodes = []
        counter = [0]
        skip_tags = {'script', 'style', 'svg', 'path', 'code', 'pre'}

        def process(element):
            if element.name in skip_tags:
                return
            for child in list(element.children):
                if isinstance(child, NavigableString):
                    text = str(child).strip()
                    if text and len(text) > 2:
                        # Skip numbers only
                        if text.replace('.', '').replace(',', '').replace(' ', '').isdigit():
                            continue
                        placeholder = f"__TRANSLATE_{counter[0]}__"
                        text_nodes.append({
                            'id': counter[0],
                            'text': text,
                            'tag': element.name,
                            'placeholder': placeholder
                        })
                        child.replace_with(NavigableString(placeholder))
                        counter[0] += 1
                elif child.name:
                    process(child)

        for el in soup.find_all(True):
            if el.name not in skip_tags:
                process(el)

        return str(soup), text_nodes

    def translate_batch(self, texts: list, target_lang: str, batch_size: int = 20) -> list:
        """Translate texts in batches with SEO optimization"""
        all_translations = []
        keywords = self.SEO_KEYWORDS.get(target_lang, self.SEO_KEYWORDS['de'])
        lang_name = self.LANGUAGES.get(target_lang, target_lang)

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"  Translating batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}...")

            batch_data = [{'id': t['id'], 'text': t['text'][:500], 'tag': t['tag']} for t in batch]

            prompt = f"""Übersetze/Translate diese Texte nach {lang_name}.

WICHTIGE REGELN / IMPORTANT RULES:
1. SEO-Optimierung: Integriere natürlich diese Keywords wo passend: {', '.join(keywords[:6])}
2. Professioneller B2B-Ton für Facility Management Website
3. Placeholder-Texte wie "Lorem ipsum" durch sinnvollen {lang_name} Facility Management Content ersetzen
4. Kurze Texte (Links, Buttons) angemessen kurz halten
5. HTML-Tags nicht übersetzen, nur den Text

TEXTE:
{json.dumps(batch_data, ensure_ascii=False, indent=2)}

ANTWORT NUR ALS JSON-ARRAY:
[{{"id": 0, "translated": "Übersetzter Text"}}, ...]"""

            response = self.client.chat.completions.create(
                model='gpt-4o',
                messages=[
                    {
                        "role": "system",
                        "content": f"Du bist ein professioneller Übersetzer und SEO-Spezialist für Facility Management. Übersetze nach {lang_name} mit SEO-Optimierung. Antworte NUR mit JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=4000
            )

            # Parse response
            response_text = response.choices[0].message.content
            json_match = re.search(r'\[[\s\S]*\]', response_text)

            if json_match:
                try:
                    translations = json.loads(json_match.group())
                    trans_map = {t['id']: t['translated'] for t in translations}

                    for node in batch:
                        all_translations.append({
                            **node,
                            'translated': trans_map.get(node['id'], node['text'])
                        })
                except json.JSONDecodeError:
                    print(f"  Warning: JSON parse error in batch {i//batch_size + 1}")
                    for node in batch:
                        all_translations.append({**node, 'translated': node['text']})
            else:
                print(f"  Warning: No JSON in response for batch {i//batch_size + 1}")
                for node in batch:
                    all_translations.append({**node, 'translated': node['text']})

        return all_translations

    def translate_title(self, title: str, target_lang: str) -> str:
        """Translate page title with SEO optimization"""
        lang_name = self.LANGUAGES.get(target_lang, target_lang)
        keywords = self.SEO_KEYWORDS.get(target_lang, self.SEO_KEYWORDS['de'])

        response = self.client.chat.completions.create(
            model='gpt-4o',
            messages=[
                {
                    "role": "system",
                    "content": f"Übersetze den Seitentitel nach {lang_name} mit SEO-Optimierung für Facility Management."
                },
                {
                    "role": "user",
                    "content": f"Übersetze diesen Titel: {title}\nKeywords: {', '.join(keywords[:4])}"
                }
            ],
            temperature=0.3,
            max_tokens=100
        )
        return response.choices[0].message.content.strip().strip('"')

    def replace_placeholders(self, html: str, translations: list) -> str:
        """Replace placeholders with translated text"""
        result = html
        for node in translations:
            result = result.replace(node['placeholder'], node['translated'])
        return result

    def run(self):
        """Main interactive loop"""
        print("\n" + "=" * 60)
        print("  WORDPRESS PAGE TRANSLATOR with SEO Optimization")
        print("=" * 60)
        print(f"\nConnected to: {self.wp_url}")

        while True:
            print("\n" + "-" * 40)
            print("OPTIONS:")
            print("  1. List available pages")
            print("  2. Translate a page")
            print("  3. Preview page content")
            print("  q. Quit")

            choice = input("\nSelect option: ").strip().lower()

            if choice == 'q':
                print("Goodbye!")
                break

            elif choice == '1':
                print("\nFetching pages...")
                pages = self.list_pages()
                print(f"\n{'ID':<8} {'Title':<50}")
                print("-" * 60)
                for page in pages[:30]:
                    title = page['title']['rendered'][:48]
                    print(f"{page['id']:<8} {title:<50}")

            elif choice == '2':
                self.translate_interactive()

            elif choice == '3':
                page_id = input("Enter page ID to preview: ").strip()
                if page_id.isdigit():
                    self.preview_page(int(page_id))
                else:
                    print("Invalid page ID")

    def preview_page(self, page_id: int):
        """Preview page content and text nodes"""
        print(f"\nFetching page {page_id}...")
        try:
            page = self.get_page(page_id)
            content = page.get('content', {}).get('raw', '')

            print(f"\nTitle: {page['title']['raw']}")
            print(f"Content length: {len(content)} characters")

            _, text_nodes = self.extract_text_nodes(content)
            print(f"Text nodes found: {len(text_nodes)}")

            print("\nFirst 15 text nodes:")
            for node in text_nodes[:15]:
                print(f"  [{node['tag']}] {node['text'][:60]}{'...' if len(node['text']) > 60 else ''}")

        except Exception as e:
            print(f"Error: {e}")

    def translate_interactive(self):
        """Interactive translation flow"""
        # Get page ID
        page_id = input("\nEnter page ID to translate: ").strip()
        if not page_id.isdigit():
            print("Invalid page ID")
            return

        page_id = int(page_id)

        # Get target language
        print("\nAvailable languages:")
        for code, name in self.LANGUAGES.items():
            print(f"  {code}: {name}")

        target_lang = input("\nTarget language (e.g., 'de' for German): ").strip().lower()
        if target_lang not in self.LANGUAGES:
            print(f"Unknown language: {target_lang}")
            return

        # Confirm
        print(f"\nWill translate page {page_id} to {self.LANGUAGES[target_lang]}")
        confirm = input("Proceed? (y/n): ").strip().lower()

        if confirm != 'y':
            print("Cancelled")
            return

        # Translate
        try:
            print(f"\nFetching page {page_id}...")
            page = self.get_page(page_id)
            original_content = page.get('content', {}).get('raw', '')
            original_title = page.get('title', {}).get('raw', '')

            print(f"Original title: {original_title}")
            print(f"Content length: {len(original_content)} chars")

            # Extract text nodes
            print("\nExtracting text nodes...")
            html_with_placeholders, text_nodes = self.extract_text_nodes(original_content)
            print(f"Found {len(text_nodes)} text nodes to translate")

            if len(text_nodes) == 0:
                print("No text found to translate!")
                return

            # Translate
            print("\nTranslating content (this may take a moment)...")
            translated_nodes = self.translate_batch(text_nodes, target_lang)

            # Translate title
            print("Translating title...")
            translated_title = self.translate_title(original_title, target_lang)
            print(f"New title: {translated_title}")

            # Replace placeholders
            print("Building translated content...")
            translated_content = self.replace_placeholders(html_with_placeholders, translated_nodes)

            # Show sample translations
            print("\n=== SAMPLE TRANSLATIONS ===")
            for node in translated_nodes[:8]:
                print(f"  Original: {node['text'][:50]}...")
                print(f"  Translated: {node['translated'][:50]}...")
                print()

            # Confirm update
            print("-" * 40)
            update = input("Apply changes to WordPress? (y/n): ").strip().lower()

            if update == 'y':
                print("\nUpdating WordPress page...")
                result = self.update_page(page_id, translated_content, translated_title)
                print(f"\n✅ SUCCESS! Page {page_id} has been translated!")
                print(f"View at: {self.wp_url}/?page_id={page_id}")
            else:
                print("Changes not applied.")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    try:
        translator = InteractiveTranslator()
        translator.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
