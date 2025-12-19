#!/usr/bin/env python3
"""
WordPress Content Translation Script for profm24.de

This script translates WordPress content (pages, posts) using OpenAI GPT-4.
It uses the ?rest_route= format for Strato hosting compatibility.

Environment variables needed (from .env):
- WP_SITE_URL: WordPress site URL (e.g., https://profm24.de)
- WP_USERNAME: WordPress admin username
- WP_APP_PASSWORD: WordPress application password
- OPENAI_API_KEY: OpenAI API key

Usage:
    python translate_wp_to_de.py --pages           # Translate all pages
    python translate_wp_to_de.py --posts           # Translate all posts
    python translate_wp_to_de.py --media           # Update media alt texts
    python translate_wp_to_de.py --page-id 123     # Translate specific page
    python translate_wp_to_de.py --post-id 456     # Translate specific post
    python translate_wp_to_de.py --dry-run         # Show what would be translated
"""

import os
import sys
import time
import argparse
import requests
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

# Configuration from environment
WP_SITE_URL = os.getenv("WP_SITE_URL", "").rstrip("/")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI API configuration
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4o"  # or "gpt-4o-mini" for cheaper option

# Default languages
SOURCE_LANG = "EN"  # Source language
TARGET_LANG = "DE"  # Target language (German)

# Rate limiting
REQUEST_DELAY = 0.5  # Seconds between API calls


def get_api_url(endpoint):
    """Generate WordPress REST API URL with ?rest_route= format for Strato hosting."""
    return f"{WP_SITE_URL}/?rest_route=/wp/v2/{endpoint}"


class WordPressClient:
    """WordPress REST API client with Strato-compatible URL format."""

    def __init__(self):
        self.session = requests.Session()
        self.session.auth = (WP_USERNAME, WP_APP_PASSWORD)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })

    def get(self, endpoint, params=None):
        """GET request to WordPress API."""
        url = get_api_url(endpoint)
        response = self.session.get(url, params=params, timeout=60)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint, data):
        """POST request to WordPress API."""
        url = get_api_url(endpoint)
        response = self.session.post(url, json=data, timeout=60)
        response.raise_for_status()
        return response.json()

    def get_all(self, endpoint, per_page=100):
        """Get all items from a paginated endpoint."""
        page = 1
        items = []
        while True:
            try:
                batch = self.get(endpoint, params={"per_page": per_page, "page": page})
                if not batch:
                    break
                items.extend(batch)
                page += 1
                time.sleep(REQUEST_DELAY)
            except requests.exceptions.HTTPError as e:
                if "rest_post_invalid_page_number" in str(e.response.text):
                    break
                raise
        return items


