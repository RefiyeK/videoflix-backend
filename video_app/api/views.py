from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from authentication_app.authentication import CookieJWTAuthentication
from video_app.models import Video
from .serializers import VideoListSerializer


class VideoListView(ListAPIView):
    """Return all available videos, newest first, for authenticated users only."""

    queryset = Video.objects.all()
    serializer_class = VideoListSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]