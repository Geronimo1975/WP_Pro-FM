"""
WordPress Page Translator with SEO Optimization
Translates page content while preserving HTML/CSS structure
"""

import os
import re
import json
from typing import Dict, List, Tuple, Optional
from bs4 import BeautifulSoup, NavigableString
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth

# Load environment variables
try:
    env_path = Path(__file__).parent.parent / '.env'
except NameError:
    env_path = Path('.env')
load_dotenv(env_path)


class PageTranslator:
    """
    Translate WordPress pages while preserving HTML structure.
    Only text content is translated, CSS/design remains intact.
    """

    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"

        # WordPress credentials
        self.wp_url = os.getenv('WP_SITE_URL', 'https://profm24.de')
        self.wp_user = os.getenv('WP_USERNAME', 'admin')
        self.wp_password = os.getenv('WP_APP_PASSWORD', '').replace(' ', '')

        # SEO keywords for Facility Management
        self.seo_keywords = [
            "Facility Management",
            "Gebäudemanagement",
            "Gebäudewartung",
            "Instandhaltung",
            "Brandschutzsicherheit",
            "Brandschutz",
            "Gebäudereinigung",
            "Reinigungsdienstleistungen",
            "Sanitär- und Wasserinstallationen",
            "Sanitärinstallationen",
            "Energieeinsparung",
            "Energieeffizienz",
            "Workflow-Optimierung",
            "Gebäudeautomation",
            "Technisches Gebäudemanagement"
        ]

    def get_page(self, page_id: int) -> Dict:
        """Fetch page from WordPress REST API"""
        url = f"{self.wp_url}/?rest_route=/wp/v2/pages/{page_id}&context=edit"
        response = requests.get(
            url,
            auth=HTTPBasicAuth(self.wp_user, self.wp_password)
        )
        response.raise_for_status()
        return response.json()

    def update_page(self, page_id: int, content: str, title: str = None) -> Dict:
        """Update page content via WordPress REST API"""
        url = f"{self.wp_url}/?rest_route=/wp/v2/pages/{page_id}"

        data = {"content": content}
        if title:
            data["title"] = title

        response = requests.post(
            url,
            auth=HTTPBasicAuth(self.wp_user, self.wp_password),
            json=data
        )
        response.raise_for_status()
        return response.json()

    def extract_text_nodes(self, html: str) -> Tuple[str, List[Dict]]:
        """
        Extract text nodes from HTML while preserving structure.
        Returns modified HTML with placeholders and a list of text nodes.
        """
        soup = BeautifulSoup(html, 'html.parser')
        text_nodes = []
        placeholder_counter = [0]  # Use list for mutable counter in nested function

        # Tags whose text content should be translated
        translatable_tags = {
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',  # Headings
            'p', 'span', 'a', 'li', 'td', 'th',   # Text containers
            'label', 'button', 'figcaption',      # UI elements
            'blockquote', 'cite', 'em', 'strong'  # Formatting
        }

        # Tags to skip entirely
        skip_tags = {'script', 'style', 'code', 'pre', 'svg', 'path'}

        def process_element(element):
            if element.name in skip_tags:
                return

            for child in list(element.children):
                if isinstance(child, NavigableString):
                    text = str(child).strip()
                    # Skip empty text, numbers only, or very short text
                    if text and len(text) > 2 and not text.replace('.', '').replace(',', '').isdigit():
                        placeholder = f"__TEXT_PLACEHOLDER_{placeholder_counter[0]}__"
                        text_nodes.append({
                            'id': placeholder_counter[0],
                            'text': text,
                            'parent_tag': element.name,
                            'placeholder': placeholder
                        })
                        child.replace_with(NavigableString(placeholder))
                        placeholder_counter[0] += 1
                elif child.name:
                    process_element(child)

        # Process all elements
        for element in soup.find_all(True):
            if element.name not in skip_tags:
                process_element(element)

        return str(soup), text_nodes

    def translate_texts_batch(self, text_nodes: List[Dict],
                              source_lang: str = 'en',
                              target_lang: str = 'de',
                              batch_size: int = 20) -> List[Dict]:
        """
        Translate text nodes in batches with SEO optimization.
        """
        translated_nodes = []

        for i in range(0, len(text_nodes), batch_size):
            batch = text_nodes[i:i + batch_size]

            # Prepare texts for translation
            texts_to_translate = []
            for node in batch:
                texts_to_translate.append({
                    'id': node['id'],
                    'text': node['text'],
                    'tag': node['parent_tag']
                })

            # Create translation prompt
            prompt = f"""Übersetze die folgenden Texte von Englisch nach Deutsch.

WICHTIGE REGELN:
1. SEO-OPTIMIERUNG: Integriere natürlich relevante Keywords wo passend:
   {', '.join(self.seo_keywords[:8])}
2. Professioneller, geschäftlicher Ton (B2B Facility Management)
3. Keine direkte 1:1 Übersetzung - verbessere den Text für deutsche Leser
4. Bei Überschriften (h1-h6): Prägnant und keyword-reich
5. Placeholder-Texte wie "Lorem ipsum" durch sinnvollen deutschen FM-Content ersetzen
6. Behalte die Bedeutung, aber optimiere für SEO

TEXTE ZU ÜBERSETZEN (JSON):
{json.dumps(texts_to_translate, ensure_ascii=False, indent=2)}

ANTWORT-FORMAT (nur JSON, keine Erklärung):
[
  {{"id": 0, "translated": "Übersetzter Text"}},
  {{"id": 1, "translated": "Übersetzter Text"}}
]
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Du bist ein professioneller Übersetzer und SEO-Spezialist für Facility Management in Deutschland.
Deine Aufgabe:
- Übersetze Englisch nach Deutsch
- Optimiere für SEO mit Facility Management Keywords
- Ersetze Lorem Ipsum durch sinnvollen deutschen Content
- Professioneller B2B-Ton
Antworte NUR mit dem JSON-Array, keine zusätzlichen Erklärungen."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=4000
            )

            # Parse response
            response_text = response.choices[0].message.content

            # Extract JSON from response
            try:
                # Try to find JSON in response
                json_match = re.search(r'\[[\s\S]*\]', response_text)
                if json_match:
                    translations = json.loads(json_match.group())
                else:
                    translations = json.loads(response_text)

                # Map translations back to nodes
                translation_map = {t['id']: t['translated'] for t in translations}

                for node in batch:
                    translated_text = translation_map.get(node['id'], node['text'])
                    translated_nodes.append({
                        **node,
                        'translated': translated_text
                    })

            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse batch {i//batch_size + 1}: {e}")
                # Fallback: keep original texts
                for node in batch:
                    translated_nodes.append({
                        **node,
                        'translated': node['text']
                    })

        return translated_nodes

    def replace_placeholders(self, html_with_placeholders: str,
                            translated_nodes: List[Dict]) -> str:
        """Replace placeholders with translated text"""
        result = html_with_placeholders

        for node in translated_nodes:
            result = result.replace(node['placeholder'], node['translated'])

        return result

    def translate_page(self, page_id: int,
                       source_lang: str = 'en',
                       target_lang: str = 'de',
                       dry_run: bool = True) -> Dict:
        """
        Main method: Translate a WordPress page while preserving structure.

        Args:
            page_id: WordPress page ID
            source_lang: Source language code
            target_lang: Target language code
            dry_run: If True, don't actually update the page

        Returns:
            Dict with original and translated content
        """
        print(f"Fetching page {page_id}...")
        page = self.get_page(page_id)

        original_content = page.get('content', {}).get('raw', '')
        original_title = page.get('title', {}).get('raw', '')

        if not original_content:
            raise ValueError(f"No content found for page {page_id}")

        print(f"Original title: {original_title}")
        print(f"Content length: {len(original_content)} chars")

        # Step 1: Extract text nodes
        print("Extracting text nodes...")
        html_with_placeholders, text_nodes = self.extract_text_nodes(original_content)
        print(f"Found {len(text_nodes)} text nodes to translate")

        if len(text_nodes) == 0:
            print("No text nodes found to translate!")
            return {
                'page_id': page_id,
                'original_title': original_title,
                'original_content': original_content,
                'translated_content': original_content,
                'text_nodes': 0
            }

        # Step 2: Translate texts in batches
        print("Translating texts with SEO optimization...")
        translated_nodes = self.translate_texts_batch(
            text_nodes, source_lang, target_lang
        )

        # Step 3: Replace placeholders
        print("Rebuilding HTML with translated text...")
        translated_content = self.replace_placeholders(
            html_with_placeholders, translated_nodes
        )

        # Step 4: Translate title
        print("Translating title...")
        title_response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Du bist SEO-Spezialist für Facility Management. Übersetze den Titel und optimiere ihn für deutsche Suchmaschinen."
                },
                {
                    "role": "user",
                    "content": f"Übersetze diesen Seitentitel nach Deutsch mit SEO-Optimierung für Facility Management:\n\n{original_title}"
                }
            ],
            temperature=0.3,
            max_tokens=100
        )
        translated_title = title_response.choices[0].message.content.strip()

        result = {
            'page_id': page_id,
            'original_title': original_title,
            'translated_title': translated_title,
            'original_content': original_content,
            'translated_content': translated_content,
            'text_nodes': len(text_nodes),
            'translations': [(n['text'][:50], n['translated'][:50]) for n in translated_nodes[:10]]
        }

        # Step 5: Update page if not dry run
        if not dry_run:
            print("Updating page on WordPress...")
            update_result = self.update_page(page_id, translated_content, translated_title)
            result['updated'] = True
            result['wordpress_response'] = update_result.get('id')
            print(f"✅ Page {page_id} updated successfully!")
        else:
            result['updated'] = False
            print("Dry run - page not updated. Use dry_run=False to apply changes.")

        return result

    def preview_translation(self, page_id: int, max_nodes: int = 10) -> None:
        """Preview translation without applying changes"""
        page = self.get_page(page_id)
        content = page.get('content', {}).get('raw', '')

        _, text_nodes = self.extract_text_nodes(content)

        print(f"\n=== Preview: Page {page_id} ===")
        print(f"Title: {page.get('title', {}).get('raw', 'N/A')}")
        print(f"Total text nodes: {len(text_nodes)}")
        print(f"\nFirst {max_nodes} text nodes:")

        for i, node in enumerate(text_nodes[:max_nodes]):
            print(f"\n[{i+1}] Tag: <{node['parent_tag']}>")
            print(f"    Text: {node['text'][:100]}{'...' if len(node['text']) > 100 else ''}")


if __name__ == '__main__':
    translator = PageTranslator()

    # Preview what will be translated
    print("=== PREVIEW MODE ===")
    translator.preview_translation(9161, max_nodes=15)

    print("\n" + "="*50)
    print("To translate, run:")
    print("  result = translator.translate_page(9161, dry_run=True)  # Preview")
    print("  result = translator.translate_page(9161, dry_run=False) # Apply")
