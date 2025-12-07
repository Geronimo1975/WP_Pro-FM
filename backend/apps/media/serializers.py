from rest_framework import serializers
from .models import MediaFile, MediaCollection, MediaSyncLog


class MediaFileSerializer(serializers.ModelSerializer):
    file_size_mb = serializers.ReadOnlyField()
    is_image = serializers.ReadOnlyField()

    class Meta:
        model = MediaFile
        fields = [
            'id', 'wp_id', 'wp_url', 'title', 'filename', 'file',
            'mime_type', 'media_type', 'file_size', 'file_size_mb',
            'alt_text', 'caption', 'description', 'width', 'height',
            'is_synced', 'is_local', 'is_image', 'created_at', 'updated_at'
        ]
        read_only_fields = ['wp_id', 'wp_url', 'synced_at']


class MediaCollectionSerializer(serializers.ModelSerializer):
    file_count = serializers.ReadOnlyField()
    media_files = MediaFileSerializer(many=True, read_only=True)

    class Meta:
        model = MediaCollection
        fields = ['id', 'name', 'slug', 'description', 'file_count', 'media_files', 'created_at']


class MediaSyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaSyncLog
        fields = '__all__'
