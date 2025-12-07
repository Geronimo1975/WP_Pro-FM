"""
Celery tasks for content management.
"""

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from openai import OpenAI
import requests
from requests.auth import HTTPBasicAuth
import logging

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
def sync_wordpress_posts(self):
    """Sync posts from WordPress"""
    from .models import Post, Category, Tag

    try:
        site_url = settings.WP_SITE_URL.rstrip('/')
        auth = HTTPBasicAuth(settings.WP_USERNAME, settings.WP_APP_PASSWORD)
        headers = {'User-Agent': 'Mozilla/5.0'}

        all_posts = []
        page = 1
        per_page = 100

        while True:
            url = f"{site_url}/?rest_route=/wp/v2/posts&per_page={per_page}&page={page}&status=any"
            response = requests.get(url, auth=auth, headers=headers, timeout=30)

            if response.status_code != 200:
                break

            posts = response.json()
            if not posts:
                break

            all_posts.extend(posts)
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))

            if page >= total_pages:
                break
            page += 1

        synced = 0
        for item in all_posts:
            Post.objects.update_or_create(
                wp_id=item.get('id'),
                defaults={
                    'title': item.get('title', {}).get('rendered', ''),
                    'content': item.get('content', {}).get('rendered', ''),
                    'excerpt': item.get('excerpt', {}).get('rendered', ''),
                    'slug': item.get('slug', ''),
                    'wp_link': item.get('link', ''),
                    'status': item.get('status', 'draft'),
                    'wp_created_at': item.get('date'),
                    'wp_modified_at': item.get('modified'),
                    'synced_at': timezone.now(),
                }
            )
            synced += 1

        return {'total': len(all_posts), 'synced': synced}

    except Exception as e:
        logger.error(f"WordPress sync failed: {e}")
        raise
