"""
WordPress Page Translator: English to German
Detects English text in German pages and translates to German
"""

import os
import re
import json
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup, NavigableString
from openai import OpenAI
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth
from langdetect import detect, LangDetectException

# Load environment
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k] = v


class EnglishToGermanTranslator:
    """Translates English content to German in WordPress pages"""

    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"

        # WordPress
        self.wp_url = os.getenv('WP_SITE_URL', 'https://profm24.de')
        self.wp_user = os.getenv('WP_USERNAME', 'admin')
        self.wp_password = os.getenv('WP_APP_PASSWORD', '').strip()
        self.auth = HTTPBasicAuth(self.wp_user, self.wp_password)

        # SEO keywords for Facility Management
        self.seo_keywords = [
            "Facility Management", "Gebäudemanagement", "Gebäudetechnik",
            "Instandhaltung", "Gebäudereinigung", "Energieeffizienz",
            "Gebäudeautomation", "Technisches Gebäudemanagement",
            "Wartung", "Objektbetreuung", "Hausmeisterservice"
        ]

    def is_english(self, text: str) -> bool:
        """Detect if text is in English"""
        if not text or len(text.strip()) < 10:
            return False
        try:
            # Clean text for detection
            clean = re.sub(r'[^\w\s]', '', text)
            if len(clean.strip()) < 5:
                return False
            lang = detect(clean)
            return lang == 'en'
        except LangDetectException:
            return False

    def get_pages(self, language: str = 'de', per_page: int = 50) -> List[Dict]:
        """Get pages from WordPress"""
        url = f"{self.wp_url}/?rest_route=/wp/v2/pages&per_page={per_page}&wpml_language={language}"
        r = requests.get(url, auth=self.auth)
        r.raise_for_status()
        return r.json()

    def get_posts(self, language: str = 'de', per_page: int = 50) -> List[Dict]:
        """Get posts from WordPress"""
        url = f"{self.wp_url}/?rest_route=/wp/v2/posts&per_page={per_page}&wpml_language={language}"
        r = requests.get(url, auth=self.auth)
        r.raise_for_status()
        return r.json()

    def get_page(self, page_id: int, language: str = 'de') -> Dict:
        """Get single page with full content"""
        url = f"{self.wp_url}/?rest_route=/wp/v2/pages/{page_id}&context=edit&wpml_language={language}"
        r = requests.get(url, auth=self.auth)
        r.raise_for_status()
        return r.json()

    def get_post(self, post_id: int, language: str = 'de') -> Dict:
        """Get single post with full content"""
        url = f"{self.wp_url}/?rest_route=/wp/v2/posts/{post_id}&context=edit&wpml_language={language}"
        r = requests.get(url, auth=self.auth)
        r.raise_for_status()
        return r.json()

    def update_page(self, page_id: int, content: str, title: str = None, language: str = 'de') -> Dict:
        """Update page content"""
        url = f"{self.wp_url}/?rest_route=/wp/v2/pages/{page_id}&wpml_language={language}"
        data = {"content": content}
        if title:
            data["title"] = title
        r = requests.post(url, auth=self.auth, json=data)
        r.raise_for_status()
        return r.json()

    def update_post(self, post_id: int, content: str, title: str = None, language: str = 'de') -> Dict:
        """Update post content"""
        url = f"{self.wp_url}/?rest_route=/wp/v2/posts/{post_id}&wpml_language={language}"
        data = {"content": content}
        if title:
            data["title"] = title
        r = requests.post(url, auth=self.auth, json=data)
        r.raise_for_status()
        return r.json()

    def extract_text_segments(self, html: str) -> Tuple[str, List[Dict]]:
        """Extract text segments from HTML, return placeholders and segments"""
        soup = BeautifulSoup(html, 'html.parser')
        segments = []
        counter = [0]

        skip_tags = {'script', 'style', 'code', 'pre', 'svg', 'path', 'noscript'}

        def process(element):
            if element.name in skip_tags:
                return
            for child in list(element.children):
                if isinstance(child, NavigableString):
                    text = str(child).strip()
                    if text and len(text) > 3:
                        placeholder = f"__SEG_{counter[0]}__"
                        segments.append({
                            'id': counter[0],
                            'text': text,
                            'tag': element.name,
                            'placeholder': placeholder,
                            'is_english': self.is_english(text)
                        })
                        child.replace_with(NavigableString(placeholder))
                        counter[0] += 1
                elif child.name:
                    process(child)

        for el in soup.find_all(True):
            if el.name not in skip_tags:
                process(el)

        return str(soup), segments

    def translate_batch(self, segments: List[Dict], batch_size: int = 25) -> List[Dict]:
        """Translate English segments to German"""
        translated = []

        # Filter only English segments
        english_segments = [s for s in segments if s['is_english']]
        german_segments = [s for s in segments if not s['is_english']]

        # Keep German segments as-is
        for seg in german_segments:
            seg['translated'] = seg['text']
            translated.append(seg)

        if not english_segments:
            return translated

        print(f"  Found {len(english_segments)} English segments to translate")

        # Translate English segments in batches
        for i in range(0, len(english_segments), batch_size):
            batch = english_segments[i:i + batch_size]

            texts = [{'id': s['id'], 'text': s['text'], 'tag': s['tag']} for s in batch]

            prompt = f"""Übersetze diese englischen Texte ins Deutsche.

REGELN:
1. Professioneller B2B-Ton für Facility Management
2. SEO-optimiert mit Keywords: {', '.join(self.seo_keywords[:6])}
3. Natürliches Deutsch, keine wörtliche Übersetzung
4. Überschriften (h1-h6): Prägnant und aussagekräftig
5. Fachbegriffe korrekt übersetzen

TEXTE:
{json.dumps(texts, ensure_ascii=False, indent=2)}

ANTWORT NUR ALS JSON-ARRAY:
[{{"id": 0, "translated": "Deutscher Text"}}, ...]"""

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Du bist Übersetzer für Facility Management. Antworte nur mit JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=4000
                )

                response_text = response.choices[0].message.content
                json_match = re.search(r'\[[\s\S]*\]', response_text)
                if json_match:
                    translations = json.loads(json_match.group())
                    trans_map = {t['id']: t['translated'] for t in translations}

                    for seg in batch:
                        seg['translated'] = trans_map.get(seg['id'], seg['text'])
                        translated.append(seg)
                else:
                    for seg in batch:
                        seg['translated'] = seg['text']
                        translated.append(seg)

            except Exception as e:
                print(f"  Translation error: {e}")
                for seg in batch:
                    seg['translated'] = seg['text']
                    translated.append(seg)

        return translated

    def rebuild_html(self, html_template: str, segments: List[Dict]) -> str:
        """Replace placeholders with translated text"""
        result = html_template
        for seg in segments:
            result = result.replace(seg['placeholder'], seg['translated'])
        return result

    def translate_content(self, content_id: int, content_type: str = 'page',
                         dry_run: bool = True) -> Dict:
        """Main translation method"""

        # Get content
        if content_type == 'page':
            item = self.get_page(content_id)
        else:
            item = self.get_post(content_id)

        title = item.get('title', {}).get('raw', '')
        content = item.get('content', {}).get('raw', '')

        print(f"\n{'='*50}")
        print(f"Translating {content_type} [{content_id}]: {title}")
        print(f"Content length: {len(content)} chars")

        if not content:
            return {'id': content_id, 'status': 'skipped', 'reason': 'no content'}

        # Extract and translate
        html_template, segments = self.extract_text_segments(content)
        english_count = sum(1 for s in segments if s['is_english'])

        print(f"  Total segments: {len(segments)}, English: {english_count}")

        if english_count == 0:
            print("  No English content found - skipping")
            return {'id': content_id, 'status': 'skipped', 'reason': 'no english'}

        # Translate
        translated_segments = self.translate_batch(segments)
        new_content = self.rebuild_html(html_template, translated_segments)

        # Translate title if English
        new_title = title
        if self.is_english(title):
            print(f"  Translating title: {title}")
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Übersetze ins Deutsche. Nur die Übersetzung, keine Erklärung."},
                        {"role": "user", "content": f"Übersetze: {title}"}
                    ],
                    temperature=0.3,
                    max_tokens=100
                )
                new_title = resp.choices[0].message.content.strip()
            except:
                pass

        result = {
            'id': content_id,
            'type': content_type,
            'original_title': title,
            'new_title': new_title,
            'segments_total': len(segments),
            'segments_translated': english_count,
            'content_changed': new_content != content
        }

        # Apply changes
        if not dry_run and new_content != content:
            print(f"  Applying changes...")
            if content_type == 'page':
                self.update_page(content_id, new_content, new_title if new_title != title else None)
            else:
                self.update_post(content_id, new_content, new_title if new_title != title else None)
            result['status'] = 'updated'
            print(f"  ✅ Updated!")
        else:
            result['status'] = 'dry_run' if dry_run else 'no_changes'
            print(f"  {'Dry run - not applied' if dry_run else 'No changes needed'}")

        return result

    def translate_all(self, content_type: str = 'pages', dry_run: bool = True,
                     limit: int = None) -> List[Dict]:
        """Translate all pages or posts"""

        print(f"\n{'='*60}")
        print(f"TRANSLATING ALL {content_type.upper()} (English → German)")
        print(f"Dry run: {dry_run}")
        print(f"{'='*60}")

        # Get items
        if content_type == 'pages':
            items = self.get_pages(language='de', per_page=100)
        else:
            items = self.get_posts(language='de', per_page=100)

        if limit:
            items = items[:limit]

        print(f"Found {len(items)} {content_type} to process")

        results = []
        for item in items:
            item_id = item.get('id')
            item_type = 'page' if content_type == 'pages' else 'post'
            result = self.translate_content(item_id, item_type, dry_run)
            results.append(result)

        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        updated = sum(1 for r in results if r.get('status') == 'updated')
        skipped = sum(1 for r in results if r.get('status') == 'skipped')
        print(f"Total processed: {len(results)}")
        print(f"Updated: {updated}")
        print(f"Skipped: {skipped}")

        return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Translate English content to German')
    parser.add_argument('--type', choices=['pages', 'posts', 'all'], default='pages',
                       help='Content type to translate')
    parser.add_argument('--id', type=int, help='Translate specific page/post ID')
    parser.add_argument('--apply', action='store_true', help='Apply changes (default: dry run)')
    parser.add_argument('--limit', type=int, help='Limit number of items')
    args = parser.parse_args()

    translator = EnglishToGermanTranslator()

    if args.id:
        # Single item
        content_type = 'post' if args.type == 'posts' else 'page'
        translator.translate_content(args.id, content_type, dry_run=not args.apply)
    elif args.type == 'all':
        # All pages and posts
        translator.translate_all('pages', dry_run=not args.apply, limit=args.limit)
        translator.translate_all('posts', dry_run=not args.apply, limit=args.limit)
    else:
        # Specific type
        translator.translate_all(args.type, dry_run=not args.apply, limit=args.limit)


if __name__ == '__main__':
    main()
