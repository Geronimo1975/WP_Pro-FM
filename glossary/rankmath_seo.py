#!/usr/bin/env python3
"""
ProFM24 RankMath SEO Manager
General-purpose SEO optimization for all WordPress pages and posts.

Features:
- List all pages/posts with SEO status
- Generate AI-powered meta titles and descriptions
- Update RankMath focus keywords
- Bulk optimize content

Usage:
    python rankmath_seo.py status                    # Show SEO status for all content
    python rankmath_seo.py list --type pages         # List pages with SEO info
    python rankmath_seo.py list --type posts         # List posts with SEO info
    python rankmath_seo.py optimize --id 123         # Optimize single page/post
    python rankmath_seo.py optimize --type pages     # Optimize all pages
    python rankmath_seo.py analyze --id 123          # Analyze SEO for single item
"""

import argparse
import json
import time
import sys
from typing import Optional, List, Dict, Any

import requests
from requests.auth import HTTPBasicAuth
from openai import OpenAI

from config import Config

# Initialize clients
openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
WP_AUTH = HTTPBasicAuth(Config.WP_USERNAME, Config.WP_APP_PASSWORD)
WP_HEADERS = {'Content-Type': 'application/json'}


class RankMathSEO:
    """RankMath SEO Manager for WordPress."""

    def __init__(self):
        self.site_url = Config.WP_SITE_URL.rstrip('/')
        self.auth = WP_AUTH

    def _api_url(self, endpoint: str) -> str:
        """Build WordPress REST API URL (Strato compatible)."""
        return f"{self.site_url}/?rest_route=/wp/v2/{endpoint}"

    def _request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> Optional[Dict]:
        """Make WordPress REST API request."""
        url = self._api_url(endpoint)

        try:
            if method == 'GET':
                response = requests.get(url, auth=self.auth, headers=WP_HEADERS, params=params)
            elif method == 'POST':
                response = requests.post(url, auth=self.auth, headers=WP_HEADERS, json=data)
            elif method == 'PUT':
                response = requests.put(url, auth=self.auth, headers=WP_HEADERS, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text[:500]}")
            return None

    def get_pages(self, per_page: int = 100, status: str = 'publish') -> List[Dict]:
        """Get all pages."""
        all_pages = []
        page = 1

        while True:
            result = self._request('GET', 'pages', params={
                'per_page': per_page,
                'page': page,
                'status': status
            })

            if not result:
                break

            all_pages.extend(result)

            if len(result) < per_page:
                break
            page += 1

        return all_pages

    def get_posts(self, per_page: int = 100, status: str = 'publish') -> List[Dict]:
        """Get all posts."""
        all_posts = []
        page = 1

        while True:
            result = self._request('GET', 'posts', params={
                'per_page': per_page,
                'page': page,
                'status': status
            })

            if not result:
                break

            all_posts.extend(result)

            if len(result) < per_page:
                break
            page += 1

        return all_posts

    def get_item(self, item_type: str, item_id: int) -> Optional[Dict]:
        """Get single page or post."""
        endpoint = 'pages' if item_type == 'page' else 'posts'
        return self._request('GET', f'{endpoint}/{item_id}')

    def update_seo(self, item_type: str, item_id: int,
                   focus_keyword: str = None,
                   meta_title: str = None,
                   meta_description: str = None) -> bool:
        """Update RankMath SEO fields via RankMath REST API."""
        meta = {}
        if focus_keyword:
            meta['rank_math_focus_keyword'] = focus_keyword
        if meta_title:
            meta['rank_math_title'] = meta_title
        if meta_description:
            meta['rank_math_description'] = meta_description

        if not meta:
            print("No SEO fields to update")
            return False

        # Use RankMath's dedicated API endpoint
        url = f"{self.site_url}/?rest_route=/rankmath/v1/updateMeta"
        data = {
            'objectID': item_id,
            'objectType': 'post',  # RankMath uses 'post' for both posts and pages
            'meta': meta
        }

        try:
            response = requests.post(url, auth=self.auth, headers=WP_HEADERS, json=data)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"RankMath API Error: {e}")
            return False

    def generate_seo(self, title: str, content: str, item_type: str = 'page') -> Dict:
        """Generate SEO meta using AI."""
        # Clean HTML from content
        import re
        clean_content = re.sub(r'<[^>]+>', '', content)
        clean_content = re.sub(r'\[.*?\]', '', clean_content)  # Remove shortcodes
        clean_content = clean_content[:2000]  # Limit for API

        prompt = f"""Du bist ein SEO-Experte für B2B Facility Management Content.

Analysiere diese WordPress {item_type} und erstelle optimierte SEO-Metadaten:

TITEL: {title}

CONTENT (Auszug):
{clean_content}

ERSTELLE (auf Deutsch):
1. focus_keyword: Das wichtigste Keyword (1-3 Wörter)
2. meta_title: SEO-Titel (max 60 Zeichen, Keyword am Anfang)
3. meta_description: Meta-Beschreibung (max 155 Zeichen, mit Call-to-Action)
4. secondary_keywords: 3-5 verwandte Keywords

KONTEXT:
- Website: ProFM24 - Facility Management Dienstleister
- Zielgruppe: Unternehmen, Facility Manager, Immobilieneigentümer
- Standort: Deutschland

Antworte NUR mit JSON:
{{
  "focus_keyword": "...",
  "meta_title": "...",
  "meta_description": "...",
  "secondary_keywords": ["...", "...", "..."],
  "seo_score_estimate": 85
}}"""

        response = openai_client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Du bist ein SEO-Experte. Antworte nur mit validem JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
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

    def analyze_item(self, item_type: str, item_id: int) -> Dict:
        """Analyze SEO status of a single item."""
        item = self.get_item(item_type, item_id)
        if not item:
            return {"error": f"{item_type} {item_id} not found"}

        title = item.get('title', {}).get('rendered', '')
        content = item.get('content', {}).get('rendered', '')
        meta = item.get('meta', {})

        # Extract RankMath fields
        focus_keyword = meta.get('rank_math_focus_keyword', '')
        meta_title = meta.get('rank_math_title', '')
        meta_description = meta.get('rank_math_description', '')

        # Word count
        import re
        clean_content = re.sub(r'<[^>]+>', '', content)
        word_count = len(clean_content.split())

        # Calculate basic SEO score
        score = 0
        issues = []

        if focus_keyword:
            score += 20
        else:
            issues.append("Missing focus keyword")

        if meta_title:
            score += 20
            if len(meta_title) > 60:
                issues.append(f"Meta title too long ({len(meta_title)} chars)")
        else:
            issues.append("Missing meta title")

        if meta_description:
            score += 20
            if len(meta_description) > 160:
                issues.append(f"Meta description too long ({len(meta_description)} chars)")
        else:
            issues.append("Missing meta description")

        if word_count >= 300:
            score += 20
        else:
            issues.append(f"Content too short ({word_count} words, need 300+)")

        if focus_keyword and focus_keyword.lower() in title.lower():
            score += 10
        else:
            issues.append("Focus keyword not in title")

        if focus_keyword and focus_keyword.lower() in content.lower():
            score += 10
        else:
            issues.append("Focus keyword not in content")

        return {
            "id": item_id,
            "type": item_type,
            "title": title,
            "url": item.get('link', ''),
            "word_count": word_count,
            "focus_keyword": focus_keyword or "(not set)",
            "meta_title": meta_title or "(not set)",
            "meta_title_length": len(meta_title) if meta_title else 0,
            "meta_description": meta_description or "(not set)",
            "meta_description_length": len(meta_description) if meta_description else 0,
            "seo_score": score,
            "issues": issues
        }

    def optimize_item(self, item_type: str, item_id: int, dry_run: bool = False) -> bool:
        """Optimize SEO for a single item."""
        print(f"\nOptimizing {item_type} ID {item_id}...")

        item = self.get_item(item_type, item_id)
        if not item:
            print(f"  {item_type} not found")
            return False

        title = item.get('title', {}).get('rendered', '')
        content = item.get('content', {}).get('rendered', '')

        print(f"  Title: {title[:50]}...")

        # Generate SEO
        print("  Generating SEO with AI...")
        try:
            seo = self.generate_seo(title, content, item_type)
        except Exception as e:
            print(f"  Error generating SEO: {e}")
            return False

        print(f"  Focus keyword: {seo['focus_keyword']}")
        print(f"  Meta title: {seo['meta_title']}")
        print(f"  Meta description: {seo['meta_description'][:60]}...")

        if dry_run:
            print("  [DRY RUN] Would update WordPress")
            return True

        # Update WordPress
        print("  Updating WordPress...")
        success = self.update_seo(
            item_type,
            item_id,
            focus_keyword=seo['focus_keyword'],
            meta_title=seo['meta_title'],
            meta_description=seo['meta_description']
        )

        if success:
            print("  Done!")
        else:
            print("  Update failed!")

        return success


