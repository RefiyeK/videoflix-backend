import django_rq
from django.db.models.signals import post_save
from django.dispatch import receiver

from video_app.models import Video
from video_app.tasks import convert_video_to_hls


@receiver(post_save, sender=Video)
def trigger_hls_conversion(sender, instance, created, **kwargs):
    """Queue HLS conversion in the background when a new video is uploaded."""
    if not created:
        return
    queue = django_rq.get_queue("default")
    queue.enqueue(convert_video_to_hls, instance.id)
