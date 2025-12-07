from django.contrib import admin
from .models import Post, Category, Tag, ContentTemplate, ContentGenerationJob


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'post_type', 'status', 'language', 'is_ai_generated', 'seo_score', 'created_at']
    list_filter = ['post_type', 'status', 'language', 'is_ai_generated', 'categories']
    search_fields = ['title', 'content', 'focus_keyword']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['categories', 'tags']
    readonly_fields = ['wp_id', 'synced_at', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'content', 'excerpt', 'featured_image')
        }),
        ('Status', {
            'fields': ('post_type', 'status', 'language')
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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'language', 'wp_id']
    list_filter = ['language', 'parent']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'language', 'wp_id']
    list_filter = ['language']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ContentTemplate)
class ContentTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'default_word_count', 'is_active', 'created_at']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'system_prompt']


@admin.register(ContentGenerationJob)
class ContentGenerationJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'template', 'status', 'tokens_used', 'cost_usd', 'created_at']
    list_filter = ['status', 'template']
    readonly_fields = ['created_at', 'completed_at', 'tokens_used', 'cost_usd']
