"""
Celery tasks for content management with WPML support.
"""

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from openai import OpenAI
import requests
from requests.auth import HTTPBasicAuth
import logging

from .wpml import WPMLService, WPMLLanguage

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_content(self, template_id: int, variables: dict, auto_publish: bool = False, language: str = 'de'):
    """Generate content using AI"""
    from .models import Post, ContentTemplate, ContentGenerationJob

    job = ContentGenerationJob.objects.create(
        template_id=template_id,
        variables=variables,
        status=ContentGenerationJob.JobStatus.PROCESSING
    )

    try:
        template = ContentTemplate.objects.get(id=template_id)

        # Build prompts
        user_prompt = template.user_prompt_template.format(**variables)

        # Call OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": template.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )

        content_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        # Parse generated content
        parsed = _parse_generated_content(content_text)

        # Create post
        post = Post.objects.create(
            title=parsed.get('title', variables.get('topic', 'Generated Post')),
            content=parsed.get('content', content_text),
            excerpt=parsed.get('excerpt', ''),
            focus_keyword=parsed.get('focus_keyword', variables.get('keyword', '')),
            meta_title=parsed.get('meta_title', ''),
            meta_description=parsed.get('meta_description', ''),
            language=language,
            status=Post.PostStatus.DRAFT,
            is_ai_generated=True,
            ai_prompt=user_prompt,
            generation_model="gpt-4o"
        )

        # Update job
        job.result_post = post
        job.tokens_used = tokens_used
        job.cost_usd = tokens_used * 0.00003  # Approximate GPT-4 cost
        job.status = ContentGenerationJob.JobStatus.COMPLETED
        job.completed_at = timezone.now()
        job.save()

        # Auto-publish if requested
        if auto_publish:
            publish_to_wordpress.delay(post.id)

        return {'post_id': post.id, 'title': post.title, 'tokens': tokens_used}

    except Exception as e:
        job.status = ContentGenerationJob.JobStatus.FAILED
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save()
        logger.error(f"Content generation failed: {e}")
        raise


def _parse_generated_content(content: str) -> dict:
    """Parse AI-generated content into structured format"""
    result = {
        'title': '',
        'meta_title': '',
        'meta_description': '',
        'content': '',
        'excerpt': '',
        'focus_keyword': ''
    }

    sections = {
        '---TITLE---': 'title',
        '---META_TITLE---': 'meta_title',
        '---META_DESCRIPTION---': 'meta_description',
        '---CONTENT---': 'content',
        '---EXCERPT---': 'excerpt',
        '---FOCUS_KEYWORD---': 'focus_keyword'
    }

    current_section = None
    current_content = []

    for line in content.split('\n'):
        line_stripped = line.strip()
        if line_stripped in sections:
            if current_section:
                result[current_section] = '\n'.join(current_content).strip()
            current_section = sections[line_stripped]
            current_content = []
        elif current_section:
            current_content.append(line)

    if current_section:
        result[current_section] = '\n'.join(current_content).strip()

    # If no sections found, use raw content
    if not result['content']:
        result['content'] = content

    return result


@shared_task(bind=True)
def publish_to_wordpress(self, post_id: int):
    """Publish a post to WordPress"""
    from .models import Post

    try:
        post = Post.objects.get(id=post_id)

        site_url = settings.WP_SITE_URL.rstrip('/')
        auth = HTTPBasicAuth(settings.WP_USERNAME, settings.WP_APP_PASSWORD)
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/json'
        }

        data = {
            'title': post.title,
            'content': post.content,
            'excerpt': post.excerpt,
            'status': 'publish',
            'meta': {
                'rank_math_focus_keyword': post.focus_keyword,
                'rank_math_description': post.meta_description,
            }
        }

        # Add language parameter for WPML
        url = f"{site_url}/?rest_route=/wp/v2/posts&wpml_language={post.language}"

        if post.wp_id:
            # Update existing post
            url = f"{site_url}/?rest_route=/wp/v2/posts/{post.wp_id}&wpml_language={post.language}"
            response = requests.post(url, json=data, auth=auth, headers=headers, timeout=30)
        else:
            # Create new post
            response = requests.post(url, json=data, auth=auth, headers=headers, timeout=30)

        response.raise_for_status()
        wp_post = response.json()

        # Update local post
        post.wp_id = wp_post.get('id')
        post.wp_link = wp_post.get('link', '')
        post.status = Post.PostStatus.PUBLISH
        post.published_at = timezone.now()
        post.synced_at = timezone.now()
        post.save()

        return {'wp_id': post.wp_id, 'link': post.wp_link}

    except Post.DoesNotExist:
        logger.error(f"Post {post_id} not found")
        raise
    except Exception as e:
        logger.error(f"Failed to publish post {post_id}: {e}")
        raise


