"""
Django management command to run the MediaFileWatcher.

Usage:
    python manage.py watch_media
    python manage.py watch_media --path /custom/path
    python manage.py watch_media --no-recursive
    python manage.py watch_media --auto-upload
    python manage.py watch_media --no-scan
"""

import signal
import sys
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Watch media directory for changes and sync with database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default=None,
            help='Directory to watch (default: MEDIA_ROOT)',
        )
        parser.add_argument(
            '--no-recursive',
            action='store_true',
            help='Do not watch subdirectories',
        )
        parser.add_argument(
            '--auto-upload',
            action='store_true',
            help='Automatically upload new files to WordPress',
        )
        parser.add_argument(
            '--no-scan',
            action='store_true',
            help='Skip scanning existing files on startup',
        )
        parser.add_argument(
            '--debounce',
            type=float,
            default=1.0,
            help='Debounce time in seconds (default: 1.0)',
        )

    def handle(self, *args, **options):
        from apps.media.watcher import MediaFileWatcher

        watch_path = options['path'] or settings.MEDIA_ROOT
        recursive = not options['no_recursive']
        auto_upload = options['auto_upload']
        scan_existing = not options['no_scan']
        debounce = options['debounce']

        self.stdout.write(
            self.style.SUCCESS(f'Starting MediaFileWatcher...')
        )
        self.stdout.write(f'  Path: {watch_path}')
        self.stdout.write(f'  Recursive: {recursive}')
        self.stdout.write(f'  Auto-upload: {auto_upload}')
        self.stdout.write(f'  Debounce: {debounce}s')
        self.stdout.write('')

        watcher = MediaFileWatcher(
            watch_path=watch_path,
            recursive=recursive,
            debounce_seconds=debounce,
            auto_upload=auto_upload,
        )

        # Handle graceful shutdown
        def signal_handler(signum, frame):
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Stopping watcher...'))
            watcher.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Scan existing files if requested
        if scan_existing:
            self.stdout.write('Scanning existing files...')
            count = watcher.scan_existing()
            self.stdout.write(
                self.style.SUCCESS(f'Added {count} files to database')
            )
            self.stdout.write('')

        # Start watching
        self.stdout.write(
            self.style.SUCCESS('Watching for changes... (Ctrl+C to stop)')
        )
        watcher.run_forever()
