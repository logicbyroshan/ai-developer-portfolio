import logging
import json
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import TemplateView, ListView, DetailView
from django.views.decorators.http import require_POST
from django.db.models import Q

from .models import (
    AboutMeConfiguration,
    ResourcesConfiguration,
    ResourceCategory,
    Resource,
    ResourceView,
    ManualPlaylist,
    ManualTrack,
)
from .forms import ResourceFilterForm, ManualPlaylistForm, ManualTrackForm

logger = logging.getLogger(__name__)


# =========================================================================
# ABOUT ME VIEW
# =========================================================================


class AboutMeView(TemplateView):
    """View for the About Me page."""

    template_name = "about-me.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            config = AboutMeConfiguration.objects.first()
            context["config"] = config
        except AboutMeConfiguration.DoesNotExist:
            context["config"] = None

        # Add FAQ data for the FAQ section
        from portfolio.models import FAQ

        context["faqs"] = FAQ.objects.order_by("order")

        return context


# =========================================================================
# RESOURCES VIEWS
# =========================================================================


class ResourcesListView(ListView):
    """View for the resources list page with filtering and pagination."""

    model = Resource
    template_name = "resources-list.html"
    context_object_name = "resources"
    paginate_by = 12

    def get_queryset(self):
        queryset = Resource.objects.filter(is_active=True)

        # Get filter parameters from form
        category_slug = self.request.GET.get("category")
        resource_type = self.request.GET.get("type")
        search_query = self.request.GET.get("search")
        sort_by = self.request.GET.get("sort", "newest")

        # Apply filters
        if category_slug and category_slug != "all":
            queryset = queryset.filter(categories__slug=category_slug)

        if resource_type and resource_type != "all":
            queryset = queryset.filter(resource_type=resource_type)

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(author__icontains=search_query)
            )

        # Apply sorting
        if sort_by == "oldest":
            queryset = queryset.order_by("created_date")
        elif sort_by == "rating":
            queryset = queryset.order_by("-personal_rating", "-created_date")
        elif sort_by == "title":
            queryset = queryset.order_by("title")
        else:  # newest
            queryset = queryset.order_by("-created_date")

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add configuration
        try:
            resources_config = ResourcesConfiguration.objects.first()
            context["resources_config"] = resources_config
        except ResourcesConfiguration.DoesNotExist:
            context["resources_config"] = None

        # Add filter form and related data
        context["form"] = ResourceFilterForm(self.request.GET)
        context["categories"] = ResourceCategory.objects.all().order_by("order", "name")
        context["resource_types"] = Resource.ResourceType.choices

        # Add current filter values
        context["current_category"] = self.request.GET.get("category", "all")
        context["current_type"] = self.request.GET.get("type", "all")
        context["current_search"] = self.request.GET.get("search", "")
        context["current_sort"] = self.request.GET.get("sort", "newest")

        return context


