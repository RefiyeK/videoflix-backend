from rest_framework import serializers

from video_app.models import Video


class VideoListSerializer(serializers.ModelSerializer):
    """Serialize a video for the dashboard list, exposing an absolute thumbnail URL."""

    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            "id",
            "created_at",
            "title",
            "description",
            "thumbnail_url",
            "category",
        ]

    def get_thumbnail_url(self, obj):
        """Return the fully qualified URL so the frontend can load the image directly."""
        request = self.context.get("request")
        return request.build_absolute_uri(obj.thumbnail.url)