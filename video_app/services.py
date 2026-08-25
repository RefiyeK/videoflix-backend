import subprocess
from pathlib import Path

from django.conf import settings

# Target resolutions and their vertical pixel height for HLS conversion.
RESOLUTIONS = {
    "480p": 480,
    "720p": 720,
    "1080p": 1080,
}

# Two seconds per segment keeps switching responsive without too many files.
SEGMENT_DURATION = "2"


def build_output_dir(video_id, resolution):
    """Return (and create) the media folder for one video and resolution."""
    output_dir = Path(settings.MEDIA_ROOT) / "video" / \
        str(video_id) / resolution
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def build_ffmpeg_command(source_path, output_dir, height):
    """Assemble the FFMPEG arguments that turn a source file into HLS."""
    playlist = output_dir / "index.m3u8"
    segments = output_dir / "%03d.ts"
    return [
        "ffmpeg", "-y", "-i", str(source_path),
        "-vf", f"scale=-2:{height}",
        "-c:v", "libx264", "-c:a", "aac",
        "-hls_time", SEGMENT_DURATION,
        "-hls_playlist_type", "vod",
        "-hls_segment_filename", str(segments),
        str(playlist),
    ]


def convert_to_resolution(source_path, video_id, resolution):
    """Convert one source video into HLS files for a single resolution."""
    height = RESOLUTIONS[resolution]
    output_dir = build_output_dir(video_id, resolution)
    command = build_ffmpeg_command(source_path, output_dir, height)
    subprocess.run(command, check=True, capture_output=True)


def get_playlist_path(video_id, resolution):
    """Return the index.m3u8 path, or None if it does not exist."""
    playlist = Path(settings.MEDIA_ROOT) / "video" / \
        str(video_id) / resolution / "index.m3u8"
    return playlist if playlist.exists() else None


def get_segment_path(video_id, resolution, segment):
    """Return the .ts segment path, or None if it does not exist."""
    segment_file = Path(settings.MEDIA_ROOT) / "video" / \
        str(video_id) / resolution / segment
    return segment_file if segment_file.exists() else None
