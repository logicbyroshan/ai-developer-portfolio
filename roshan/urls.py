from django.urls import path
from . import views

app_name = "roshan"

urlpatterns = [
    # About page
    path("about/", views.AboutMeView.as_view(), name="about"),
    # Resources
    path("resources/", views.ResourcesListView.as_view(), name="resources"),
    path(
        "resources/<slug:slug>/",
        views.ResourceDetailView.as_view(),
        name="resource_detail",
    ),
    # Playlists/Music
    path("playlist/", views.my_playlist, name="my_playlist"),
    path("playlist/<int:playlist_id>/", views.playlist_detail, name="playlist_detail"),
    # Playlist Management (admin only)
    path(
        "playlist/create/", views.create_manual_playlist, name="create_manual_playlist"
    ),
    path(
        "playlist/<int:playlist_id>/edit/",
        views.edit_manual_playlist,
        name="edit_manual_playlist",
    ),
    path(
        "playlist/<int:playlist_id>/delete/",
        views.delete_manual_playlist,
        name="delete_manual_playlist",
    ),
    path(
        "playlist/<int:playlist_id>/add-track/",
        views.add_track_to_playlist,
        name="add_track_to_playlist",
    ),
    path(
        "track/<int:track_id>/delete/",
        views.delete_manual_track,
        name="delete_manual_track",
    ),
    # Legal pages
    path("privacy/", views.PrivacyPolicyView.as_view(), name="privacy_policy"),
    path("terms/", views.TermsOfServiceView.as_view(), name="terms_of_service"),
]
