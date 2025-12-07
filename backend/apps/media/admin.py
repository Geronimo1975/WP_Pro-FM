from django.contrib import admin
from .models import MediaFile, MediaCollection, MediaSyncLog


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ['title', 'filename', 'media_type', 'file_size_mb', 'is_synced', 'created_at']
    list_filter = ['media_type', 'is_synced', 'is_local', 'created_at']
    search_fields = ['title', 'filename', 'alt_text']
    readonly_fields = ['wp_id', 'wp_url', 'synced_at', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('title', 'filename', 'file', 'media_type', 'mime_type')
        }),
        ('WordPress', {
            'fields': ('wp_id', 'wp_url', 'is_synced', 'synced_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('alt_text', 'caption', 'description', 'width', 'height', 'file_size')
        }),
        ('Timestamps', {
            'fields': ('wp_created_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MediaCollection)
class MediaCollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'file_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['media_files']


@admin.register(MediaSyncLog)
class MediaSyncLogAdmin(admin.ModelAdmin):
    list_display = ['started_at', 'status', 'total_items', 'synced_items', 'failed_items']
    list_filter = ['status', 'started_at']
    readonly_fields = ['started_at', 'completed_at', 'total_items', 'synced_items', 'failed_items', 'error_message']
