# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WP_Pro-FM is a Django-based backend system that manages and enhances a WordPress-powered Facility Management website (profm24.de). It provides AI-powered content generation, SEO optimization, media management, and email marketing capabilities with WPML multi-language support.

## Common Commands

### Docker Development
```bash
make build          # Build Docker images
make up             # Start all containers (db, redis, backend, celery, celery-beat)
make down           # Stop containers
make migrate        # Run database migrations
make shell          # Open Django shell in backend container
make test           # Run tests
make prod-up        # Production deployment with Nginx
```

### Django Management (inside container)
```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py collectstatic
```

### Running Single Tests
```bash
docker compose exec backend pytest apps/content/tests/test_views.py -v
docker compose exec backend pytest apps/content/tests/test_views.py::TestPostViewSet::test_list -v
```

## Architecture

### Django Apps (`backend/apps/`)

- **content/**: WordPress post management and AI content generation via GPT-4o. Models: `Post`, `Category`, `Tag`, `ContentTemplate`, `ContentGenerationJob`
- **media/**: Media file management with file system watcher. Models: `MediaFile`, `MediaCollection`, `MediaSyncLog`
- **seo/**: Keyword tracking, site audits, backlinks, IndexNow. Models: `Keyword`, `KeywordRankingHistory`, `SiteAudit`, `Backlink`, `IndexNowSubmission`
- **email_marketing/**: Email campaigns and automation workflows. Models: `Subscriber`, `Campaign`, `EmailTemplate`, `AutomationWorkflow`, `AutomationStep`

### Key Modules

- **`backend/config/`**: Django settings, URL routing, Celery configuration, WSGI entry
- **`wpml/`**: WordPress REST API client with WPML integration. Uses `?rest_route=` format for Strato hosting compatibility

### API Structure

All REST endpoints prefixed with `/api/`:
- `/api/content/` - Posts, categories, tags, templates, generation jobs
- `/api/media/` - Files, collections, sync logs
- `/api/seo/` - Keywords, audits, backlinks, IndexNow
- `/api/email/` - Subscribers, campaigns, templates, automations

Admin interface at `/admin/`

### Async Tasks (Celery)

Tasks defined in each app's `tasks.py`:
- Content generation with OpenAI GPT-4o
- WordPress publishing via REST API
- Media synchronization from WordPress
- Keyword ranking tracking
- Email campaign sending and automation execution

### Docker Services

- `db`: PostgreSQL 16 (port 5433)
- `redis`: Redis 7 (port 6379, task broker + cache)
- `backend`: Django app (port 8001 → 8000)
- `celery`: Async task worker
- `celery-beat`: Scheduled task coordinator
- `nginx`: Production web server (port 80)

## WordPress Integration

The `wpml/` module handles WordPress communication:
- `wp_client.py`: REST API client with WPML language parameter support
- `content_generator.py`: German Facility Management content generation
- `publisher.py`: Publishes content to WordPress

Authentication uses HTTP Basic Auth with WordPress application passwords.

## Configuration

Key environment variables (see `.env.example`):
- Django: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- Database: `POSTGRES_*`
- WordPress: `WP_SITE_URL`, `WP_USERNAME`, `WP_APP_PASSWORD`
- OpenAI: `OPENAI_API_KEY`
- Email: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`

Timezone: `Europe/Berlin`, Primary language: German (`de-de`)
