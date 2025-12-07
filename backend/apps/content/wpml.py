"""
WPML Integration Service for WordPress Multilingual Content Management.

Provides comprehensive WPML support including:
- Language management and switching
- Translation linking via trid (translation group ID)
- Content synchronization across languages
- REST API integration with WPML endpoints
"""

from typing import Optional, Dict, Any, List, Tuple
from django.conf import settings
import requests
from requests.auth import HTTPBasicAuth
import logging

logger = logging.getLogger(__name__)


class WPMLLanguage:
    """WPML supported languages configuration"""

    # ISO 639-1 language codes supported by WPML
    GERMAN = 'de'
    ENGLISH = 'en'
    FRENCH = 'fr'
    SPANISH = 'es'
    ITALIAN = 'it'
    DUTCH = 'nl'
    POLISH = 'pl'
    PORTUGUESE = 'pt-pt'
    RUSSIAN = 'ru'
    TURKISH = 'tr'
    ARABIC = 'ar'
    CHINESE_SIMPLIFIED = 'zh-hans'
    CHINESE_TRADITIONAL = 'zh-hant'
    JAPANESE = 'ja'
    KOREAN = 'ko'

    # Default language for this project
    DEFAULT = GERMAN

    # Available languages for this site
    AVAILABLE = [GERMAN, ENGLISH]

    @classmethod
    def get_choices(cls) -> List[Tuple[str, str]]:
        """Return language choices for Django model fields"""
        names = {
            cls.GERMAN: 'Deutsch',
            cls.ENGLISH: 'English',
            cls.FRENCH: 'Français',
            cls.SPANISH: 'Español',
            cls.ITALIAN: 'Italiano',
            cls.DUTCH: 'Nederlands',
            cls.POLISH: 'Polski',
            cls.PORTUGUESE: 'Português',
            cls.RUSSIAN: 'Русский',
            cls.TURKISH: 'Türkçe',
            cls.ARABIC: 'العربية',
            cls.CHINESE_SIMPLIFIED: '简体中文',
            cls.CHINESE_TRADITIONAL: '繁體中文',
            cls.JAPANESE: '日本語',
            cls.KOREAN: '한국어',
        }
        return [(code, names.get(code, code)) for code in cls.AVAILABLE]


