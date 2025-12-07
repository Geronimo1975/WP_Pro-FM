"""
WordPress Media Downloader
Downloads all media files from WordPress site
"""

import requests
from requests.auth import HTTPBasicAuth
import os
from pathlib import Path
from urllib.parse import urlparse, unquote
import time
import json


def load_env_file(env_path: Path):
    """Load environment variables from .env file"""
    if not env_path.exists():
        return
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value


# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_env_file(env_path)


class MediaDownloader:
    """Download all media from WordPress"""

    def __init__(self):
        self.site_url = os.getenv('WP_SITE_URL', '').rstrip('/')
        self.username = os.getenv('WP_USERNAME')
        self.app_password = os.getenv('WP_APP_PASSWORD')

        if not all([self.site_url, self.username, self.app_password]):
            raise ValueError("Missing WordPress credentials in .env file")

        self.auth = HTTPBasicAuth(self.username, self.app_password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Output directories
        self.base_dir = Path(__file__).parent
        self.downloads_dir = self.base_dir / 'downloads'
        self.downloads_dir.mkdir(exist_ok=True)

    def _api_request(self, endpoint: str, params: dict = None) -> dict:
        """Make API request using ?rest_route="""
        url = f"{self.site_url}/?rest_route={endpoint}"
        if params:
            param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
            url = f"{url}&{param_str}"

        response = self.session.get(url)
        response.raise_for_status()
        return response.json(), response.headers

    def get_all_media(self, per_page: int = 100) -> list:
        """Get all media items from WordPress"""
        all_media = []
        page = 1

        print("Fetching media list from WordPress...")

        while True:
            try:
                media, headers = self._api_request('/wp/v2/media', {
                    'per_page': per_page,
                    'page': page
                })

                if not media:
                    break

                all_media.extend(media)
                total_pages = int(headers.get('X-WP-TotalPages', 1))
                total_items = int(headers.get('X-WP-Total', len(all_media)))

                print(f"  Page {page}/{total_pages} - {len(all_media)}/{total_items} items")

                if page >= total_pages:
                    break

                page += 1
                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"Error on page {page}: {e}")
                break

        return all_media

    def download_file(self, url: str, filename: str = None) -> Path:
        """Download a single file"""
        if not filename:
            parsed = urlparse(url)
            filename = unquote(Path(parsed.path).name)

        filepath = self.downloads_dir / filename

        # Skip if already downloaded
        if filepath.exists():
            return filepath

        try:
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return filepath

        except Exception as e:
            print(f"  Error downloading {filename}: {e}")
            return None

    def download_all_media(self, include_sizes: bool = False) -> dict:
        """Download all media files"""
        media_list = self.get_all_media()

        if not media_list:
            print("No media found!")
            return {'downloaded': 0, 'skipped': 0, 'errors': 0}

        print(f"\nFound {len(media_list)} media items")
        print(f"Downloading to: {self.downloads_dir}\n")

        stats = {'downloaded': 0, 'skipped': 0, 'errors': 0, 'files': []}

        for i, item in enumerate(media_list, 1):
            media_id = item.get('id')
            title = item.get('title', {}).get('rendered', 'Untitled')
            source_url = item.get('source_url', '')
            mime_type = item.get('mime_type', '')

            if not source_url:
                print(f"[{i}/{len(media_list)}] Skipping {title} - no URL")
                stats['skipped'] += 1
                continue

            # Get filename from URL
            parsed = urlparse(source_url)
            filename = unquote(Path(parsed.path).name)

            # Check if already exists
            filepath = self.downloads_dir / filename
            if filepath.exists():
                print(f"[{i}/{len(media_list)}] Already exists: {filename}")
                stats['skipped'] += 1
                stats['files'].append({
                    'id': media_id,
                    'filename': filename,
                    'status': 'skipped'
                })
                continue

            print(f"[{i}/{len(media_list)}] Downloading: {filename}")
            result = self.download_file(source_url, filename)

            if result:
                stats['downloaded'] += 1
                stats['files'].append({
                    'id': media_id,
                    'filename': filename,
                    'title': title,
                    'mime_type': mime_type,
                    'url': source_url,
                    'status': 'downloaded'
                })
            else:
                stats['errors'] += 1
                stats['files'].append({
                    'id': media_id,
                    'filename': filename,
                    'status': 'error'
                })

            # Rate limiting
            time.sleep(0.2)

        return stats

    def save_media_index(self, stats: dict):
        """Save media index to JSON file"""
        index_file = self.base_dir / 'media_index.json'

        # Get full media list for index
        media_list = self.get_all_media()

        index = {
            'site_url': self.site_url,
            'total_items': len(media_list),
            'download_stats': {
                'downloaded': stats['downloaded'],
                'skipped': stats['skipped'],
                'errors': stats['errors']
            },
            'media': []
        }

        for item in media_list:
            index['media'].append({
                'id': item.get('id'),
                'title': item.get('title', {}).get('rendered', ''),
                'filename': Path(urlparse(item.get('source_url', '')).path).name,
                'url': item.get('source_url', ''),
                'mime_type': item.get('mime_type', ''),
                'alt_text': item.get('alt_text', ''),
                'caption': item.get('caption', {}).get('rendered', ''),
                'date': item.get('date', ''),
                'sizes': list(item.get('media_details', {}).get('sizes', {}).keys())
            })

        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        print(f"\nMedia index saved to: {index_file}")


def main():
    print("=" * 60)
    print("WordPress Media Downloader")
    print("=" * 60 + "\n")

    downloader = MediaDownloader()

    # Download all media
    stats = downloader.download_all_media()

    # Save index
    downloader.save_media_index(stats)

    # Summary
    print("\n" + "=" * 60)
    print("Download Complete!")
    print("=" * 60)
    print(f"  Downloaded: {stats['downloaded']}")
    print(f"  Skipped:    {stats['skipped']}")
    print(f"  Errors:     {stats['errors']}")
    print(f"\nFiles saved to: {downloader.downloads_dir}")


if __name__ == '__main__':
    main()
