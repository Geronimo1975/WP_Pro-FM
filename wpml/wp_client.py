"""
WordPress REST API Client with WPML Support
Uses ?rest_route= for Strato hosting compatibility
"""

import requests
from requests.auth import HTTPBasicAuth
import os
from typing import Optional, Dict, Any, List
from pathlib import Path


def load_env_file(env_path: Path):
    """Load environment variables from .env file"""
    if not env_path.exists():
        return
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Don't strip value - preserve spaces (important for app passwords)
                os.environ[key.strip()] = value


# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_env_file(env_path)


class WPClient:
    """WordPress REST API Client with WPML language support"""

    def __init__(self, language: str = 'de'):
        self.site_url = os.getenv('WP_SITE_URL', '').rstrip('/')
        self.username = os.getenv('WP_USERNAME')
        self.app_password = os.getenv('WP_APP_PASSWORD')
        self.language = language

        if not all([self.site_url, self.username, self.app_password]):
            raise ValueError("Missing WordPress credentials in .env file")

        self.auth = HTTPBasicAuth(self.username, self.app_password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json'
        })

    def _build_url(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Build REST API URL using ?rest_route= format for Strato compatibility"""
        # Use ?rest_route= instead of /wp-json/ for hosting compatibility
        base = f"{self.site_url}/?rest_route={endpoint}"

        # Add WPML language parameter
        if params is None:
            params = {}
        params['wpml_language'] = self.language

        if params:
            param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
            return f"{base}&{param_str}"
        return base

    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                 data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request"""
        url = self._build_url(endpoint, params)

        try:
            response = self.session.request(method, url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text[:500]}")
            raise

    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            user = self._request('GET', '/wp/v2/users/me')
            print(f"Connected as: {user.get('name')} (ID: {user.get('id')})")
            print(f"Admin: {user.get('is_super_admin', False)}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    # Posts
    def get_posts(self, per_page: int = 10, page: int = 1, status: str = 'publish') -> List[Dict]:
        """Get posts"""
        return self._request('GET', '/wp/v2/posts', {
            'per_page': per_page,
            'page': page,
            'status': status
        })

    def get_post(self, post_id: int) -> Dict:
        """Get single post"""
        return self._request('GET', f'/wp/v2/posts/{post_id}')

    def create_post(self, title: str, content: str, status: str = 'draft',
                    categories: Optional[List[int]] = None,
                    tags: Optional[List[int]] = None,
                    meta: Optional[Dict] = None) -> Dict:
        """Create a new post"""
        data = {
            'title': title,
            'content': content,
            'status': status,
        }
        if categories:
            data['categories'] = categories
        if tags:
            data['tags'] = tags
        if meta:
            data['meta'] = meta

        return self._request('POST', '/wp/v2/posts', data=data)

    def update_post(self, post_id: int, **kwargs) -> Dict:
        """Update existing post"""
        return self._request('POST', f'/wp/v2/posts/{post_id}', data=kwargs)

    def delete_post(self, post_id: int, force: bool = False) -> Dict:
        """Delete post"""
        return self._request('DELETE', f'/wp/v2/posts/{post_id}', {'force': force})

    # Pages
    def get_pages(self, per_page: int = 10, page: int = 1) -> List[Dict]:
        """Get pages"""
        return self._request('GET', '/wp/v2/pages', {
            'per_page': per_page,
            'page': page
        })

    def create_page(self, title: str, content: str, status: str = 'draft',
                    parent: int = 0) -> Dict:
        """Create a new page"""
        return self._request('POST', '/wp/v2/pages', data={
            'title': title,
            'content': content,
            'status': status,
            'parent': parent
        })

    # Categories
    def get_categories(self, per_page: int = 100) -> List[Dict]:
        """Get all categories"""
        return self._request('GET', '/wp/v2/categories', {'per_page': per_page})

    def create_category(self, name: str, slug: Optional[str] = None,
                        description: str = '', parent: int = 0) -> Dict:
        """Create category"""
        data = {
            'name': name,
            'description': description,
            'parent': parent
        }
        if slug:
            data['slug'] = slug
        return self._request('POST', '/wp/v2/categories', data=data)

    # Tags
    def get_tags(self, per_page: int = 100) -> List[Dict]:
        """Get all tags"""
        return self._request('GET', '/wp/v2/tags', {'per_page': per_page})

    def create_tag(self, name: str, slug: Optional[str] = None) -> Dict:
        """Create tag"""
        data = {'name': name}
        if slug:
            data['slug'] = slug
        return self._request('POST', '/wp/v2/tags', data=data)

    # Media
    def upload_media(self, file_path: str, title: Optional[str] = None) -> Dict:
        """Upload media file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine content type
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf'
        }
        content_type = content_types.get(file_path.suffix.lower(), 'application/octet-stream')

        url = self._build_url('/wp/v2/media')
        headers = {
            'Content-Disposition': f'attachment; filename="{file_path.name}"',
            'Content-Type': content_type
        }

        with open(file_path, 'rb') as f:
            response = self.session.post(url, data=f, headers=headers)
            response.raise_for_status()
            media = response.json()

        # Update title if provided
        if title and media.get('id'):
            media = self._request('POST', f"/wp/v2/media/{media['id']}", data={'title': title})

        return media

    # WPML specific
    def get_languages(self) -> List[Dict]:
        """Get available WPML languages"""
        try:
            return self._request('GET', '/wpml/v1/languages')
        except:
            # Fallback if WPML API not available
            return [{'code': 'de', 'name': 'Deutsch'}, {'code': 'en', 'name': 'English'}]

    def set_language(self, language: str):
        """Set active language for API requests"""
        self.language = language


if __name__ == '__main__':
    # Test connection
    client = WPClient(language='de')
    if client.test_connection():
        print("\nWordPress REST API is working!")

        # Test getting posts
        posts = client.get_posts(per_page=3)
        print(f"\nLatest {len(posts)} posts:")
        for post in posts:
            print(f"  - [{post['id']}] {post['title']['rendered']}")