@shared_task(bind=True)
def sync_wordpress_posts(self, language: str = None, sync_all_languages: bool = False):
    """
    Sync posts from WordPress with WPML language support.

    Args:
        language: Specific language to sync (None syncs default language)
        sync_all_languages: If True, sync posts from all available languages
    """
    from .models import Post, Category, Tag

    try:
        results = {}

        if sync_all_languages:
            languages_to_sync = WPMLLanguage.AVAILABLE
        elif language:
            languages_to_sync = [language]
        else:
            languages_to_sync = [WPMLLanguage.DEFAULT]

        for lang in languages_to_sync:
            try:
                service = WPMLService(language=lang)
                posts = service.sync_posts_by_language(lang)

                synced = 0
                for item in posts:
                    # Extract WPML-specific data
                    wpml_trid = item.get('wpml_trid') or item.get('meta', {}).get('_wpml_trid')

                    post, created = Post.objects.update_or_create(
                        wp_id=item.get('id'),
                        defaults={
                            'title': item.get('title', {}).get('rendered', ''),
                            'content': item.get('content', {}).get('rendered', ''),
                            'excerpt': item.get('excerpt', {}).get('rendered', ''),
                            'slug': item.get('slug', ''),
                            'wp_link': item.get('link', ''),
                            'status': item.get('status', 'draft'),
                            'language': lang,
                            'wpml_trid': wpml_trid,
                            'wp_created_at': item.get('date'),
                            'wp_modified_at': item.get('modified'),
                            'synced_at': timezone.now(),
                        }
                    )
                    synced += 1

                results[lang] = {'total': len(posts), 'synced': synced}
                logger.info(f"Synced {synced} posts for language '{lang}'")

            except Exception as e:
                logger.error(f"Failed to sync language '{lang}': {e}")
                results[lang] = {'error': str(e)}

        # Link translations by wpml_trid
        _link_translations_by_trid()

        return results

    except Exception as e:
        logger.error(f"WordPress sync failed: {e}")
        raise


def _link_translations_by_trid():
    """Link posts that share the same wpml_trid as translations"""
    from .models import Post
    from django.db.models import Count

    # Find all unique trids with multiple posts
    trids = (Post.objects
             .exclude(wpml_trid__isnull=True)
             .values('wpml_trid')
             .annotate(count=Count('id'))
             .filter(count__gt=1))

    for trid_data in trids:
        trid = trid_data['wpml_trid']
        posts = list(Post.objects.filter(wpml_trid=trid).order_by('id'))

        if len(posts) < 2:
            continue

        # First post (oldest) is considered the original
        original = posts[0]

        # Link other posts as translations
        for translation in posts[1:]:
            if not translation.translation_of_id:
                translation.translation_of = original
                translation.source_language = original.language
                translation.save(update_fields=['translation_of', 'source_language'])
                logger.debug(f"Linked post {translation.id} ({translation.language}) "
                           f"to original {original.id} ({original.language})")


@shared_task(bind=True)
def sync_wpml_translations(self, post_id: int):
    """
    Sync translations for a specific post from WordPress.

    Fetches all language versions of the post and updates/creates local records.
    """
    from .models import Post

    try:
        post = Post.objects.get(id=post_id)

        if not post.wp_id:
            logger.warning(f"Post {post_id} has no WordPress ID, cannot sync translations")
            return {'error': 'Post not synced with WordPress'}

        service = WPMLService(language=post.language)
        translations = service.get_post_translations(post.wp_id)

        synced = []
        for lang, data in translations.items():
            if lang == post.language:
                # Update wpml_trid if available
                if not post.wpml_trid:
                    trid = service.get_post_trid(post.wp_id)
                    if trid:
                        post.wpml_trid = trid
                        post.save(update_fields=['wpml_trid'])
                continue

            # Check if translation exists locally
            existing = Post.objects.filter(wp_id=data['id']).first()

            if existing:
                # Link as translation if not already linked
                if not existing.translation_of_id:
                    existing.translation_of = post if post.is_original else post.translation_of
                    existing.source_language = post.language
                    existing.wpml_trid = post.wpml_trid
                    existing.save()
                synced.append({'language': lang, 'id': existing.id, 'action': 'linked'})
            else:
                # Sync this translation from WordPress
                service.set_language(lang)
                wp_post = service._request('GET', f'/wp/v2/posts/{data["id"]}')

                new_post = Post.objects.create(
                    wp_id=wp_post.get('id'),
                    title=wp_post.get('title', {}).get('rendered', ''),
                    content=wp_post.get('content', {}).get('rendered', ''),
                    excerpt=wp_post.get('excerpt', {}).get('rendered', ''),
                    slug=wp_post.get('slug', ''),
                    wp_link=wp_post.get('link', ''),
                    status=wp_post.get('status', 'draft'),
                    language=lang,
                    translation_of=post if post.is_original else post.translation_of,
                    source_language=post.language,
                    wpml_trid=post.wpml_trid,
                    wp_created_at=wp_post.get('date'),
                    wp_modified_at=wp_post.get('modified'),
                    synced_at=timezone.now(),
                )
                synced.append({'language': lang, 'id': new_post.id, 'action': 'created'})

        return {'post_id': post_id, 'translations_synced': synced}

    except Post.DoesNotExist:
        logger.error(f"Post {post_id} not found")
        raise
    except Exception as e:
        logger.error(f"Failed to sync translations for post {post_id}: {e}")
        raise


