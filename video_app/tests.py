from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from video_app.models import Video

User = get_user_model()


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
            thumbnail=SimpleUploadedFile("thumb.jpg", b"fake-image", content_type="image/jpeg"),
            video_file=SimpleUploadedFile("clip.mp4", b"fake-video", content_type="video/mp4"),
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