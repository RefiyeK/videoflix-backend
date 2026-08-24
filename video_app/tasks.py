from video_app.models import Video
from video_app.services import RESOLUTIONS, convert_to_resolution


def convert_video_to_hls(video_id):
    """Convert one uploaded video into HLS for every target resolution.

    Runs in the background via Django RQ so the admin request returns
    immediately instead of blocking on the lengthy FFMPEG work.
    """
    video = Video.objects.get(id=video_id)
    source_path = video.video_file.path
    for resolution in RESOLUTIONS:
        convert_to_resolution(source_path, video_id, resolution)
