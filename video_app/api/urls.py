from django.urls import path, re_path

from .views import VideoListView, HLSPlaylistView, HLSSegmentView

urlpatterns = [
    path("video/", VideoListView.as_view(), name="video-list"),
    path(
        "video/<int:movie_id>/<str:resolution>/index.m3u8",
        HLSPlaylistView.as_view(),
        name="video-playlist",
    ),
    re_path(
        r"^video/(?P<movie_id>\d+)/(?P<resolution>[^/]+)/"
        r"(?P<segment>[\w-]+\.ts)$",
        HLSSegmentView.as_view(),
        name="video-segment",
    ),
]
