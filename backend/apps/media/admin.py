from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import MediaFile, MediaCollection, MediaSyncLog


@admin.register(MediaFile)
class MediaFileAdmin(ModelAdmin):
    list_display = ['title', 'filename', 'media_type_display', 'file_size_mb', 'sync_status', 'created_at']
    list_filter = ['media_type', 'is_synced', 'is_local', 'created_at']
    list_filter_submit = True
    search_fields = ['title', 'filename', 'alt_text']
    readonly_fields = ['wp_id', 'wp_url', 'synced_at', 'created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 25

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

    @display(description="Type", ordering="media_type", label=True)
    def media_type_display(self, obj):
        colors = {
            'image': 'success',
            'video': 'warning',
            'audio': 'info',
            'document': 'secondary',
        }
        return obj.media_type, colors.get(obj.media_type, 'secondary')

    @display(description="Synced", label=True)
    def sync_status(self, obj):
        if obj.is_synced:
            return "Synced", "success"
        return "Local", "warning"


@admin.register(MediaCollection)
class MediaCollectionAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'file_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['media_files']
    list_per_page = 25


@admin.register(MediaSyncLog)
class MediaSyncLogAdmin(ModelAdmin):
    list_display = ['started_at', 'status_display', 'total_items', 'synced_items', 'failed_items']
    list_filter = ['status', 'started_at']
    list_filter_submit = True
    readonly_fields = ['started_at', 'completed_at', 'total_items', 'synced_items', 'failed_items', 'error_message']
    list_per_page = 25

    @display(description="Status", ordering="status", label=True)
    def status_display(self, obj):
        colors = {
            'pending': 'warning',
            'running': 'info',
            'completed': 'success',
            'failed': 'danger',
        }
        return obj.status, colors.get(obj.status, 'secondary')