class OpenAITranslator:
    """OpenAI GPT-4 translator."""

    def __init__(self, api_key, source_lang="EN", target_lang="DE"):
        self.api_key = api_key
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.lang_names = {
            "DE": "German",
            "EN": "English",
            "FR": "French",
            "ES": "Spanish",
            "IT": "Italian",
            "RO": "Romanian",
            "PL": "Polish",
            "NL": "Dutch",
        }

    def translate(self, text, is_html=True):
        """Translate text using OpenAI GPT-4."""
        if not text or not text.strip():
            return text

        target_name = self.lang_names.get(self.target_lang, self.target_lang)
        source_name = self.lang_names.get(self.source_lang, self.source_lang)

        if is_html:
            system_prompt = f"""You are a professional translator specializing in website content.
Translate the following HTML content from {source_name} to {target_name}.

IMPORTANT RULES:
1. Preserve ALL HTML tags, attributes, classes, and structure exactly as they are
2. Only translate the visible text content
3. Do not translate HTML attributes like class names, IDs, URLs, or src values
4. Maintain the same formatting and line breaks
5. Use natural, professional {target_name} language appropriate for a business website
6. For technical terms related to Facility Management, use the appropriate {target_name} industry terminology
7. Return ONLY the translated HTML, no explanations"""
        else:
            system_prompt = f"""You are a professional translator.
Translate the following text from {source_name} to {target_name}.
Use natural, professional language. Return ONLY the translation, no explanations."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0.3,  # Lower temperature for more consistent translations
            "max_tokens": 16000,
        }

        try:
            response = requests.post(
                OPENAI_API_URL,
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            translated = data["choices"][0]["message"]["content"]
            return translated.strip()
        except requests.exceptions.HTTPError as e:
            print(f"  [ERROR] OpenAI translation failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response: {e.response.text[:500]}")
            return text
        except Exception as e:
            print(f"  [ERROR] Unexpected error: {e}")
            return text


def translate_page(wp_client, translator, page, dry_run=False):
    """Translate a WordPress page."""
    page_id = page["id"]
    title_original = page["title"]["rendered"]
    content_original = page["content"]["rendered"]
    excerpt_original = page.get("excerpt", {}).get("rendered", "")
    slug_original = page.get("slug", "")

    print(f"\nTranslating page {page_id}: {title_original[:50]}...")

    if dry_run:
        print(f"  [DRY RUN] Would translate:")
        print(f"    - Title: {title_original[:100]}")
        print(f"    - Content length: {len(content_original)} chars")
        print(f"    - Excerpt length: {len(excerpt_original)} chars")
        return None

    # Translate content
    print("  Translating title...")
    title_de = translator.translate(title_original, is_html=False)
    time.sleep(REQUEST_DELAY)

    print("  Translating content...")
    content_de = translator.translate(content_original, is_html=True)
    time.sleep(REQUEST_DELAY)

    if excerpt_original.strip():
        print("  Translating excerpt...")
        excerpt_de = translator.translate(excerpt_original, is_html=True)
    else:
        excerpt_de = ""

    # Create new slug
    new_slug = f"{slug_original}-de" if slug_original else f"page-{page_id}-de"

    # Create translated page as draft
    payload = {
        "title": title_de,
        "content": content_de,
        "excerpt": excerpt_de,
        "status": "draft",
        "slug": new_slug,
    }

    result = wp_client.post("pages", payload)
    print(f"  [OK] Created DE page: ID={result['id']}, slug={result['slug']}")
    return result


def translate_post(wp_client, translator, post, dry_run=False):
    """Translate a WordPress post."""
    post_id = post["id"]
    title_original = post["title"]["rendered"]
    content_original = post["content"]["rendered"]
    excerpt_original = post.get("excerpt", {}).get("rendered", "")
    slug_original = post.get("slug", "")

    print(f"\nTranslating post {post_id}: {title_original[:50]}...")

    if dry_run:
        print(f"  [DRY RUN] Would translate:")
        print(f"    - Title: {title_original[:100]}")
        print(f"    - Content length: {len(content_original)} chars")
        return None

    # Translate content
    print("  Translating title...")
    title_de = translator.translate(title_original, is_html=False)
    time.sleep(REQUEST_DELAY)

    print("  Translating content...")
    content_de = translator.translate(content_original, is_html=True)
    time.sleep(REQUEST_DELAY)

    if excerpt_original.strip():
        print("  Translating excerpt...")
        excerpt_de = translator.translate(excerpt_original, is_html=True)
    else:
        excerpt_de = ""

    # Create new slug
    new_slug = f"{slug_original}-de" if slug_original else f"post-{post_id}-de"

    # Preserve categories and tags
    payload = {
        "title": title_de,
        "content": content_de,
        "excerpt": excerpt_de,
        "status": "draft",
        "slug": new_slug,
        "categories": post.get("categories", []),
        "tags": post.get("tags", []),
    }

    result = wp_client.post("posts", payload)
    print(f"  [OK] Created DE post: ID={result['id']}, slug={result['slug']}")
    return result


def update_media_alt_text(wp_client, translator, dry_run=False):
    """Update media alt text with translations."""
    print("\nFetching media items...")
    media_items = wp_client.get_all("media")
    print(f"Found {len(media_items)} media items")

    updated = 0
    for m in media_items:
        alt = m.get("alt_text", "") or ""
        title = m.get("title", {}).get("rendered", "") or ""

        # Skip if alt text already exists
        if alt.strip():
            continue

        # Use title as source for alt text if available
        if not title.strip():
            continue

        print(f"\nUpdating media {m['id']}: {title[:50]}...")

        if dry_run:
            print(f"  [DRY RUN] Would set alt_text from title")
            continue

        alt_de = translator.translate(title, is_html=False)
        payload = {"alt_text": alt_de}

        try:
            wp_client.post(f"media/{m['id']}", payload)
            print(f"  [OK] Updated alt_text")
            updated += 1
            time.sleep(REQUEST_DELAY)
        except Exception as e:
            print(f"  [ERROR] Failed to update: {e}")

    print(f"\nUpdated {updated} media items")


def main():
    parser = argparse.ArgumentParser(description="Translate WordPress content using OpenAI GPT-4")
    parser.add_argument("--pages", action="store_true", help="Translate all pages")
    parser.add_argument("--posts", action="store_true", help="Translate all posts")
    parser.add_argument("--media", action="store_true", help="Update media alt texts")
    parser.add_argument("--page-id", type=int, help="Translate specific page by ID")
    parser.add_argument("--post-id", type=int, help="Translate specific post by ID")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--source-lang", default=SOURCE_LANG, help="Source language code (default: EN)")
    parser.add_argument("--target-lang", default=TARGET_LANG, help="Target language code (default: DE)")
    parser.add_argument("--model", default=OPENAI_MODEL, help=f"OpenAI model (default: {OPENAI_MODEL})")
    args = parser.parse_args()

    # Validate configuration
    missing = []
    if not WP_SITE_URL:
        missing.append("WP_SITE_URL")
    if not WP_USERNAME:
        missing.append("WP_USERNAME")
    if not WP_APP_PASSWORD:
        missing.append("WP_APP_PASSWORD")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")

    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("\nPlease set these in your .env file:")
        for var in missing:
            print(f"  {var}=your_value_here")
        sys.exit(1)

    # Update model if specified
    global OPENAI_MODEL
    OPENAI_MODEL = args.model

    # Initialize clients
    wp_client = WordPressClient()
    translator = OpenAITranslator(
        api_key=OPENAI_API_KEY,
        source_lang=args.source_lang,
        target_lang=args.target_lang
    )

    print(f"WordPress Site: {WP_SITE_URL}")
    print(f"OpenAI Model: {OPENAI_MODEL}")
    print(f"Translation: {args.source_lang} -> {args.target_lang}")
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
    print("-" * 50)

    # Test connection
    try:
        wp_client.get("posts", params={"per_page": 1})
        print("[OK] WordPress connection successful")
    except Exception as e:
        print(f"[ERROR] WordPress connection failed: {e}")
        sys.exit(1)

    # Execute requested operations
    if args.page_id:
        page = wp_client.get(f"pages/{args.page_id}")
        translate_page(wp_client, translator, page, args.dry_run)

    elif args.post_id:
        post = wp_client.get(f"posts/{args.post_id}")
        translate_post(wp_client, translator, post, args.dry_run)

    elif args.pages:
        print("\nFetching pages...")
        pages = wp_client.get_all("pages")
        print(f"Found {len(pages)} pages")

        for page in pages:
            # Skip already translated pages
            slug = page.get("slug", "")
            if slug.endswith("-de"):
                print(f"Skipping already translated: {slug}")
                continue
            translate_page(wp_client, translator, page, args.dry_run)
            time.sleep(REQUEST_DELAY)

    elif args.posts:
        print("\nFetching posts...")
        posts = wp_client.get_all("posts")
        print(f"Found {len(posts)} posts")

        for post in posts:
            # Skip already translated posts
            slug = post.get("slug", "")
            if slug.endswith("-de"):
                print(f"Skipping already translated: {slug}")
                continue
            translate_post(wp_client, translator, post, args.dry_run)
            time.sleep(REQUEST_DELAY)

    elif args.media:
        update_media_alt_text(wp_client, translator, args.dry_run)

    else:
        print("No action specified. Use --pages, --posts, --media, --page-id, or --post-id")
        parser.print_help()
        sys.exit(1)

    print("\nDone!")


if __name__ == "__main__":
    main()
