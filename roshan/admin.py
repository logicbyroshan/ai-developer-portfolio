import csv
from django.http import HttpResponse
from django.contrib import admin
from .models import (
    AboutMeConfiguration,
    ResourcesConfiguration,
    ResourceCategory,
    Resource,
    ResourceView,
    ManualPlaylist,
    ManualTrack,
)


# =========================================================================
# ABOUT ME ADMIN
# =========================================================================


@admin.register(AboutMeConfiguration)
class AboutMeConfigurationAdmin(admin.ModelAdmin):
    """Admin for the About Me Configuration object."""

    fieldsets = (
        ("Page Header", {"fields": ("page_title", "intro_paragraph")}),
        ("Profile Section", {"fields": ("profile_image", "detailed_description")}),
        (
            "Personal Information",
            {"fields": ("birthday", "location", "open_to_work", "email")},
        ),
        (
            "Social Media",
            {
                "fields": (
                    "github_url",
                    "linkedin_url",
                    "twitter_url",
                    "youtube_url",
                    "instagram_url",
                    "website_url",
                )
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj:  # If editing existing object, show timestamps
            fieldsets += (("Timestamps", {"fields": ("created_at", "updated_at")}),)
        return fieldsets

    def has_add_permission(self, request):
        """Only allow adding if no instance exists."""
        return not AboutMeConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion to maintain singleton pattern."""
        return False


# =========================================================================
# RESOURCES ADMIN INTERFACES
# =========================================================================


@admin.register(ResourcesConfiguration)
class ResourcesConfigurationAdmin(admin.ModelAdmin):
    """Admin for Resources page configuration."""

    def has_add_permission(self, request):
        """Prevent creating multiple instances."""
        return not ResourcesConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the configuration."""
        return False

    fieldsets = (
        ("Page Header", {"fields": ("page_title", "intro_paragraph")}),
        (
            "Content Settings",
            {"fields": ("resources_description", "resources_per_page")},
        ),
    )


@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    """Admin for resource categories."""

    list_display = ("name", "slug", "order", "description")
    list_editable = ("order",)
    search_fields = ("name", "description")
    ordering = ("order", "name")

    fieldsets = (
        ("Category Information", {"fields": ("name", "description", "icon")}),
        ("Display Settings", {"fields": ("order",)}),
    )


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """Admin for resources with comprehensive management features."""

    list_display = (
        "title",
        "resource_type",
        "author",
        "personal_rating",
        "is_featured",
        "is_active",
        "created_date",
    )
    list_filter = (
        "resource_type",
        "is_featured",
        "is_active",
        "personal_rating",
        "categories",
        "created_date",
    )
    search_fields = ("title", "description", "author")
    filter_horizontal = ("categories", "technologies")
    list_editable = ("is_featured", "is_active", "personal_rating")
    date_hierarchy = "created_date"
    ordering = ("order", "-created_date")

    fieldsets = (
        ("Basic Information", {"fields": ("title", "description", "resource_type")}),
        ("Resource Content", {"fields": ("link", "file_upload")}),
        (
            "Video Embedding",
            {
                "fields": ("youtube_embed_id", "vimeo_embed_id", "custom_embed_code"),
                "classes": ("collapse",),
                "description": "For video resources, provide embed information",
            },
        ),
        (
            "Visual Content",
            {"fields": ("thumbnail", "preview_image"), "classes": ("collapse",)},
        ),
        (
            "Categorization",
            {
                "fields": ("categories", "technologies"),
            },
        ),
        (
            "Metadata",
            {"fields": ("author", "publication_date"), "classes": ("collapse",)},
        ),
        (
            "Management",
            {"fields": ("is_featured", "is_active", "order", "personal_rating")},
        ),
    )

    # Custom actions
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)

    mark_as_featured.short_description = "Mark selected resources as featured"

    def mark_as_unfeatured(self, request, queryset):
        queryset.update(is_featured=False)

    mark_as_unfeatured.short_description = "Remove featured status"

    def mark_as_active(self, request, queryset):
        queryset.update(is_active=True)

    mark_as_active.short_description = "Mark selected resources as active"

    def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False)

    mark_as_inactive.short_description = "Mark selected resources as inactive"

    actions = [
        "mark_as_featured",
        "mark_as_unfeatured",
        "mark_as_active",
        "mark_as_inactive",
    ]


@admin.register(ResourceView)
class ResourceViewAdmin(admin.ModelAdmin):
    """Admin for resource view analytics."""

    list_display = ("resource", "viewed_date", "ip_address")
    list_filter = ("viewed_date", "resource__resource_type")
    search_fields = ("resource__title", "ip_address")
    date_hierarchy = "viewed_date"
    ordering = ("-viewed_date",)

    # Make it read-only since this is analytics data
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# =========================================================================
# PLAYLIST ADMIN
# =========================================================================


class ManualTrackInline(admin.TabularInline):
    """Inline admin for manual tracks."""

    model = ManualTrack
    extra = 0
    fields = (
        "track_number",
        "name",
        "artist",
        "album",
        "duration_formatted",
        "is_active",
    )
    readonly_fields = ("duration_formatted",)
    ordering = ("track_number",)


@admin.register(ManualPlaylist)
class ManualPlaylistAdmin(admin.ModelAdmin):
    """Admin for manual playlists."""

    list_display = ("name", "track_count", "is_public", "is_featured", "created_at")
    list_filter = ("is_public", "is_featured", "created_at")
    search_fields = ("name", "description")
    readonly_fields = (
        "slug",
        "track_count",
        "total_duration",
        "created_at",
        "updated_at",
    )
    inlines = [ManualTrackInline]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "slug", "description", "cover_image")},
        ),
        ("Settings", {"fields": ("is_public", "is_featured")}),
        (
            "Statistics",
            {"fields": ("track_count", "total_duration"), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("manual_tracks")


@admin.register(ManualTrack)
class ManualTrackAdmin(admin.ModelAdmin):
    """Admin for manual tracks."""

    list_display = (
        "name",
        "artist",
        "playlist",
        "track_number",
        "duration_formatted",
        "has_audio_source",
        "is_active",
    )
    list_filter = ("playlist", "is_active", "created_at")
    search_fields = ("name", "artist", "album")
    readonly_fields = (
        "duration_formatted",
        "has_audio_source",
        "primary_audio_source",
        "created_at",
    )

    fieldsets = (
        (
            "Track Information",
            {"fields": ("playlist", "name", "artist", "album", "track_number")},
        ),
        ("Duration", {"fields": ("duration_ms", "duration_formatted")}),
        (
            "Audio Sources",
            {
                "fields": (
                    "audio_file",
                    "youtube_url",
                    "has_audio_source",
                    "primary_audio_source",
                )
            },
        ),
        (
            "External Links",
            {"fields": ("apple_music_url",), "classes": ("collapse",)},
        ),
        ("Settings", {"fields": ("is_active", "created_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("playlist")