class WPMLService:
    """
    WPML REST API Service for managing multilingual content.

    Handles translation linking, language switching, and content sync
    with WordPress WPML plugin via REST API.
    """

    def __init__(self, language: str = None):
        self.site_url = getattr(settings, 'WP_SITE_URL', '').rstrip('/')
        self.username = getattr(settings, 'WP_USERNAME', '')
        self.app_password = getattr(settings, 'WP_APP_PASSWORD', '')
        self.language = language or WPMLLanguage.DEFAULT

        if not all([self.site_url, self.username, self.app_password]):
            raise ValueError("Missing WordPress credentials in settings")

        self.auth = HTTPBasicAuth(self.username, self.app_password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            'User-Agent': 'WP_Pro-FM/1.0',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _build_url(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """
        Build REST API URL using ?rest_route= format for Strato compatibility.
        Automatically adds WPML language parameter.
        """
        base = f"{self.site_url}/?rest_route={endpoint}"

        if params is None:
            params = {}
        params['wpml_language'] = self.language

        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base}&{param_str}"

    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                 data: Optional[Dict] = None, timeout: int = 30) -> Dict[str, Any]:
        """Make authenticated API request"""
        url = self._build_url(endpoint, params)

        try:
            response = self.session.request(method, url, json=data, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"WPML API Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text[:500]}")
            raise

    def set_language(self, language: str) -> None:
        """Set the active language for subsequent API requests"""
        if language not in WPMLLanguage.AVAILABLE:
            raise ValueError(f"Language '{language}' not in available languages: {WPMLLanguage.AVAILABLE}")
        self.language = language

    # ==================== Language Management ====================

    def get_languages(self) -> List[Dict[str, Any]]:
        """
        Get all active languages configured in WPML.

        Returns:
            List of language dictionaries with code, name, native_name, etc.
        """
        try:
            # Try WPML REST API endpoint first
            return self._request('GET', '/wpml/v1/languages')
        except Exception:
            # Fallback to configured languages
            logger.warning("WPML languages endpoint not available, using configured languages")
            return [
                {'code': code, 'name': name, 'active': True}
                for code, name in WPMLLanguage.get_choices()
            ]

    def get_default_language(self) -> str:
        """Get the default language code from WPML settings"""
        try:
            languages = self.get_languages()
            for lang in languages:
                if lang.get('default', False):
                    return lang['code']
        except Exception:
            pass
        return WPMLLanguage.DEFAULT

    # ==================== Post Translation Management ====================

    def get_post_translations(self, post_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Get all translations of a post.

        Args:
            post_id: WordPress post ID

        Returns:
            Dictionary mapping language codes to post data
        """
        translations = {}

        for lang_code in WPMLLanguage.AVAILABLE:
            try:
                self.set_language(lang_code)
                # Get post with translation info
                post = self._request('GET', f'/wp/v2/posts/{post_id}')
                if post:
                    translations[lang_code] = {
                        'id': post.get('id'),
                        'title': post.get('title', {}).get('rendered', ''),
                        'link': post.get('link', ''),
                        'status': post.get('status', ''),
                        'wpml': post.get('wpml_current_locale', lang_code),
                    }
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    # No translation exists for this language
                    continue
                raise

        return translations

    def get_post_trid(self, post_id: int) -> Optional[int]:
        """
        Get the translation group ID (trid) for a post.

        The trid links all translations of the same content together.

        Args:
            post_id: WordPress post ID

        Returns:
            Translation group ID or None if not found
        """
        try:
            # WPML exposes trid in post meta or via custom endpoint
            post = self._request('GET', f'/wp/v2/posts/{post_id}')

            # Check for WPML meta fields
            if 'wpml_trid' in post:
                return post['wpml_trid']

            # Check in meta object
            meta = post.get('meta', {})
            if '_wpml_trid' in meta:
                return meta['_wpml_trid']

            return None
        except Exception as e:
            logger.error(f"Failed to get trid for post {post_id}: {e}")
            return None

    def create_post_with_language(self, title: str, content: str, language: str,
                                   status: str = 'draft', categories: List[int] = None,
                                   tags: List[int] = None, meta: Dict = None,
                                   translation_of: int = None) -> Dict[str, Any]:
        """
        Create a new post in a specific language, optionally linking as translation.

        Args:
            title: Post title
            content: Post content (HTML)
            language: Language code (e.g., 'de', 'en')
            status: Post status (draft, publish, etc.)
            categories: List of category IDs
            tags: List of tag IDs
            meta: Additional meta fields (including Rank Math SEO)
            translation_of: If set, link this post as translation of the given post ID

        Returns:
            Created post data from WordPress
        """
        self.set_language(language)

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

        # Create the post
        post = self._request('POST', '/wp/v2/posts', data=data)

        # Link as translation if source post specified
        if translation_of and post.get('id'):
            self.link_translation(
                source_post_id=translation_of,
                translated_post_id=post['id'],
                source_language=WPMLLanguage.DEFAULT,
                target_language=language
            )

        return post

    def link_translation(self, source_post_id: int, translated_post_id: int,
                         source_language: str, target_language: str) -> bool:
        """
        Link two posts as translations of each other via WPML.

        This creates or updates the trid relationship in WPML.

        Args:
            source_post_id: Original post ID
            translated_post_id: Translated post ID
            source_language: Language code of source post
            target_language: Language code of translated post

        Returns:
            True if linking succeeded
        """
        try:
            # Get the trid of the source post
            source_trid = self.get_post_trid(source_post_id)

            if not source_trid:
                logger.warning(f"No trid found for source post {source_post_id}")
                return False

            # Use WPML REST API to set translation details
            # This endpoint may vary based on WPML version
            data = {
                'element_id': translated_post_id,
                'element_type': 'post_post',
                'trid': source_trid,
                'language_code': target_language,
                'source_language_code': source_language
            }

            try:
                self._request('POST', '/wpml/v1/translation/set', data=data)
                logger.info(f"Linked post {translated_post_id} ({target_language}) "
                           f"to post {source_post_id} ({source_language})")
                return True
            except Exception as e:
                # Fallback: Update post meta directly
                logger.warning(f"WPML set translation endpoint failed: {e}")
                self._request('POST', f'/wp/v2/posts/{translated_post_id}', data={
                    'meta': {
                        '_wpml_trid': source_trid,
                        '_wpml_language': target_language,
                        '_wpml_source_language': source_language
                    }
                })
                return True

        except Exception as e:
            logger.error(f"Failed to link translations: {e}")
            return False

    def duplicate_post_for_translation(self, post_id: int, target_language: str,
                                        translate_title: bool = False) -> Optional[Dict]:
        """
        Duplicate a post to create a translation placeholder.

        Args:
            post_id: Source post ID to duplicate
            target_language: Target language for the new post
            translate_title: If True, attempt to auto-translate title

        Returns:
            New post data or None on failure
        """
        try:
            # Get source post
            source_post = self._request('GET', f'/wp/v2/posts/{post_id}')

            title = source_post.get('title', {}).get('rendered', '')
            content = source_post.get('content', {}).get('rendered', '')

            if translate_title:
                title = f"[{target_language.upper()}] {title}"

            # Create translated post
            return self.create_post_with_language(
                title=title,
                content=content,
                language=target_language,
                status='draft',
                categories=source_post.get('categories', []),
                tags=source_post.get('tags', []),
                translation_of=post_id
            )

        except Exception as e:
            logger.error(f"Failed to duplicate post {post_id} for {target_language}: {e}")
            return None

    # ==================== Category & Tag Translation ====================

    def get_category_translations(self, category_id: int) -> Dict[str, Dict[str, Any]]:
        """Get all translations of a category"""
        translations = {}

        for lang_code in WPMLLanguage.AVAILABLE:
            try:
                self.set_language(lang_code)
                cat = self._request('GET', f'/wp/v2/categories/{category_id}')
                if cat:
                    translations[lang_code] = {
                        'id': cat.get('id'),
                        'name': cat.get('name', ''),
                        'slug': cat.get('slug', ''),
                    }
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    continue
                raise

        return translations

    def create_category_translation(self, source_category_id: int, name: str,
                                     target_language: str, slug: str = None,
                                     description: str = '') -> Optional[Dict]:
        """Create a translated version of a category"""
        self.set_language(target_language)

        data = {
            'name': name,
            'description': description,
        }
        if slug:
            data['slug'] = slug

        try:
            return self._request('POST', '/wp/v2/categories', data=data)
        except Exception as e:
            logger.error(f"Failed to create category translation: {e}")
            return None

    # ==================== Sync Operations ====================

    def sync_posts_by_language(self, language: str, per_page: int = 100) -> List[Dict]:
        """
        Sync all posts for a specific language.

        Args:
            language: Language code to sync
            per_page: Number of posts per page

        Returns:
            List of all posts in the specified language
        """
        self.set_language(language)
        all_posts = []
        page = 1

        while True:
            try:
                posts = self._request('GET', '/wp/v2/posts', {
                    'per_page': per_page,
                    'page': page,
                    'status': 'any'
                })

                if not posts:
                    break

                # Add language info to each post
                for post in posts:
                    post['wpml_language'] = language

                all_posts.extend(posts)
                page += 1

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400:  # No more pages
                    break
                raise

        logger.info(f"Synced {len(all_posts)} posts for language '{language}'")
        return all_posts

    def sync_all_languages(self, per_page: int = 100) -> Dict[str, List[Dict]]:
        """
        Sync posts from all available languages.

        Returns:
            Dictionary mapping language codes to post lists
        """
        result = {}

        for lang_code in WPMLLanguage.AVAILABLE:
            result[lang_code] = self.sync_posts_by_language(lang_code, per_page)

        return result

    def get_translation_status(self, post_id: int) -> Dict[str, str]:
        """
        Get translation status for a post across all languages.

        Returns:
            Dictionary mapping language codes to status:
            - 'original': This is the original content
            - 'translated': Translation exists
            - 'missing': No translation
        """
        translations = self.get_post_translations(post_id)
        status = {}

        # Find original language
        original_lang = None
        for lang, data in translations.items():
            if data.get('id') == post_id:
                original_lang = lang
                break

        for lang_code in WPMLLanguage.AVAILABLE:
            if lang_code == original_lang:
                status[lang_code] = 'original'
            elif lang_code in translations:
                status[lang_code] = 'translated'
            else:
                status[lang_code] = 'missing'

        return status