def cmd_status(seo: RankMathSEO):
    """Show overall SEO status."""
    print("\nFetching pages...")
    pages = seo.get_pages()

    print("Fetching posts...")
    posts = seo.get_posts()

    # Analyze
    pages_with_seo = 0
    posts_with_seo = 0

    for page in pages:
        meta = page.get('meta', {})
        if meta.get('rank_math_focus_keyword'):
            pages_with_seo += 1

    for post in posts:
        meta = post.get('meta', {})
        if meta.get('rank_math_focus_keyword'):
            posts_with_seo += 1

    print("\n" + "="*60)
    print("RANKMATH SEO STATUS - profm24.de")
    print("="*60)
    print(f"\nPages:")
    print(f"  Total:     {len(pages)}")
    print(f"  With SEO:  {pages_with_seo}")
    print(f"  Missing:   {len(pages) - pages_with_seo}")

    print(f"\nPosts:")
    print(f"  Total:     {len(posts)}")
    print(f"  With SEO:  {posts_with_seo}")
    print(f"  Missing:   {len(posts) - posts_with_seo}")

    total = len(pages) + len(posts)
    with_seo = pages_with_seo + posts_with_seo
    pct = (with_seo / total * 100) if total > 0 else 0

    print(f"\nOverall: {with_seo}/{total} ({pct:.1f}%)")
    print("="*60)


