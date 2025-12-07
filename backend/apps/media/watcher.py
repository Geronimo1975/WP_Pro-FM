"""
MediaFileWatcher - Monitors media directory and auto-syncs changes.

Uses watchdog library to monitor file system events and trigger
synchronization with WordPress or database updates.
"""

import os
import time
import logging
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime
from threading import Thread, Event

from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    FileMovedEvent,
    DirCreatedEvent,
    DirDeletedEvent,
)

logger = logging.getLogger(__name__)


class MediaFileHandler(FileSystemEventHandler):
    """
    Handles file system events for media files.
    Filters by allowed extensions and triggers sync callbacks.
    """

    ALLOWED_EXTENSIONS = {
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico',
        # Videos
        '.mp4', '.webm', '.avi', '.mov', '.wmv', '.flv', '.mkv',
        # Audio
        '.mp3', '.wav', '.ogg', '.flac', '.aac', '.wma',
        # Documents
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    }

    def __init__(
        self,
        on_created: Optional[Callable] = None,
        on_modified: Optional[Callable] = None,
        on_deleted: Optional[Callable] = None,
        on_moved: Optional[Callable] = None,
        debounce_seconds: float = 1.0,
    ):
        super().__init__()
        self.on_created = on_created
        self.on_modified = on_modified
        self.on_deleted = on_deleted
        self.on_moved = on_moved
        self.debounce_seconds = debounce_seconds
        self._last_events = {}  # Track last event time per file

    def _is_allowed_file(self, path: str) -> bool:
        """Check if file extension is in allowed list."""
        ext = Path(path).suffix.lower()
        return ext in self.ALLOWED_EXTENSIONS

    def _should_process(self, path: str) -> bool:
        """Debounce rapid events on the same file."""
        now = time.time()
        last_time = self._last_events.get(path, 0)

        if now - last_time < self.debounce_seconds:
            return False

        self._last_events[path] = now
        return True

    def on_created(self, event: FileCreatedEvent):
        """Handle file creation event."""
        if isinstance(event, DirCreatedEvent):
            logger.debug(f"Directory created: {event.src_path}")
            return

        if not self._is_allowed_file(event.src_path):
            return

        if not self._should_process(event.src_path):
            return

        logger.info(f"File created: {event.src_path}")
        if self.on_created:
            self.on_created(event.src_path)

    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification event."""
        if event.is_directory:
            return

        if not self._is_allowed_file(event.src_path):
            return

        if not self._should_process(event.src_path):
            return

        logger.info(f"File modified: {event.src_path}")
        if self.on_modified:
            self.on_modified(event.src_path)

    def on_deleted(self, event: FileDeletedEvent):
        """Handle file deletion event."""
        if isinstance(event, DirDeletedEvent):
            logger.debug(f"Directory deleted: {event.src_path}")
            return

        if not self._is_allowed_file(event.src_path):
            return

        logger.info(f"File deleted: {event.src_path}")
        if self.on_deleted:
            self.on_deleted(event.src_path)

    def on_moved(self, event: FileMovedEvent):
        """Handle file move/rename event."""
        if event.is_directory:
            return

        src_allowed = self._is_allowed_file(event.src_path)
        dest_allowed = self._is_allowed_file(event.dest_path)

        if not (src_allowed or dest_allowed):
            return

        logger.info(f"File moved: {event.src_path} -> {event.dest_path}")
        if self.on_moved:
            self.on_moved(event.src_path, event.dest_path)


class MediaFileWatcher:
    """
    Watches a media directory for changes and synchronizes with Django database.

    Usage:
        watcher = MediaFileWatcher('/path/to/media')
        watcher.start()
        # ... do other work ...
        watcher.stop()

    Or as context manager:
        with MediaFileWatcher('/path/to/media') as watcher:
            # watcher is running
            pass
        # watcher automatically stopped
    """

    def __init__(
        self,
        watch_path: str,
        recursive: bool = True,
        debounce_seconds: float = 1.0,
        auto_upload: bool = False,
    ):
        """
        Initialize the media file watcher.

        Args:
            watch_path: Directory path to monitor
            recursive: Watch subdirectories as well
            debounce_seconds: Minimum time between events for same file
            auto_upload: Automatically upload new files to WordPress
        """
        self.watch_path = Path(watch_path).resolve()
        self.recursive = recursive
        self.debounce_seconds = debounce_seconds
        self.auto_upload = auto_upload

        self._observer: Optional[Observer] = None
        self._stop_event = Event()
        self._sync_thread: Optional[Thread] = None

        # Validate watch path
        if not self.watch_path.exists():
            self.watch_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created watch directory: {self.watch_path}")

    def _get_file_hash(self, path: str) -> str:
        """Calculate MD5 hash of file for change detection."""
        hash_md5 = hashlib.md5()
        try:
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {path}: {e}")
            return ''

    def _get_media_type(self, path: str) -> str:
        """Determine media type from file path."""
        mime_type, _ = mimetypes.guess_type(path)
        if not mime_type:
            return 'other'

        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type in ['application/pdf', 'application/msword',
                          'application/vnd.openxmlformats-officedocument']:
            return 'document'
        return 'other'

    def _ensure_django_ready(self):
        """Ensure Django is properly initialized."""
        import django
        from django.apps import apps
        if not apps.ready:
            django.setup()

    def _handle_created(self, path: str):
        """Handle new file creation - add to database."""
        self._ensure_django_ready()
        from .models import MediaFile
        from django.core.files import File
        from django.utils import timezone

        try:
            file_path = Path(path)
            filename = file_path.name

            # Check if already exists
            if MediaFile.objects.filter(filename=filename).exists():
                logger.debug(f"File already in database: {filename}")
                return

            # Get file info
            stat = file_path.stat()
            mime_type, _ = mimetypes.guess_type(path)
            media_type = self._get_media_type(path)

            # Create database entry
            media_file = MediaFile(
                title=file_path.stem.replace('_', ' ').replace('-', ' ').title(),
                filename=filename,
                mime_type=mime_type or 'application/octet-stream',
                media_type=media_type,
                file_size=stat.st_size,
                is_local=True,
                is_synced=False,
            )

            # Attach the file
            with open(path, 'rb') as f:
                media_file.file.save(filename, File(f), save=True)

            logger.info(f"Added to database: {filename}")

            # Optionally upload to WordPress
            if self.auto_upload:
                from .tasks import upload_media_to_wordpress
                upload_media_to_wordpress.delay(media_file.id)
                logger.info(f"Queued for WordPress upload: {filename}")

        except Exception as e:
            logger.error(f"Error handling created file {path}: {e}")

    def _handle_modified(self, path: str):
        """Handle file modification - update database entry."""
        self._ensure_django_ready()
        from .models import MediaFile
        from django.utils import timezone

        try:
            file_path = Path(path)
            filename = file_path.name

            # Find existing entry
            media_file = MediaFile.objects.filter(filename=filename).first()
            if not media_file:
                # Treat as new file
                self._handle_created(path)
                return

            # Update file info
            stat = file_path.stat()
            media_file.file_size = stat.st_size
            media_file.updated_at = timezone.now()
            media_file.is_synced = False  # Mark as needing sync
            media_file.save()

            logger.info(f"Updated in database: {filename}")

        except Exception as e:
            logger.error(f"Error handling modified file {path}: {e}")

    def _handle_deleted(self, path: str):
        """Handle file deletion - optionally remove from database."""
        self._ensure_django_ready()
        from .models import MediaFile

        try:
            file_path = Path(path)
            filename = file_path.name

            # Find and mark as deleted (soft delete approach)
            media_file = MediaFile.objects.filter(filename=filename).first()
            if media_file:
                media_file.is_local = False
                media_file.save()
                logger.info(f"Marked as not local: {filename}")

        except Exception as e:
            logger.error(f"Error handling deleted file {path}: {e}")

    def _handle_moved(self, src_path: str, dest_path: str):
        """Handle file move/rename - update database entry."""
        self._ensure_django_ready()
        from .models import MediaFile

        try:
            src_file = Path(src_path)
            dest_file = Path(dest_path)

            # Find existing entry
            media_file = MediaFile.objects.filter(filename=src_file.name).first()
            if media_file:
                media_file.filename = dest_file.name
                media_file.title = dest_file.stem.replace('_', ' ').replace('-', ' ').title()
                media_file.save()
                logger.info(f"Renamed in database: {src_file.name} -> {dest_file.name}")
            else:
                # Treat destination as new file
                self._handle_created(dest_path)

        except Exception as e:
            logger.error(f"Error handling moved file {src_path} -> {dest_path}: {e}")

    def start(self):
        """Start watching the media directory."""
        if self._observer is not None:
            logger.warning("Watcher already running")
            return

        self._stop_event.clear()

        # Create event handler with callbacks
        handler = MediaFileHandler(
            on_created=self._handle_created,
            on_modified=self._handle_modified,
            on_deleted=self._handle_deleted,
            on_moved=self._handle_moved,
            debounce_seconds=self.debounce_seconds,
        )

        # Override the handler methods properly
        handler.on_created = lambda event: self._on_event(event, 'created')
        handler.on_modified = lambda event: self._on_event(event, 'modified')
        handler.on_deleted = lambda event: self._on_event(event, 'deleted')
        handler.on_moved = lambda event: self._on_event(event, 'moved')

        # Store handler reference for event processing
        self._handler = handler

        # Create and start observer
        self._observer = Observer()
        self._observer.schedule(
            handler,
            str(self.watch_path),
            recursive=self.recursive
        )
        self._observer.start()

        logger.info(f"Started watching: {self.watch_path} (recursive={self.recursive})")

    def _on_event(self, event, event_type: str):
        """Process file system events."""
        # Skip directories
        if event.is_directory:
            return

        # Check file extension
        ext = Path(event.src_path).suffix.lower()
        if ext not in MediaFileHandler.ALLOWED_EXTENSIONS:
            return

        if event_type == 'created':
            self._handle_created(event.src_path)
        elif event_type == 'modified':
            self._handle_modified(event.src_path)
        elif event_type == 'deleted':
            self._handle_deleted(event.src_path)
        elif event_type == 'moved':
            self._handle_moved(event.src_path, event.dest_path)

    def stop(self):
        """Stop watching the media directory."""
        if self._observer is None:
            return

        self._stop_event.set()
        self._observer.stop()
        self._observer.join(timeout=5)
        self._observer = None

        logger.info(f"Stopped watching: {self.watch_path}")

    def is_running(self) -> bool:
        """Check if watcher is currently running."""
        return self._observer is not None and self._observer.is_alive()

    def scan_existing(self):
        """Scan existing files in directory and add to database."""
        from .models import MediaFile
        from django.core.files import File

        logger.info(f"Scanning existing files in: {self.watch_path}")
        count = 0

        for ext in MediaFileHandler.ALLOWED_EXTENSIONS:
            pattern = f"**/*{ext}" if self.recursive else f"*{ext}"
            for file_path in self.watch_path.glob(pattern):
                if file_path.is_file():
                    if not MediaFile.objects.filter(filename=file_path.name).exists():
                        self._handle_created(str(file_path))
                        count += 1

        logger.info(f"Added {count} existing files to database")
        return count

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False

    def run_forever(self):
        """Run watcher until interrupted."""
        self.start()
        try:
            while not self._stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt, stopping watcher...")
        finally:
            self.stop()


# Convenience function for running from command line
def watch_media_directory(
    path: str = None,
    recursive: bool = True,
    auto_upload: bool = False,
    scan_existing: bool = True,
):
    """
    Start watching media directory.

    Args:
        path: Directory to watch (defaults to MEDIA_ROOT)
        recursive: Watch subdirectories
        auto_upload: Auto-upload new files to WordPress
        scan_existing: Scan and add existing files on startup
    """
    from django.conf import settings

    if path is None:
        path = settings.MEDIA_ROOT

    watcher = MediaFileWatcher(
        watch_path=path,
        recursive=recursive,
        auto_upload=auto_upload,
    )

    if scan_existing:
        watcher.scan_existing()

    watcher.run_forever()
