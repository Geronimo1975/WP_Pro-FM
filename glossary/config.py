"""
ProFM24 Glossary Configuration Module
Handles environment variables and settings for the glossary system.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try parent directory
    load_dotenv(Path(__file__).parent.parent / '.env')


class Config:
    """Central configuration for the glossary system."""

    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://profm_user:password@localhost:5433/profm_glossar')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5433')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'profm_glossar')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'profm_user')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')

    # WordPress
    WP_SITE_URL = os.getenv('WP_SITE_URL', 'https://profm24.de')
    WP_USERNAME = os.getenv('WP_USERNAME', 'admin')
    WP_APP_PASSWORD = os.getenv('WP_APP_PASSWORD', '')

    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))

    # VPS
    VPS_HOST = os.getenv('VPS_HOST', '217.154.250.85')
    VPS_USER = os.getenv('VPS_USER', 'root')
    VPS_PATH = os.getenv('VPS_PATH', '/var/www/profm24')

    # Generation Settings
    GENERATION_DELAY = float(os.getenv('GENERATION_DELAY', '1.0'))
    GENERATION_RETRIES = int(os.getenv('GENERATION_RETRIES', '3'))
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '50'))

    # Paths
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / 'data'
    OUTPUT_DIR = BASE_DIR / 'output'
    TEMPLATES_DIR = BASE_DIR / 'templates'

    @classmethod
    def get_db_connection_string(cls):
        """Get PostgreSQL connection string."""
        if cls.DATABASE_URL:
            return cls.DATABASE_URL
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"

    @classmethod
    def get_wp_auth(cls):
        """Get WordPress authentication tuple."""
        return (cls.WP_USERNAME, cls.WP_APP_PASSWORD)

    @classmethod
    def get_wp_api_url(cls, endpoint=''):
        """Get WordPress REST API URL (Strato hosting compatible)."""
        base = cls.WP_SITE_URL.rstrip('/')
        # Use rest_route format for Strato hosting compatibility
        if endpoint:
            return f"{base}/?rest_route=/wp/v2/{endpoint.lstrip('/')}"
        return f"{base}/?rest_route=/wp/v2"

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        errors = []

        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")

        if not cls.WP_APP_PASSWORD:
            errors.append("WP_APP_PASSWORD is required")

        if not cls.POSTGRES_PASSWORD and 'DATABASE_URL' not in os.environ:
            errors.append("POSTGRES_PASSWORD or DATABASE_URL is required")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        return True


# Categories definition
CATEGORIES = [
    "Smart Building & IoT",
    "Robotik & Automatisierung",
    "Sensorik & Messtechnik",
    "Gebäudetechnik (TGA)",
    "Energiemanagement",
    "Sicherheitstechnik",
    "Gebäudereinigung",
    "Grünflächenpflege",
    "Catering & Services",
    "CAFM & Digitalisierung",
    "Flächenmanagement",
    "Vertragsmanagement",
    "ESG & Nachhaltigkeit",
    "Predictive Maintenance",
    "Workplace & New Work"
]

# Target terms per letter
LETTER_TARGETS = {
    'A': 35, 'B': 30, 'C': 25, 'D': 30, 'E': 30,
    'F': 35, 'G': 35, 'H': 25, 'I': 25, 'J': 5,
    'K': 30, 'L': 25, 'M': 30, 'N': 20, 'O': 15,
    'P': 30, 'Q': 3, 'R': 25, 'S': 50, 'T': 25,
    'U': 15, 'V': 20, 'W': 25, 'X': 2, 'Y': 2, 'Z': 15
}

# Total target
TOTAL_TERMS_TARGET = sum(LETTER_TARGETS.values())
