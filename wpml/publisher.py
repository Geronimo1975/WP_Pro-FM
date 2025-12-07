"""
WordPress Content Publisher
Publishes generated German content to WordPress with WPML
"""

from wp_client import WPClient
from content_generator import GermanContentGenerator
from typing import Optional, List, Dict
import time


class WPPublisher:
    """Publish content to WordPress with Rank Math SEO support"""

    def __init__(self, language: str = 'de'):
        self.client = WPClient(language=language)
        self.generator = GermanContentGenerator()
        self.language = language

    def publish_blog_post(self, topic: str, keyword: str,
                          category_ids: Optional[List[int]] = None,
                          tag_ids: Optional[List[int]] = None,
                          status: str = 'draft',
                          word_count: int = 800) -> Dict:
        """Generate and publish a blog post"""

        print(f"Generating content for: {topic}")
        content = self.generator.generate_blog_post(
            topic=topic,
            target_keyword=keyword,
            word_count=word_count
        )

        print(f"Publishing: {content['title']}")
        post = self.client.create_post(
            title=content['title'],
            content=content['content'],
            status=status,
            categories=category_ids,
            tags=tag_ids,
            meta={
                'rank_math_focus_keyword': content['focus_keyword'],
                'rank_math_description': content['meta_description'],
            }
        )

        print(f"Published! Post ID: {post['id']}")
        print(f"URL: {post.get('link', 'N/A')}")

        return {
            'post_id': post['id'],
            'title': content['title'],
            'url': post.get('link'),
            'status': status,
            'meta': content
        }

    def publish_service_page(self, service: str, city: Optional[str] = None,
                             parent_page_id: int = 0,
                             status: str = 'draft') -> Dict:
        """Generate and publish a service page"""

        print(f"Generating service page: {service}" + (f" in {city}" if city else ""))
        content = self.generator.generate_service_page(service=service, city=city)

        print(f"Publishing page: {content['title']}")
        page = self.client.create_page(
            title=content['title'],
            content=content['content'],
            status=status,
            parent=parent_page_id
        )

        # Update with Rank Math meta if possible
        try:
            self.client.update_post(page['id'], meta={
                'rank_math_focus_keyword': content['focus_keyword'],
                'rank_math_description': content['meta_description'],
            })
        except Exception as e:
            print(f"Warning: Could not update Rank Math meta: {e}")

        print(f"Published! Page ID: {page['id']}")

        return {
            'page_id': page['id'],
            'title': content['title'],
            'url': page.get('link'),
            'status': status,
            'meta': content
        }

    def bulk_publish_posts(self, topics: List[Dict], delay_seconds: int = 5) -> List[Dict]:
        """
        Bulk publish multiple posts

        topics format: [{'topic': '...', 'keyword': '...', 'categories': [...]}]
        """
        results = []

        for i, item in enumerate(topics):
            print(f"\n[{i+1}/{len(topics)}] Processing...")

            try:
                result = self.publish_blog_post(
                    topic=item['topic'],
                    keyword=item['keyword'],
                    category_ids=item.get('categories'),
                    tag_ids=item.get('tags'),
                    status=item.get('status', 'draft')
                )
                results.append({'success': True, **result})
            except Exception as e:
                print(f"Error: {e}")
                results.append({'success': False, 'topic': item['topic'], 'error': str(e)})

            if i < len(topics) - 1:
                print(f"Waiting {delay_seconds}s...")
                time.sleep(delay_seconds)

        return results

    def bulk_publish_service_pages(self, services: List[str],
                                   cities: Optional[List[str]] = None,
                                   parent_page_id: int = 0,
                                   delay_seconds: int = 5) -> List[Dict]:
        """
        Bulk publish service pages, optionally for multiple cities

        If cities provided, creates city-specific pages for each service
        """
        results = []
        tasks = []

        # Build task list
        for service in services:
            if cities:
                for city in cities:
                    tasks.append({'service': service, 'city': city})
            else:
                tasks.append({'service': service, 'city': None})

        for i, task in enumerate(tasks):
            print(f"\n[{i+1}/{len(tasks)}] Processing...")

            try:
                result = self.publish_service_page(
                    service=task['service'],
                    city=task['city'],
                    parent_page_id=parent_page_id,
                    status='draft'
                )
                results.append({'success': True, **result})
            except Exception as e:
                print(f"Error: {e}")
                results.append({'success': False, 'service': task['service'], 'error': str(e)})

            if i < len(tasks) - 1:
                print(f"Waiting {delay_seconds}s...")
                time.sleep(delay_seconds)

        return results


if __name__ == '__main__':
    publisher = WPPublisher(language='de')

    # Test connection
    if not publisher.client.test_connection():
        print("Connection failed!")
        exit(1)

    # Example: Publish a single blog post
    print("\n" + "="*50)
    print("Publishing test blog post...")
    print("="*50)

    result = publisher.publish_blog_post(
        topic="Die Vorteile professioneller Gebäudereinigung für Ihr Unternehmen",
        keyword="professionelle Gebäudereinigung",
        status='draft'  # Use 'publish' to publish immediately
    )

    print(f"\nResult: {result}")
