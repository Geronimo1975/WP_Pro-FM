from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from .models import Post, Category, Tag, ContentTemplate, ContentGenerationJob
from .wpml import WPMLLanguage


def get_pending_posts_count(request):
    """Return count of draft posts for sidebar badge."""
    count = Post.objects.filter(status='draft').count()
    if count > 0:
        return count
    return None


def dashboard_callback(request, context):
    """Add custom dashboard statistics."""
    from apps.media.models import MediaFile
    from apps.seo.models import Keyword
    from apps.email_marketing.models import Subscriber, Campaign

    # Content statistics
    total_posts = Post.objects.count()
    published_posts = Post.objects.filter(status='publish').count()
    draft_posts = Post.objects.filter(status='draft').count()
    ai_posts = Post.objects.filter(is_ai_generated=True).count()

    # Language distribution
    german_posts = Post.objects.filter(language='de').count()
    english_posts = Post.objects.filter(language='en').count()

    # Other stats
    total_media = MediaFile.objects.count()
    tracked_keywords = Keyword.objects.filter(is_tracked=True).count()
    total_subscribers = Subscriber.objects.filter(status='subscribed').count()
    active_campaigns = Campaign.objects.filter(status='sending').count()

    context.update({
        "kpi": [
            {
                "title": "Total Posts",
                "metric": total_posts,
                "icon": "article",
                "footer": {
                    "text": f"{published_posts} published, {draft_posts} drafts",
                },
            },
            {
                "title": "AI Generated",
                "metric": ai_posts,
                "icon": "smart_toy",
                "footer": {
                    "text": f"{round(ai_posts/total_posts*100) if total_posts else 0}% of content",
                },
            },
            {
                "title": "Media Files",
                "metric": total_media,
                "icon": "perm_media",
            },
            {
                "title": "Tracked Keywords",
                "metric": tracked_keywords,
                "icon": "search",
            },
            {
                "title": "Subscribers",
                "metric": total_subscribers,
                "icon": "people",
            },
            {
                "title": "Active Campaigns",
                "metric": active_campaigns,
                "icon": "campaign",
            },
        ],
        "progress": [
            {
                "title": "German Content",
                "description": f"{german_posts} posts",
                "value": round(german_posts/total_posts*100) if total_posts else 0,
            },
            {
                "title": "English Content",
                "description": f"{english_posts} posts",
                "value": round(english_posts/total_posts*100) if total_posts else 0,
            },
        ],
    })

    return context