@shared_task(bind=True)
def create_translation_task(self, post_id: int, target_language: str):
    """
    Create a translation of a post using AI.

    Translates the title, content, excerpt, and SEO fields.
    """
    from .models import Post

    try:
        post = Post.objects.get(id=post_id)

        # Use OpenAI to translate content
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        language_names = dict(WPMLLanguage.get_choices())
        source_lang_name = language_names.get(post.language, post.language)
        target_lang_name = language_names.get(target_language, target_language)

        # Prepare translation prompt
        system_prompt = f"""You are a professional translator specializing in Facility Management content.
Translate the following content from {source_lang_name} to {target_lang_name}.
Maintain the HTML structure, formatting, and SEO optimization.
Keep technical terms accurate and natural for the target language.
Return the translation in the exact same format as the input."""

        content_to_translate = f"""---TITLE---
{post.title}

---CONTENT---
{post.content}

---EXCERPT---
{post.excerpt}

---META_TITLE---
{post.meta_title}

---META_DESCRIPTION---
{post.meta_description}"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content_to_translate}
            ],
            temperature=0.3,
            max_tokens=4000
        )

        translated_text = response.choices[0].message.content
        parsed = _parse_generated_content(translated_text)

        # Create translated post
        translation = Post.objects.create(
            title=parsed.get('title', f"[{target_language.upper()}] {post.title}"),
            content=parsed.get('content', post.content),
            excerpt=parsed.get('excerpt', post.excerpt),
            slug=f"{post.slug}-{target_language}" if post.slug else '',
            post_type=post.post_type,
            status=Post.PostStatus.DRAFT,
            language=target_language,
            translation_of=post if post.is_original else post.translation_of,
            source_language=post.language,
            wpml_trid=post.wpml_trid,
            focus_keyword=post.focus_keyword,
            meta_title=parsed.get('meta_title', ''),
            meta_description=parsed.get('meta_description', ''),
            is_ai_generated=True,
            ai_prompt=f"Translation from {source_lang_name} to {target_lang_name}",
            generation_model="gpt-4o"
        )

        # Copy categories and tags
        for category in post.categories.all():
            translated_cat = category.get_translation(target_language)
            translation.categories.add(translated_cat or category)

        for tag in post.tags.all():
            translated_tag = tag.get_translation(target_language)
            translation.tags.add(translated_tag or tag)

        logger.info(f"Created translation of post {post_id} to {target_language}: {translation.id}")

        return {
            'original_id': post_id,
            'translation_id': translation.id,
            'target_language': target_language,
            'title': translation.title
        }

    except Post.DoesNotExist:
        logger.error(f"Post {post_id} not found")
        raise
    except Exception as e:
        logger.error(f"Failed to create translation for post {post_id}: {e}")
        raise


@shared_task(bind=True)
def publish_to_wordpress_wpml(self, post_id: int, link_translation: bool = True):
    """
    Publish a post to WordPress with WPML translation linking.

    Args:
        post_id: Local post ID to publish
        link_translation: If True, link to existing translations in WPML
    """
    from .models import Post

    try:
        post = Post.objects.get(id=post_id)
        service = WPMLService(language=post.language)

        # Prepare post data
        data = {
            'title': post.title,
            'content': post.content,
            'excerpt': post.excerpt,
            'status': 'publish',
            'meta': {
                'rank_math_focus_keyword': post.focus_keyword,
                'rank_math_description': post.meta_description,
            }
        }

        if post.wp_id:
            # Update existing post
            wp_post = service._request('POST', f'/wp/v2/posts/{post.wp_id}', data=data)
        else:
            # Create new post
            wp_post = service._request('POST', '/wp/v2/posts', data=data)

        # Update local post with WordPress data
        post.wp_id = wp_post.get('id')
        post.wp_link = wp_post.get('link', '')
        post.status = Post.PostStatus.PUBLISH
        post.published_at = timezone.now()
        post.synced_at = timezone.now()

        # Get and store WPML trid
        trid = service.get_post_trid(post.wp_id)
        if trid:
            post.wpml_trid = trid

        post.save()

        # Link as translation if this is a translated post
        if link_translation and post.translation_of_id:
            original = post.translation_of
            if original.wp_id:
                service.link_translation(
                    source_post_id=original.wp_id,
                    translated_post_id=post.wp_id,
                    source_language=original.language,
                    target_language=post.language
                )

        return {'wp_id': post.wp_id, 'link': post.wp_link, 'wpml_trid': post.wpml_trid}

    except Post.DoesNotExist:
        logger.error(f"Post {post_id} not found")
        raise
    except Exception as e:
        logger.error(f"Failed to publish post {post_id}: {e}")
        raise
