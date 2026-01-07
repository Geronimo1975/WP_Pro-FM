#!/usr/bin/env python3
"""
ProFM24 Glossary Progress Dashboard
Real-time monitoring of glossary generation and sync progress.

Usage:
    python progress_dashboard.py
    python progress_dashboard.py --watch
    python progress_dashboard.py --export
"""

import argparse
import json
import time
import sys
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

from config import Config, CATEGORIES, LETTER_TARGETS, TOTAL_TERMS_TARGET


def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(Config.get_db_connection_string())


def get_statistics():
    """Get comprehensive statistics."""
    conn = get_db_connection()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Overall stats
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_published) as published,
                COUNT(*) FILTER (WHERE wordpress_post_id IS NOT NULL) as synced,
                COUNT(*) FILTER (WHERE focus_keyword IS NOT NULL) as seo_optimized,
                COUNT(DISTINCT letter) as letters_covered,
                COUNT(DISTINCT category) as categories_used,
                SUM(search_volume) as total_volume,
                AVG(LENGTH(definition)) as avg_definition,
                COUNT(*) FILTER (WHERE priority = 1) as priority_1,
                COUNT(*) FILTER (WHERE priority = 2) as priority_2,
                MAX(created_at) as last_created
            FROM fm_glossar_terms
        """)
        overall = cur.fetchone()

        # By letter
        cur.execute("""
            SELECT letter, COUNT(*) as count
            FROM fm_glossar_terms
            GROUP BY letter
            ORDER BY letter
        """)
        by_letter = {row['letter']: row['count'] for row in cur.fetchall()}

        # By category
        cur.execute("""
            SELECT category, COUNT(*) as count, SUM(search_volume) as volume
            FROM fm_glossar_terms
            GROUP BY category
            ORDER BY count DESC
        """)
        by_category = cur.fetchall()

        # Recent terms
        cur.execute("""
            SELECT term, category, search_volume, created_at
            FROM fm_glossar_terms
            ORDER BY created_at DESC
            LIMIT 5
        """)
        recent = cur.fetchall()

    conn.close()

    return {
        'overall': overall,
        'by_letter': by_letter,
        'by_category': by_category,
        'recent': recent
    }


def render_progress_bar(current: int, total: int, width: int = 30) -> str:
    """Render ASCII progress bar."""
    if total == 0:
        return '░' * width
    filled = int(width * current / total)
    return '█' * filled + '░' * (width - filled)


def render_dashboard(stats: dict, clear: bool = True):
    """Render dashboard to console."""
    if clear:
        print('\033[2J\033[H', end='')  # Clear screen

    overall = stats['overall']
    by_letter = stats['by_letter']
    by_category = stats['by_category']
    recent = stats['recent']

    total = overall['total'] or 0
    target = TOTAL_TERMS_TARGET
    progress = total / target * 100 if target > 0 else 0

    print("╔" + "═" * 70 + "╗")
    print("║" + " ProFM24 GLOSSARY DASHBOARD ".center(70) + "║")
    print("╠" + "═" * 70 + "╣")

    # Overall progress
    print("║ OVERALL PROGRESS".ljust(71) + "║")
    print("║" + "-" * 70 + "║")

    bar = render_progress_bar(total, target, 40)
    print(f"║   Terms: {total:4} / {target:4}  [{bar}] {progress:5.1f}%".ljust(71) + "║")

    synced = overall['synced'] or 0
    seo = overall['seo_optimized'] or 0
    print(f"║   Published: {overall['published'] or 0:4}  |  Synced to WP: {synced:4}  |  SEO Optimized: {seo:4}".ljust(71) + "║")

    volume = overall['total_volume'] or 0
    print(f"║   Search Volume: {volume:,}/month  |  Letters: {overall['letters_covered'] or 0}/26  |  Categories: {overall['categories_used'] or 0}/15".ljust(71) + "║")

    print("╠" + "═" * 70 + "╣")

    # Letter progress
    print("║ BY LETTER".ljust(71) + "║")
    print("║" + "-" * 70 + "║")

    line = "║   "
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        current = by_letter.get(letter, 0)
        target_l = LETTER_TARGETS.get(letter, 0)
        if current >= target_l and target_l > 0:
            status = '✓'
        elif current > 0:
            status = str(current)[-1]  # Last digit
        else:
            status = '·'
        line += f"{letter}:{status} "
        if letter in 'IMZ':  # Line breaks
            print(line.ljust(71) + "║")
            line = "║   "

    if line.strip() != "║":
        print(line.ljust(71) + "║")

    print("╠" + "═" * 70 + "╣")

    # Top categories
    print("║ TOP CATEGORIES".ljust(71) + "║")
    print("║" + "-" * 70 + "║")

    for cat in by_category[:6]:
        name = cat['category'][:35]
        count = cat['count']
        volume = cat['volume'] or 0
        bar = render_progress_bar(count, 50, 15)
        print(f"║   {name:35} {count:3} [{bar}] {volume:,}/mo".ljust(71) + "║")

    print("╠" + "═" * 70 + "╣")

    # Recent activity
    print("║ RECENT TERMS".ljust(71) + "║")
    print("║" + "-" * 70 + "║")

    for term in recent:
        name = term['term'][:40]
        cat = term['category'][:15]
        vol = term['search_volume'] or 0
        print(f"║   • {name:40} | {cat:15} | {vol:,}/mo".ljust(71) + "║")

    print("╠" + "═" * 70 + "╣")

    # Footer
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    last = overall['last_created']
    last_str = last.strftime('%H:%M:%S') if last else 'N/A'

    print(f"║ Updated: {now}  |  Last term: {last_str}".ljust(71) + "║")
    print("╚" + "═" * 70 + "╝")


def watch_mode(interval: int = 10):
    """Continuously update dashboard."""
    print("Starting watch mode. Press Ctrl+C to exit.\n")
    try:
        while True:
            stats = get_statistics()
            render_dashboard(stats)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\nDashboard stopped.")


def export_stats(output_path: str = None):
    """Export statistics to JSON."""
    stats = get_statistics()

    # Convert datetime objects
    def convert(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj

    output = {
        'generated_at': datetime.now().isoformat(),
        'target': TOTAL_TERMS_TARGET,
        'overall': {k: convert(v) for k, v in stats['overall'].items()},
        'by_letter': stats['by_letter'],
        'by_category': [{k: convert(v) for k, v in cat.items()} for cat in stats['by_category']],
        'recent': [{k: convert(v) for k, v in term.items()} for term in stats['recent']]
    }

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Statistics exported to: {output_path}")
    else:
        print(json.dumps(output, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='ProFM24 Glossary Progress Dashboard')
    parser.add_argument('--watch', '-w', action='store_true', help='Continuous update mode')
    parser.add_argument('--interval', '-i', type=int, default=10, help='Update interval in seconds')
    parser.add_argument('--export', '-e', nargs='?', const=True, help='Export stats to JSON file')
    parser.add_argument('--no-clear', action='store_true', help='Don\'t clear screen')

    args = parser.parse_args()

    if args.export:
        output_path = args.export if isinstance(args.export, str) else None
        export_stats(output_path)
        return

    if args.watch:
        watch_mode(args.interval)
        return

    # Single render
    stats = get_statistics()
    render_dashboard(stats, clear=not args.no_clear)


if __name__ == '__main__':
    main()
