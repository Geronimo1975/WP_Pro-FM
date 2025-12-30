"""
WPML Content Generator Package
Generates German content for WordPress with WPML support
"""

try:
    from .wp_client import WPClient
    from .content_generator import GermanContentGenerator
    from .publisher import WPPublisher
    from .page_translator import PageTranslator
    __all__ = ['WPClient', 'GermanContentGenerator', 'WPPublisher', 'PageTranslator']
except ImportError:
    # Allow individual module imports
    __all__ = []