class TranslationInline(TabularInline):
    """Inline display of translations for a post"""
    model = Post
    fk_name = 'translation_of'
    fields = ['language', 'title', 'status', 'wp_id']
    readonly_fields = ['language', 'title', 'status', 'wp_id']
    extra = 0
    max_num = 0
    can_delete = False
    verbose_name = "Translation"
    verbose_name_plural = "Translations"
    tab = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = [
        'title', 'post_type', 'status', 'language_badge', 'translation_status',
        'is_ai_generated', 'seo_score', 'created_at'
    ]
    list_filter = ['post_type', 'status', 'language', 'is_ai_generated', 'categories']
    list_filter_submit = True
    search_fields = ['title', 'content', 'focus_keyword']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['categories', 'tags']
    readonly_fields = [
        'wp_id', 'synced_at', 'created_at', 'updated_at',
        'translation_links', 'wpml_trid'
    ]
    date_hierarchy = 'created_at'
    inlines = [TranslationInline]
    list_per_page = 25
    save_on_top = True
    show_facets = True

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'content', 'excerpt', 'featured_image')
        }),
        ('Status', {
            'fields': ('post_type', 'status')
        }),
        ('WPML Translation', {
            'fields': ('language', 'translation_of', 'source_language', 'wpml_trid', 'translation_links'),
            'description': 'Multilingual content settings powered by WPML'
        }),
        ('Taxonomy', {
            'fields': ('categories', 'tags')
        }),
        ('SEO (Rank Math)', {
            'fields': ('focus_keyword', 'meta_title', 'meta_description', 'seo_score'),
            'classes': ('collapse',)
        }),
        ('AI Generation', {
            'fields': ('is_ai_generated', 'ai_prompt', 'generation_model'),
            'classes': ('collapse',)
        }),
        ('WordPress Sync', {
            'fields': ('wp_id', 'wp_link', 'synced_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )

    @display(description="Language", ordering="language", label=True)
    def language_badge(self, obj):
        """Display language as a colored badge"""
        label_colors = {
            'de': 'primary',
            'en': 'info',
            'fr': 'info',
            'es': 'danger',
        }
        color = label_colors.get(obj.language, 'secondary')
        lang_name = dict(WPMLLanguage.get_choices()).get(obj.language, obj.language)
        return lang_name, color

    def translation_status(self, obj):
        """Show translation status icons"""
        if obj.is_original:
            translations = obj.translations.all()
            if translations.exists():
                langs = [t.language for t in translations]
                return format_html(
                    '<span title="Original with translations: {}">+ {}</span>',
                    ', '.join(langs), len(langs)
                )
            return format_html('<span title="Original, no translations">-</span>')
        else:
            return format_html(
                '<span title="Translation of post {}">TR {}</span>',
                obj.translation_of_id, obj.source_language.upper()
            )
    translation_status.short_description = 'Trans.'

    def translation_links(self, obj):
        """Display clickable links to all translations"""
        translations = obj.get_available_translations()
        links = []

        for lang, post in translations.items():
            if post.id == obj.id:
                links.append(format_html(
                    '<strong>{} (current)</strong>',
                    dict(WPMLLanguage.get_choices()).get(lang, lang)
                ))
            else:
                url = reverse('admin:content_post_change', args=[post.id])
                links.append(format_html(
                    '<a href="{}">{}: {}</a>',
                    url,
                    dict(WPMLLanguage.get_choices()).get(lang, lang),
                    post.title[:30]
                ))

        missing = obj.get_missing_languages()
        if missing:
            for lang in missing:
                links.append(format_html(
                    '<span style="color: #999;">{}: <em>missing</em></span>',
                    dict(WPMLLanguage.get_choices()).get(lang, lang)
                ))

        return format_html('<br>'.join(links)) if links else '-'
    translation_links.short_description = 'All Translations'

    def get_queryset(self, request):
        """Optimize query with related translations"""
        return super().get_queryset(request).select_related('translation_of').prefetch_related('translations')


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'language_badge', 'translation_info', 'wp_id']
    list_filter = ['language', 'parent']
    list_filter_submit = True
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['wpml_trid']

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'parent')
        }),
        ('WPML Translation', {
            'fields': ('language', 'translation_of', 'wpml_trid')
        }),
        ('WordPress', {
            'fields': ('wp_id',),
            'classes': ('collapse',)
        }),
    )

    @display(description="Lang", ordering="language", label=True)
    def language_badge(self, obj):
        lang_name = dict(WPMLLanguage.get_choices()).get(obj.language, obj.language)
        return lang_name, "secondary"

    def translation_info(self, obj):
        if obj.translation_of:
            return format_html('TR: {}', obj.translation_of.name)
        return '-'
    translation_info.short_description = 'Translation Of'


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'language_badge', 'translation_info', 'wp_id']
    list_filter = ['language']
    list_filter_submit = True
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['wpml_trid']

    fieldsets = (
        (None, {
            'fields': ('name', 'slug')
        }),
        ('WPML Translation', {
            'fields': ('language', 'translation_of', 'wpml_trid')
        }),
        ('WordPress', {
            'fields': ('wp_id',),
            'classes': ('collapse',)
        }),
    )

    @display(description="Lang", ordering="language", label=True)
    def language_badge(self, obj):
        lang_name = dict(WPMLLanguage.get_choices()).get(obj.language, obj.language)
        return lang_name, "secondary"

    def translation_info(self, obj):
        if obj.translation_of:
            return format_html('TR: {}', obj.translation_of.name)
        return '-'
    translation_info.short_description = 'Translation Of'


@admin.register(ContentTemplate)
class ContentTemplateAdmin(ModelAdmin):
    list_display = ['name', 'template_type', 'default_word_count', 'is_active', 'created_at']
    list_filter = ['template_type', 'is_active']
    list_filter_submit = True
    search_fields = ['name', 'system_prompt']


@admin.register(ContentGenerationJob)
class ContentGenerationJobAdmin(ModelAdmin):
    list_display = ['id', 'template', 'status', 'tokens_used', 'cost_usd', 'created_at']
    list_filter = ['status', 'template']
    list_filter_submit = True
    readonly_fields = ['created_at', 'completed_at', 'tokens_used', 'cost_usd']