def cmd_list(seo: RankMathSEO, item_type: str):
    """List items with SEO info."""
    print(f"\nFetching {item_type}...")

    if item_type == 'pages':
        items = seo.get_pages()
    else:
        items = seo.get_posts()

    print(f"\n{'ID':>6} {'SEO':>5} {'Title':<50} {'Focus Keyword':<25}")
    print("-" * 90)

    for item in items:
        item_id = item.get('id')
        title = item.get('title', {}).get('rendered', '')[:48]
        meta = item.get('meta', {})
        focus_kw = meta.get('rank_math_focus_keyword', '')[:23] if meta.get('rank_math_focus_keyword') else '-'

        # Simple SEO check
        has_seo = 'Yes' if meta.get('rank_math_focus_keyword') else 'No'

        print(f"{item_id:>6} {has_seo:>5} {title:<50} {focus_kw:<25}")

    print(f"\nTotal: {len(items)} {item_type}")


def cmd_analyze(seo: RankMathSEO, item_id: int, item_type: str):
    """Analyze single item SEO."""
    analysis = seo.analyze_item(item_type, item_id)

    if "error" in analysis:
        print(f"\nError: {analysis['error']}")
        return

    print("\n" + "="*60)
    print(f"SEO ANALYSIS: {analysis['title'][:50]}")
    print("="*60)
    print(f"\nURL: {analysis['url']}")
    print(f"Type: {analysis['type']}")
    print(f"Word count: {analysis['word_count']}")
    print(f"\nFocus keyword: {analysis['focus_keyword']}")
    print(f"Meta title: {analysis['meta_title']} ({analysis['meta_title_length']} chars)")
    print(f"Meta description: {analysis['meta_description'][:80]}... ({analysis['meta_description_length']} chars)")

    print(f"\nSEO Score: {analysis['seo_score']}/100")

    if analysis['issues']:
        print("\nIssues:")
        for issue in analysis['issues']:
            print(f"  - {issue}")
    else:
        print("\nNo issues found!")

    print("="*60)


def cmd_optimize(seo: RankMathSEO, item_id: int = None, item_type: str = None,
                 limit: int = None, dry_run: bool = False):
    """Optimize SEO for items."""

    if item_id:
        # Single item
        itype = 'page' if item_type in ['page', 'pages'] else 'post'
        seo.optimize_item(itype, item_id, dry_run)
        return

    # Batch optimize
    if item_type == 'pages':
        items = seo.get_pages()
        itype = 'page'
    else:
        items = seo.get_posts()
        itype = 'post'

    # Filter items without SEO
    items_to_optimize = []
    for item in items:
        meta = item.get('meta', {})
        if not meta.get('rank_math_focus_keyword'):
            items_to_optimize.append(item)

    if limit:
        items_to_optimize = items_to_optimize[:limit]

    print(f"\nOptimizing {len(items_to_optimize)} {item_type} without SEO...")
    print(f"Dry run: {dry_run}")
    print("="*50)

    success = 0
    failed = 0

    for i, item in enumerate(items_to_optimize):
        print(f"\n[{i+1}/{len(items_to_optimize)}]")

        if seo.optimize_item(itype, item['id'], dry_run):
            success += 1
        else:
            failed += 1

        # Rate limiting
        time.sleep(2.0)

    print("\n" + "="*50)
    print(f"Optimization complete!")
    print(f"  Success: {success}")
    print(f"  Failed: {failed}")
    print("="*50)


def main():
    parser = argparse.ArgumentParser(description='ProFM24 RankMath SEO Manager')
    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Status command
    subparsers.add_parser('status', help='Show overall SEO status')

    # List command
    list_parser = subparsers.add_parser('list', help='List items with SEO info')
    list_parser.add_argument('--type', '-t', choices=['pages', 'posts'], default='pages',
                            help='Type of items to list')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze SEO for single item')
    analyze_parser.add_argument('--id', '-i', type=int, required=True, help='Item ID')
    analyze_parser.add_argument('--type', '-t', choices=['page', 'post'], default='page',
                               help='Type of item')

    # Optimize command
    opt_parser = subparsers.add_parser('optimize', help='Optimize SEO')
    opt_parser.add_argument('--id', '-i', type=int, help='Single item ID')
    opt_parser.add_argument('--type', '-t', choices=['pages', 'posts', 'page', 'post'],
                           default='pages', help='Type of items')
    opt_parser.add_argument('--limit', '-l', type=int, help='Limit number of items')
    opt_parser.add_argument('--dry-run', action='store_true', help='Preview without updating')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    seo = RankMathSEO()

    if args.command == 'status':
        cmd_status(seo)
    elif args.command == 'list':
        cmd_list(seo, args.type)
    elif args.command == 'analyze':
        cmd_analyze(seo, args.id, args.type)
    elif args.command == 'optimize':
        cmd_optimize(seo, args.id, args.type, args.limit, args.dry_run)


if __name__ == '__main__':
    main()