class ResourceDetailView(DetailView):
    """View for individual resource detail pages."""

    model = Resource
    template_name = "resource-detail.html"
    context_object_name = "resource"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Resource.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resource = self.get_object()

        # Get related resources
        context["related_resources"] = self._get_related_resources(resource)

        return context

    def get(self, request, *args, **kwargs):
        # Record view
        resource = self.get_object()
        ResourceView.objects.create(
            resource=resource,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        return super().get(request, *args, **kwargs)

    def _get_related_resources(self, resource):
        """Get related resources based on categories and technologies."""
        try:
            # Get resources with similar categories or technologies
            related = (
                Resource.objects.filter(
                    Q(categories__in=resource.categories.all())
                    | Q(technologies__in=resource.technologies.all()),
                    is_active=True,
                )
                .exclude(pk=resource.pk)
                .distinct()[:4]
            )

            return related
        except Exception:
            return Resource.objects.none()

    def _get_client_ip(self, request):
        """Get client IP address from request.

        Uses REMOTE_ADDR which is set by the web server and cannot be spoofed.
        X-Forwarded-For is only trusted if the server is behind a known reverse proxy.
        """
        return request.META.get("REMOTE_ADDR", "0.0.0.0")


# =========================================================================
# MUSIC/PLAYLIST VIEWS
# =========================================================================


def my_playlist(request):
    """Public view showing manual playlists"""
    playlists = ManualPlaylist.objects.filter(is_public=True)

    return render(
        request,
        "music/playlist.html",
        {"playlists": playlists},
    )


def playlist_detail(request, playlist_id):
    """Show detailed view of a specific playlist with tracks"""
    playlist = get_object_or_404(ManualPlaylist, id=playlist_id, is_public=True)
    tracks = playlist.manual_tracks.filter(is_active=True)

    # Prepare tracks data for JavaScript player
    tracks_data = []
    for track in tracks:
        audio_source = track.primary_audio_source
        tracks_data.append(
            {
                "id": track.id,
                "name": track.name,
                "artist": track.artist,
                "album": track.album,
                "preview_url": audio_source["url"] if audio_source else None,
                "audio_type": audio_source["type"] if audio_source else None,
                "external_url": track.youtube_url or "#",
                "duration_ms": track.duration_ms,
                "track_number": track.track_number,
                "youtube_url": track.youtube_url,
                "apple_music_url": track.apple_music_url,
            }
        )

    return render(
        request,
        "music/playlist_detail.html",
        {
            "playlist": playlist,
            "tracks": tracks,
            "tracks_json": json.dumps(tracks_data),
        },
    )


# =========================================================================
# MANUAL PLAYLIST MANAGEMENT VIEWS (Admin only)
# =========================================================================


def is_admin(user):
    """Check if user is admin/staff"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin)
def create_manual_playlist(request):
    """Create a new manual playlist"""
    if request.method == "POST":
        form = ManualPlaylistForm(request.POST, request.FILES)
        if form.is_valid():
            playlist = form.save()
            messages.success(
                request, f'Playlist "{playlist.name}" created successfully!'
            )
            return JsonResponse(
                {
                    "success": True,
                    "playlist_id": playlist.id,
                    "redirect_url": f"/playlist/{playlist.id}/",
                }
            )
        else:
            return JsonResponse({"success": False, "errors": form.errors})
    else:
        form = ManualPlaylistForm()

    return render(request, "music/create_playlist_modal.html", {"form": form})


@login_required
@user_passes_test(is_admin)
def add_track_to_playlist(request, playlist_id):
    """Add a track to a manual playlist"""
    playlist = get_object_or_404(ManualPlaylist, id=playlist_id)

    if request.method == "POST":
        form = ManualTrackForm(request.POST, request.FILES)
        if form.is_valid():
            track = form.save(commit=False)
            track.playlist = playlist

            # Set track number if not provided
            if not track.track_number:
                last_track = playlist.manual_tracks.order_by("-track_number").first()
                track.track_number = (last_track.track_number + 1) if last_track else 1

            track.save()
            messages.success(request, f'Track "{track.name}" added to playlist!')
            return JsonResponse(
                {"success": True, "track_id": track.id, "track_name": track.name}
            )
        else:
            return JsonResponse({"success": False, "errors": form.errors})
    else:
        form = ManualTrackForm()

    return render(
        request, "music/add_track_modal.html", {"form": form, "playlist": playlist}
    )


@login_required
@user_passes_test(is_admin)
def edit_manual_playlist(request, playlist_id):
    """Edit a manual playlist"""
    playlist = get_object_or_404(ManualPlaylist, id=playlist_id)

    if request.method == "POST":
        form = ManualPlaylistForm(request.POST, request.FILES, instance=playlist)
        if form.is_valid():
            form.save()
            messages.success(
                request, f'Playlist "{playlist.name}" updated successfully!'
            )
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": form.errors})
    else:
        form = ManualPlaylistForm(instance=playlist)

    return render(
        request, "music/edit_playlist_modal.html", {"form": form, "playlist": playlist}
    )


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_manual_playlist(request, playlist_id):
    """Delete a manual playlist"""
    playlist = get_object_or_404(ManualPlaylist, id=playlist_id)
    playlist_name = playlist.name
    playlist.delete()
    messages.success(request, f'Playlist "{playlist_name}" deleted successfully!')
    return JsonResponse({"success": True})


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_manual_track(request, track_id):
    """Delete a track from a manual playlist"""
    track = get_object_or_404(ManualTrack, id=track_id)
    track_name = track.name
    track.delete()
    messages.success(request, f'Track "{track_name}" removed from playlist!')
    return JsonResponse({"success": True})


# =========================================================================
# LEGAL PAGES VIEWS
# =========================================================================


class PrivacyPolicyView(TemplateView):
    """View for the Privacy Policy page."""

    template_name = "legal/privacy-policy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Privacy Policy"
        context["last_updated"] = "October 2025"
        return context


class TermsOfServiceView(TemplateView):
    """View for the Terms of Service page."""

    template_name = "legal/terms-of-service.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Terms of Service"
        context["last_updated"] = "October 2025"
        return context
