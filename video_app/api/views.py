from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from django.http import FileResponse, Http404

from authentication_app.authentication import CookieJWTAuthentication
from video_app.models import Video
from video_app.services import get_playlist_path, get_segment_path
from .serializers import VideoListSerializer


class VideoListView(ListAPIView):
    """List available videos, newest first, for authenticated users."""

    queryset = Video.objects.all()
    serializer_class = VideoListSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class HLSPlaylistView(APIView):
    """Serve the HLS master playlist for a video and resolution."""

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        """Return the m3u8 manifest, or 404 if it has not been generated."""
        playlist_path = get_playlist_path(movie_id, resolution)
        if playlist_path is None:
            raise Http404("Manifest not found.")
        return FileResponse(
            open(playlist_path, "rb"),
            content_type="application/vnd.apple.mpegurl",
        )


class HLSSegmentView(APIView):
    """Serve a single HLS video segment (.ts) for a video and resolution."""

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        """Return the requested .ts segment, or 404 if it does not exist."""
        segment_path = get_segment_path(movie_id, resolution, segment)
        if segment_path is None:
            raise Http404("Segment not found.")
        return FileResponse(
            open(segment_path, "rb"), content_type="video/MP2T"
        )
