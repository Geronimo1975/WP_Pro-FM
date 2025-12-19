from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.conf import settings
from unfold.admin import ModelAdmin
from unfold.decorators import display, action
from .models import MediaFile, MediaCollection, MediaSyncLog
import requests
from requests.auth import HTTPBasicAuth
import os


@admin.register(MediaFile)
class MediaFileAdmin(ModelAdmin):
    list_display = ['image_preview', 'title', 'filename', 'media_type_display', 'file_size_mb', 'sync_status', 'action_buttons']
    list_filter = ['media_type', 'is_synced', 'is_local', 'created_at']
    list_filter_submit = True
    search_fields = ['title', 'filename', 'alt_text']
    readonly_fields = ['image_preview_large', 'action_buttons_detail', 'wp_id', 'wp_url', 'synced_at', 'created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': ('image_preview_large', 'action_buttons_detail')
        }),
        ('File Information', {
            'fields': ('title', 'filename', 'file', 'media_type', 'mime_type')
        }),
        ('WordPress', {
            'fields': ('wp_id', 'wp_url', 'is_synced', 'synced_at'),
        }),
        ('Metadata', {
            'fields': ('alt_text', 'caption', 'description', 'width', 'height', 'file_size')
        }),
        ('Timestamps', {
            'fields': ('wp_created_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/transfer-to-wp/', self.admin_site.admin_view(self.transfer_to_wordpress), name='media_mediafile_transfer_wp'),
            path('<int:pk>/download-from-wp/', self.admin_site.admin_view(self.download_from_wordpress), name='media_mediafile_download_wp'),
        ]
        return custom_urls + urls

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
        if obj.is_local and obj.is_synced:
            return "Full Sync", "success"
        elif obj.is_synced:
            return "WP Only", "info"
        elif obj.is_local:
            return "Local Only", "warning"
        return "Not Synced", "danger"

    def get_preview_url(self, obj):
        """Get the best URL for preview - prefer wp_url as it's always accessible"""
        # Prefer wp_url as local files may not be served through Apache
        if obj.wp_url:
            return obj.wp_url
        if obj.file:
            try:
                return obj.file.url
            except:
                pass
        return None

    def image_preview(self, obj):
        """Small thumbnail for list view"""
        if obj.media_type != 'image':
            return format_html('<span class="material-symbols-outlined">description</span>')
        url = self.get_preview_url(obj)
        if url:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 80px; object-fit: cover; border-radius: 4px;" loading="lazy" />',
                url
            )
        return '-'
    image_preview.short_description = 'Preview'

    def image_preview_large(self, obj):
        """Large preview for detail view with upload area"""
        if obj.media_type != 'image':
            icon = 'description'
            if obj.media_type == 'video':
                icon = 'movie'
            elif obj.media_type == 'audio':
                icon = 'audio_file'
            return format_html(
                '<div style="text-align: center; padding: 40px; background: #f5f5f5; border-radius: 8px;">'
                '<span class="material-symbols-outlined" style="font-size: 64px; color: #666;">{}</span>'
                '<p style="margin-top: 16px; color: #666;">{} file</p>'
                '</div>',
                icon, obj.media_type.title()
            )

        url = self.get_preview_url(obj)
        if url:
            return format_html(
                '<div style="text-align: center;">'
                '<img src="{}" style="max-width: 100%; max-height: 400px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />'
                '<p style="margin-top: 8px; color: #666; font-size: 12px;">{} x {} px</p>'
                '</div>',
                url, obj.width or '?', obj.height or '?'
            )
        return format_html(
            '<div style="text-align: center; padding: 40px; background: #f5f5f5; border-radius: 8px; border: 2px dashed #ccc;">'
            '<span class="material-symbols-outlined" style="font-size: 64px; color: #999;">cloud_upload</span>'
            '<p style="margin-top: 16px; color: #666;">No image available. Upload a file below.</p>'
            '</div>'
        )
    image_preview_large.short_description = 'Image Preview'

    def action_buttons(self, obj):
        """Action buttons for list view"""
        buttons = []

        # View on WordPress button
        if obj.wp_url:
            buttons.append(format_html(
                '<a href="{}" target="_blank" class="button" style="padding: 4px 8px; font-size: 11px; margin-right: 4px;" title="View on WordPress">'
                '<span class="material-symbols-outlined" style="font-size: 14px; vertical-align: middle;">open_in_new</span>'
                '</a>',
                obj.wp_url
            ))

        # Transfer to WordPress button (only if local file exists)
        if obj.file:
            transfer_url = reverse('admin:media_mediafile_transfer_wp', args=[obj.pk])
            buttons.append(format_html(
                '<a href="{}" class="button" style="padding: 4px 8px; font-size: 11px; background: #4CAF50; color: white;" title="Transfer to WordPress">'
                '<span class="material-symbols-outlined" style="font-size: 14px; vertical-align: middle;">cloud_upload</span>'
                '</a>',
                transfer_url
            ))
        # Download from WordPress button (if no local file but has wp_url)
        elif obj.wp_url and not obj.file:
            download_url = reverse('admin:media_mediafile_download_wp', args=[obj.pk])
            buttons.append(format_html(
                '<a href="{}" class="button" style="padding: 4px 8px; font-size: 11px; background: #2196F3; color: white;" title="Download from WordPress">'
                '<span class="material-symbols-outlined" style="font-size: 14px; vertical-align: middle;">cloud_download</span>'
                '</a>',
                download_url
            ))

        return format_html(''.join([str(b) for b in buttons])) if buttons else '-'
    action_buttons.short_description = 'Actions'

    def action_buttons_detail(self, obj):
        """Action buttons for detail view"""
        buttons = []

        # View on WordPress
        if obj.wp_url:
            buttons.append(format_html(
                '<a href="{}" target="_blank" class="button" style="margin-right: 8px; padding: 8px 16px;">'
                '<span class="material-symbols-outlined" style="vertical-align: middle; margin-right: 4px;">open_in_new</span>'
                'View on WordPress'
                '</a>',
                obj.wp_url
            ))

        # Transfer to WordPress
        if obj.file:
            transfer_url = reverse('admin:media_mediafile_transfer_wp', args=[obj.pk])
            buttons.append(format_html(
                '<a href="{}" class="button" style="margin-right: 8px; padding: 8px 16px; background: #4CAF50; color: white;">'
                '<span class="material-symbols-outlined" style="vertical-align: middle; margin-right: 4px;">cloud_upload</span>'
                'Transfer to WordPress'
                '</a>',
                transfer_url
            ))

        # Download from WordPress
        if obj.wp_url:
            download_url = reverse('admin:media_mediafile_download_wp', args=[obj.pk])
            btn_style = "background: #2196F3; color: white;" if not obj.file else ""
            buttons.append(format_html(
                '<a href="{}" class="button" style="margin-right: 8px; padding: 8px 16px; {}">'
                '<span class="material-symbols-outlined" style="vertical-align: middle; margin-right: 4px;">cloud_download</span>'
                '{}'
                '</a>',
                download_url,
                btn_style,
                'Download from WordPress' if not obj.file else 'Re-download from WordPress'
            ))

        if not buttons:
            return format_html('<p style="color: #666;">No actions available</p>')

        return format_html(
            '<div style="margin: 16px 0; padding: 16px; background: #f8f9fa; border-radius: 8px;">{}</div>',
            format_html(''.join([str(b) for b in buttons]))
        )
    action_buttons_detail.short_description = 'Quick Actions'

    def transfer_to_wordpress(self, request, pk):
        """Transfer local file to WordPress"""
        obj = self.get_object(request, pk)

        if not obj.file:
            messages.error(request, 'No local file to transfer.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('admin:media_mediafile_changelist')))

        try:
            site_url = settings.WP_SITE_URL.rstrip('/')
            auth = HTTPBasicAuth(settings.WP_USERNAME, settings.WP_APP_PASSWORD)

            # Determine content type
            content_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.pdf': 'application/pdf',
                '.mp4': 'video/mp4',
                '.mp3': 'audio/mpeg',
            }
            ext = os.path.splitext(obj.file.name)[1].lower()
            content_type = content_types.get(ext, 'application/octet-stream')

            # Upload to WordPress
            url = f"{site_url}/?rest_route=/wp/v2/media"
            headers = {
                'Content-Disposition': f'attachment; filename="{obj.filename}"',
                'Content-Type': content_type
            }

            with obj.file.open('rb') as f:
                response = requests.post(url, data=f, headers=headers, auth=auth, timeout=60)

            if response.status_code in [200, 201]:
                wp_media = response.json()
                obj.wp_id = wp_media.get('id')
                obj.wp_url = wp_media.get('source_url', '')
                obj.is_synced = True
                obj.save()
                messages.success(request, f'Successfully transferred "{obj.title}" to WordPress!')
            else:
                messages.error(request, f'Failed to transfer to WordPress: {response.text[:200]}')

        except Exception as e:
            messages.error(request, f'Error transferring to WordPress: {str(e)}')

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('admin:media_mediafile_changelist')))

    def download_from_wordpress(self, request, pk):
        """Download file from WordPress to local storage"""
        from django.core.files.base import ContentFile
        from django.utils import timezone

        obj = self.get_object(request, pk)

        if not obj.wp_url:
            messages.error(request, 'No WordPress URL to download from.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('admin:media_mediafile_changelist')))

        try:
            # Download file from WordPress
            response = requests.get(obj.wp_url, timeout=60)
            response.raise_for_status()

            # Save to local storage
            filename = obj.filename or os.path.basename(obj.wp_url)
            obj.file.save(filename, ContentFile(response.content), save=False)
            obj.is_local = True
            obj.file_size = len(response.content)
            obj.synced_at = timezone.now()
            obj.save()

            messages.success(request, f'Successfully downloaded "{obj.title}" from WordPress!')

        except Exception as e:
            messages.error(request, f'Error downloading from WordPress: {str(e)}')

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('admin:media_mediafile_changelist')))

    # Bulk actions
    @action(description="Transfer selected to WordPress")
    def transfer_selected_to_wordpress(self, request, queryset):
        success = 0
        failed = 0
        for obj in queryset.filter(file__isnull=False):
            try:
                # Similar logic as transfer_to_wordpress
                site_url = settings.WP_SITE_URL.rstrip('/')
                auth = HTTPBasicAuth(settings.WP_USERNAME, settings.WP_APP_PASSWORD)

                ext = os.path.splitext(obj.file.name)[1].lower()
                content_types = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp'}
                content_type = content_types.get(ext, 'application/octet-stream')

                url = f"{site_url}/?rest_route=/wp/v2/media"
                headers = {'Content-Disposition': f'attachment; filename="{obj.filename}"', 'Content-Type': content_type}

                with obj.file.open('rb') as f:
                    response = requests.post(url, data=f, headers=headers, auth=auth, timeout=60)

                if response.status_code in [200, 201]:
                    wp_media = response.json()
                    obj.wp_id = wp_media.get('id')
                    obj.wp_url = wp_media.get('source_url', '')
                    obj.is_synced = True
                    obj.save()
                    success += 1
                else:
                    failed += 1
            except:
                failed += 1

        messages.success(request, f'Transferred {success} files to WordPress. Failed: {failed}')

    @action(description="Download selected from WordPress")
    def download_selected_from_wordpress(self, request, queryset):
        from django.core.files.base import ContentFile
        from django.utils import timezone

        success = 0
        failed = 0
        for obj in queryset.filter(wp_url__isnull=False).exclude(wp_url=''):
            try:
                response = requests.get(obj.wp_url, timeout=60)
                response.raise_for_status()

                filename = obj.filename or os.path.basename(obj.wp_url)
                obj.file.save(filename, ContentFile(response.content), save=False)
                obj.is_local = True
                obj.file_size = len(response.content)
                obj.synced_at = timezone.now()
                obj.save()
                success += 1
            except:
                failed += 1

        messages.success(request, f'Downloaded {success} files from WordPress. Failed: {failed}')

    actions = ['transfer_selected_to_wordpress', 'download_selected_from_wordpress']


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
