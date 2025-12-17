"""
Front Page app configuration.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FrontPageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.front_page'
    verbose_name = _('Front Page Management')

    def ready(self):
        # Import signals when app is ready
        pass
