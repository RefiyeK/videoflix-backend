from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'video_app'

    def ready(self):
        """Import signal handlers to enable HLS conversion on upload."""
        import video_app.signals  # noqa: F401
