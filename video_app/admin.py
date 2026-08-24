from django.contrib import admin

from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Admin configuration for browsing and uploading videos."""

    list_display = ("id", "title", "category", "created_at")
    list_filter = ("category",)
    search_fields = ("title", "description")
