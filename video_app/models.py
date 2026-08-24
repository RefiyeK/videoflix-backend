from django.db import models


class Video(models.Model):
    """A single video offered for streaming, converted to HLS after upload."""

    CATEGORY_CHOICES = [
        ("Drama", "Drama"),
        ("Romance", "Romance"),
        ("Comedy", "Comedy"),
        ("Action", "Action"),
        ("Documentary", "Documentary"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    thumbnail = models.ImageField(upload_to="thumbnails/")
    video_file = models.FileField(upload_to="videos/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Newest first — the frontend "newest" section relies on this order.
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
