#!/usr/bin/env python3
"""
Apply translation to WordPress page with rollback capability.
Only modifies text content, preserves HTML structure completely.
"""

import os
import json
import re
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

WP_SITE_URL = os.getenv("WP_SITE_URL", "https://profm24.de")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")


def get_page(page_id: int) -> dict:
    """Fetch WordPress page."""
    url = f"{WP_SITE_URL}/?rest_route=/wp/v2/pages/{page_id}"
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    response = requests.get(url, auth=auth)
    response.raise_for_status()
    return response.json()


def update_page(page_id: int, content: str, title: str = None) -> dict:
    """Update WordPress page content."""
    url = f"{WP_SITE_URL}/?rest_route=/wp/v2/pages/{page_id}"
    auth = (WP_USERNAME, WP_APP_PASSWORD)

    data = {"content": content}
    if title:
        data["title"] = title

    response = requests.post(url, auth=auth, json=data)
    response.raise_for_status()
    return response.json()


def safe_replace_text(content: str, translations: dict) -> str:
    """
    Safely replace text content without touching HTML structure.
    Only replaces text between > and < tags.
    """
    translated = content

    for original, translation in translations.items():
        if not original or not translation or original == translation:
            continue

        # Skip placeholder Latin text
        if 'lorem' in original.lower() or 'ipsum' in original.lower():
            continue

        # Skip names (keep original)
        if original in ['Alice Howard', 'Henry Sanchez', 'Nathan Marshall',
                       'Emma Romero', 'John Romero', 'Judy Wells',
                       'Philip Larson', 'Jean Scott', 'Miguel Anders', 'Evelyn Grant']:
            continue

        # Pattern 1: Text between tags (most common)
        # Match >original< and replace with >translated<
        pattern = f'>{re.escape(original)}<'
        replacement = f'>{translation}<'
        translated = translated.replace(pattern, replacement)

        # Pattern 2: Text in alt attributes
        pattern = f'alt="{re.escape(original)}"'
        replacement = f'alt="{translation}"'
        translated = translated.replace(pattern, replacement)

        # Pattern 3: Text in title attributes
        pattern = f'title="{re.escape(original)}"'
        replacement = f'title="{translation}"'
        translated = translated.replace(pattern, replacement)

    return translated


def apply_translations(page_id: int, translations_file: str):
    """Apply translations to WordPress page."""

    print("=" * 60)
    print("APPLYING TRANSLATIONS TO WORDPRESS")
    print("=" * 60)

    # Load translations
    with open(translations_file, 'r', encoding='utf-8') as f:
        report = json.load(f)

    translations = report.get('translations', {})
    translated_title = report.get('translated_title')

    print(f"\nPage ID: {page_id}")
    print(f"Translations to apply: {len(translations)}")

    # Get current page content
    print("\n[1/4] Fetching current page content...")
    page = get_page(page_id)
    original_content = page.get('content', {}).get('rendered', '')
    original_title = page.get('title', {}).get('rendered', '')

    print(f"   Original title: {original_title}")
    print(f"   Content length: {len(original_content)} chars")

    # Apply translations
    print("\n[2/4] Applying translations (text only, preserving HTML)...")
    translated_content = safe_replace_text(original_content, translations)

    # Count changes
    changes = sum(1 for orig, trans in translations.items()
                  if orig != trans and f'>{trans}<' in translated_content)
    print(f"   Applied {changes} text replacements")

    # Verify HTML structure is intact
    print("\n[3/4] Verifying HTML structure...")
    original_tags = len(re.findall(r'<[^>]+>', original_content))
    translated_tags = len(re.findall(r'<[^>]+>', translated_content))

    if original_tags != translated_tags:
        print(f"   WARNING: Tag count changed! Original: {original_tags}, New: {translated_tags}")
        print("   ABORTING to prevent structure damage!")
        return False

    print(f"   HTML tags preserved: {original_tags} tags (unchanged)")

    # Update WordPress
    print("\n[4/4] Updating WordPress page...")

    try:
        # Note: We keep the original title since "Main Home" might be used programmatically
        result = update_page(page_id, translated_content)
        print(f"   SUCCESS! Page updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Page link: {result.get('link', WP_SITE_URL)}")

        # Save applied content for verification
        with open('/app/applied_content.html', 'w', encoding='utf-8') as f:
            f.write(translated_content)
        print("   Applied content saved to: applied_content.html")

        return True

    except Exception as e:
        print(f"   ERROR: {e}")
        return False


def rollback(page_id: int, backup_file: str):
    """Rollback to original content."""
    print("=" * 60)
    print("ROLLBACK - Restoring original content")
    print("=" * 60)

    with open(backup_file, 'r', encoding='utf-8') as f:
        backup = json.load(f)

    original_content = backup.get('content', {}).get('rendered', '')
    original_title = backup.get('title', {}).get('rendered', '')

    print(f"\nRestoring page {page_id}...")
    print(f"   Title: {original_title}")
    print(f"   Content length: {len(original_content)} chars")

    try:
        result = update_page(page_id, original_content, original_title)
        print(f"\n   SUCCESS! Page restored to original state.")
        print(f"   Page link: {result.get('link')}")
        return True
    except Exception as e:
        print(f"\n   ERROR during rollback: {e}")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        # Find latest backup
        import glob
        backups = sorted(glob.glob('/app/backup_page_9161_*.json'))
        if backups:
            rollback(9161, backups[-1])
        else:
            print("No backup files found!")
    else:
        apply_translations(9161, '/app/translation_report.json')
