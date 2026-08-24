import shutil
import tempfile
from pathlib import Path

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from unittest.mock import patch

from video_app.models import Video

User = get_user_model()

# Route media writes to a temporary folder so tests never touch real media.
TEMP_MEDIA_ROOT = tempfile.mkdtemp()


class VideoListTests(APITestCase):
    """Tests for the authenticated GET /api/video/ endpoint."""

    def setUp(self):
        """Create an active user and one video before each test."""
        self.user = User.objects.create_user(
            email="viewer@example.com", password="StrongPass123"
        )
        self.user.is_active = True
        self.user.save()

        self.video = Video.objects.create(
            title="Ocean Waves",
            description="Relaxing ocean waves at sunset.",
            category="Documentary",
            thumbnail=SimpleUploadedFile(
                "thumb.jpg", b"fake-image", content_type="image/jpeg"),
            video_file=SimpleUploadedFile(
                "clip.mp4", b"fake-video", content_type="video/mp4"),
        )
        self.url = reverse("video-list")

    def authenticate(self):
        """Set a valid access token cookie so the request is authenticated."""
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies["access_token"] = str(refresh.access_token)

    def test_list_requires_authentication(self):
        """An anonymous request without a token cookie is rejected with 401."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_videos_when_authenticated(self):
        """An authenticated user receives the list of videos with 200."""
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_contains_expected_fields(self):
        """Each video item exposes all fields the frontend relies on."""
        self.authenticate()
        response = self.client.get(self.url)
        first = response.data[0]
        self.assertEqual(first["title"], "Ocean Waves")
        self.assertEqual(first["category"], "Documentary")
        self.assertIn("thumbnail_url", first)
        self.assertIn("created_at", first)

    def test_thumbnail_url_is_absolute(self):
        """The thumbnail_url is a fully qualified URL, not a relative path."""
        self.authenticate()
        response = self.client.get(self.url)
        thumbnail_url = response.data[0]["thumbnail_url"]
        self.assertTrue(thumbnail_url.startswith("http"))


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class HLSPlaylistTests(APITestCase):
    """Tests for the GET .../<resolution>/index.m3u8 playlist endpoint."""

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary media folder once all tests have run."""
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        """Create an active user and one HLS playlist file on disk."""
        self.user = User.objects.create_user(
            email="viewer@example.com", password="StrongPass123"
        )
        self.user.is_active = True
        self.user.save()

        self.movie_id = 1
        self.resolution = "480p"
        output_dir = Path(TEMP_MEDIA_ROOT) / "video" / \
            str(self.movie_id) / self.resolution
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "index.m3u8").write_text("#EXTM3U\n")

        self.url = reverse(
            "video-playlist",
            kwargs={"movie_id": self.movie_id, "resolution": self.resolution},
        )

    def authenticate(self):
        """Set a valid access token cookie so the request is authenticated."""
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies["access_token"] = str(refresh.access_token)

    def test_playlist_requires_authentication(self):
        """An anonymous request is rejected with 401."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_playlist_success_returns_manifest(self):
        """An authenticated request returns 200 with the m3u8 content type."""
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"],
                         "application/vnd.apple.mpegurl")

    def test_playlist_missing_file_returns_404(self):
        """A request for a resolution without a manifest returns 404."""
        self.authenticate()
        missing_url = reverse(
            "video-playlist",
            kwargs={"movie_id": self.movie_id, "resolution": "1080p"},
        )
        response = self.client.get(missing_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class HLSSegmentTests(APITestCase):
    """Tests for the GET .../<resolution>/<segment> segment endpoint."""

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary media folder once all tests have run."""
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        """Create an active user and one .ts segment file on disk."""
        self.user = User.objects.create_user(
            email="viewer@example.com", password="StrongPass123"
        )
        self.user.is_active = True
        self.user.save()

        self.movie_id = 1
        self.resolution = "480p"
        self.segment = "000.ts"
        output_dir = Path(TEMP_MEDIA_ROOT) / "video" / \
            str(self.movie_id) / self.resolution
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / self.segment).write_bytes(b"fake-segment-data")

        self.url = reverse(
            "video-segment",
            kwargs={
                "movie_id": self.movie_id,
                "resolution": self.resolution,
                "segment": self.segment,
            },
        )

    def authenticate(self):
        """Set a valid access token cookie so the request is authenticated."""
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies["access_token"] = str(refresh.access_token)

    def test_segment_requires_authentication(self):
        """An anonymous request is rejected with 401."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_segment_success_returns_ts(self):
        """An authenticated request returns 200 with the MP2T content type."""
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "video/MP2T")

    def test_segment_missing_file_returns_404(self):
        """A request for a segment that does not exist returns 404."""
        self.authenticate()
        missing_url = reverse(
            "video-segment",
            kwargs={
                "movie_id": self.movie_id,
                "resolution": self.resolution,
                "segment": "999.ts",
            },
        )
        response = self.client.get(missing_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class HLSConversionTaskTests(APITestCase):
    """Tests for the background conversion task using a mocked FFMPEG call."""

    def setUp(self):
        """Create one video whose source file will be converted."""
        self.video = Video.objects.create(
            title="Clip",
            description="A short clip.",
            category="Action",
            thumbnail=SimpleUploadedFile(
                "t.jpg", b"img", content_type="image/jpeg"),
            video_file=SimpleUploadedFile(
                "c.mp4", b"vid", content_type="video/mp4"),
        )

    @patch("video_app.tasks.convert_to_resolution")
    def test_task_converts_every_resolution(self, mock_convert):
        """The task calls the converter once per target resolution."""
        from video_app.tasks import convert_video_to_hls
        from video_app.services import RESOLUTIONS

        convert_video_to_hls(self.video.id)
        self.assertEqual(mock_convert.call_count, len(RESOLUTIONS))


class FFmpegCommandTests(APITestCase):
    """Tests for the FFMPEG command builder used during conversion."""

    def test_command_targets_requested_height(self):
        """The built command scales to the requested resolution height."""
        from video_app.services import build_ffmpeg_command

        command = build_ffmpeg_command("in.mp4", Path("/tmp"), 720)
        self.assertIn("scale=-2:720", command)
        self.assertIn("libx264", command)
