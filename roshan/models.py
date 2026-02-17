from django.db import models
from django.utils.text import slugify
from tinymce.models import HTMLField
from django.core.exceptions import ValidationError
import nh3
import os

ALLOWED_TAGS = {
    "b", "i", "strong", "em", "u", "a", "br", "p", "ul", "ol", "li", "span",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption", "colgroup", "col",
    "div", "section", "article", "header", "footer", "nav", "aside",
    "img", "figure", "figcaption", "picture", "source",
    "blockquote", "pre", "code", "hr", "sub", "sup", "mark", "del", "ins", "abbr",
    "dl", "dt", "dd", "details", "summary",
    "iframe", "video", "audio",
}
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title", "target", "rel"},
    "img": {"src", "alt", "title", "width", "height", "loading", "style"},
    "iframe": {"src", "width", "height", "frameborder", "allow", "allowfullscreen", "title", "loading", "style"},
    "video": {"src", "controls", "width", "height", "autoplay", "muted", "loop", "poster"},
    "audio": {"src", "controls"},
    "source": {"src", "type", "media"},
    "td": {"colspan", "rowspan", "style"},
    "th": {"colspan", "rowspan", "scope", "style"},
    "col": {"span", "style"},
    "colgroup": {"span"},
    "span": {"style", "class"},
    "div": {"style", "class"},
    "p": {"style", "class"},
    "pre": {"class"},
    "code": {"class"},
    "blockquote": {"cite"},
    "abbr": {"title"},
    "h1": {"style"}, "h2": {"style"}, "h3": {"style"}, "h4": {"style"}, "h5": {"style"}, "h6": {"style"},
    "table": {"style", "class"},
    "figure": {"class"},
}


def sanitize_html(value):
    if value:
        return nh3.clean(
            value, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES
        )
    return value


def validate_image_file(file):
    """
    Validates that the uploaded file is an image with allowed extensions.
    Supports all common image formats including modern ones like WebP.
    """
    valid_extensions = [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".webp",
        ".svg",
        ".tiff",
        ".tif",
        ".ico",
        ".avif",
    ]
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError(
            f"Only image files are allowed. Supported formats: "
            f"{', '.join(valid_extensions).upper().replace('.', '')}"
        )


# =========================================================================
# ABOUT ME PAGE CONFIGURATION MODEL
# =========================================================================


class AboutMeConfiguration(models.Model):
    # --- Page Header ---
    page_title = models.CharField(
        max_length=255, default="A Bit More <span>About Me</span>"
    )
    intro_paragraph = models.TextField(
        default="This is my story, my journey, and what drives me."
    )
    profile_image = models.FileField(
        upload_to="about/",
        blank=True,
        null=True,
        validators=[validate_image_file],
        help_text="Profile image for About Me page (supports all image formats)",
    )
    detailed_description = HTMLField(
        default="""<ul>
            <li><strong>Mission:</strong> To build software that is not only functional but also intuitive and impactful.</li>
            <li><strong>Interests:</strong> Beyond coding, I'm passionate about AI ethics, open-source contribution, and exploring the intersection of technology and art.</li>
        </ul>""",
        help_text="Detailed description with HTML support",
    )

    # --- Personal Information ---
    birthday = models.DateField(
        blank=True,
        null=True,
        help_text="Your birthday (used to calculate age automatically)",
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        default="Bhopal, India",
        help_text="Your current location/address",
    )
    open_to_work = models.BooleanField(
        default=True, help_text="Display 'Open to Work' status badge"
    )

    # --- Social Media Links ---
    github_url = models.URLField(
        blank=True,
        default="https://github.com/logicbyroshan",
        help_text="GitHub profile URL",
    )
    linkedin_url = models.URLField(
        blank=True,
        default="https://www.linkedin.com/in/logicbyroshan",
        help_text="LinkedIn profile URL",
    )
    twitter_url = models.URLField(
        blank=True,
        default="https://x.com/logicbyroshan",
        help_text="Twitter/X profile URL",
    )
    youtube_url = models.URLField(
        blank=True,
        default="https://www.youtube.com/@logicbyroshan",
        help_text="YouTube channel URL",
    )
    instagram_url = models.URLField(
        blank=True,
        default="https://www.instagram.com/logicbyroshan",
        help_text="Instagram profile URL",
    )
    website_url = models.URLField(
        blank=True,
        default="https://www.roshandamor.me",
        help_text="Personal website URL",
    )

    # --- Contact Information ---
    email = models.EmailField(
        blank=True, default="contact@roshandamor.me", help_text="Contact email address"
    )

    # --- Meta Information ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "About Me Configuration"
        verbose_name_plural = "About Me Configuration"

    def __str__(self):
        return "About Me Page Configuration"

    @property
    def age(self):
        """Calculate age from birthday."""
        if self.birthday:
            from datetime import date

            today = date.today()
            return (
                today.year
                - self.birthday.year
                - ((today.month, today.day) < (self.birthday.month, self.birthday.day))
            )
        return None

    def save(self, *args, **kwargs):
        """Ensure only one instance exists."""
        if not self.pk and AboutMeConfiguration.objects.exists():
            # Update existing instance instead of creating new one
            existing = AboutMeConfiguration.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)


# =========================================================================
# RESOURCES PAGE MODELS
# =========================================================================


class ResourcesConfiguration(models.Model):
    # --- Page Header ---
    page_title = HTMLField(default="My Curated <span>Resources</span>")
    intro_paragraph = models.TextField(
        max_length=500,
    )
    resources_description = HTMLField(
        help_text="Additional description content for the resources section", blank=True
    )
    resources_per_page = models.PositiveIntegerField(
        default=12, help_text="Number of resources to display per page"
    )

    # --- Meta Information ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Resources Configuration"
        verbose_name_plural = "Resources Configuration"

    def __str__(self):
        return "Resources Page Configuration"

    def save(self, *args, **kwargs):
        """Ensure only one instance exists."""
        if not self.pk and ResourcesConfiguration.objects.exists():
            # Update existing instance instead of creating new one
            existing = ResourcesConfiguration.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)


class ResourceCategory(models.Model):
    """
    Model for categorizing resources (separate from general categories).
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, editable=False)
    description = HTMLField(
        blank=True,
        help_text="Brief description of this resource category with HTML support",
    )
    icon = models.CharField(
        max_length=50,
        default="fa-solid fa-folder",
        help_text="Font Awesome icon class (e.g., 'fa-solid fa-code')",
    )
    order = models.PositiveIntegerField(
        default=0, help_text="Display order for category filtering"
    )

    class Meta:
        verbose_name_plural = "Resource Categories"
        ordering = ["order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug or self.slug != slugify(self.name):
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while ResourceCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        self.description = sanitize_html(self.description)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Resource(models.Model):
    # --- Resource Type Choices ---
    class ResourceType(models.TextChoices):
        ARTICLE = "ART", "Article"
        VIDEO = "VID", "Video"
        PDF = "PDF", "PDF Document"
        TOOL = "TOL", "Tool/Website"
        COURSE = "CRS", "Course"
        BOOK = "BOK", "Book"
        TUTORIAL = "TUT", "Tutorial"
        DOCUMENTATION = "DOC", "Documentation"
        REPOSITORY = "REP", "Code Repository"
        OTHER = "OTH", "Other"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, editable=False)
    description = HTMLField(
        help_text="Brief description of the resource with HTML support"
    )
    resource_type = models.CharField(
        max_length=3, choices=ResourceType.choices, default=ResourceType.ARTICLE
    )
    link = models.URLField(
        blank=True, null=True, help_text="External link to the resource"
    )
    file_upload = models.FileField(
        upload_to="resources/files/",
        blank=True,
        null=True,
        help_text="Upload file for downloadable resources (PDFs, documents, etc.)",
    )
    youtube_embed_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="YouTube video ID for embedding (e.g., 'dQw4w9WgXcQ')",
    )
    vimeo_embed_id = models.CharField(
        max_length=50, blank=True, help_text="Vimeo video ID for embedding"
    )
    custom_embed_code = HTMLField(
        blank=True, help_text="Custom embed code for other video platforms or widgets"
    )
    thumbnail = models.FileField(
        upload_to="resources/thumbnails/",
        blank=True,
        null=True,
        validators=[validate_image_file],
        help_text="Thumbnail image for the resource (supports all image formats)",
    )
    preview_image = models.FileField(
        upload_to="resources/previews/",
        blank=True,
        null=True,
        validators=[validate_image_file],
        help_text="Preview image for PDFs or other documents (supports all image formats)",
    )
    categories = models.ManyToManyField(
        ResourceCategory, related_name="resources", blank=True
    )
    technologies = models.ManyToManyField(
        "portfolio.Technology",
        related_name="resources",
        blank=True,
        help_text="Related technologies or tech stack",
    )
    author = models.CharField(
        max_length=100,
        blank=True,
        help_text="Original author or creator of the resource",
    )
    publication_date = models.DateField(
        blank=True, null=True, help_text="When the resource was originally published"
    )
    is_featured = models.BooleanField(
        default=False, db_index=True, help_text="Display this resource prominently"
    )
    is_active = models.BooleanField(
        default=True, db_index=True, help_text="Whether this resource should be displayed"
    )
    order = models.PositiveIntegerField(
        default=0, help_text="Display order within category"
    )
    personal_rating = models.PositiveIntegerField(
        default=5,
        choices=[(i, f"{i} Stars") for i in range(1, 6)],
        help_text="Your personal rating of this resource (1-5 stars)",
    )

    # --- Timestamps ---
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-created_date"]
        verbose_name = "Resource"
        verbose_name_plural = "Resources"

    def save(self, *args, **kwargs):
        if not self.slug or self.slug != slugify(self.title):
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Resource.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        self.description = sanitize_html(self.description)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_resource_type_display()})"

    @property
    def has_video_embed(self):
        """Check if resource has any video embed information."""
        return bool(
            self.youtube_embed_id or self.vimeo_embed_id or self.custom_embed_code
        )

    @property
    def embed_url(self):
        """Get the appropriate embed URL based on platform."""
        if self.youtube_embed_id:
            return f"https://www.youtube.com/embed/{self.youtube_embed_id}"
        elif self.vimeo_embed_id:
            return f"https://player.vimeo.com/video/{self.vimeo_embed_id}"
        return None

    @property
    def is_downloadable(self):
        """Check if resource has downloadable content."""
        return bool(self.file_upload)

    @property
    def display_thumbnail(self):
        """Get appropriate thumbnail - uploaded thumbnail, preview image, or default based on type."""
        if self.thumbnail:
            return self.thumbnail.url
        elif self.preview_image:
            return self.preview_image.url
        elif self.youtube_embed_id:
            return (
                f"https://img.youtube.com/vi/{self.youtube_embed_id}/maxresdefault.jpg"
            )
        return None


class ResourceView(models.Model):
    resource = models.ForeignKey(
        Resource, on_delete=models.CASCADE, related_name="views"
    )
    viewed_date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        verbose_name = "Resource View"
        verbose_name_plural = "Resource Views"

    def __str__(self):
        return f"View of {self.resource.title} on {self.viewed_date.date()}"


# =========================================================================
# PLAYLIST MODELS
# =========================================================================


class ManualPlaylist(models.Model):
    """Manually created playlists with custom tracks"""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    description = models.TextField(blank=True, null=True)
    cover_image = models.FileField(
        upload_to="playlists/covers/",
        blank=True,
        null=True,
        validators=[validate_image_file],
        help_text="Cover image for the playlist (supports all image formats)",
    )
    is_public = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Manual Playlist"
        verbose_name_plural = "Manual Playlists"

    def save(self, *args, **kwargs):
        if not self.slug or self.slug != slugify(self.name):
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while ManualPlaylist.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def track_count(self):
        return self.manual_tracks.count()

    @property
    def total_duration(self):
        """Calculate total duration of all tracks"""
        total_ms = sum(
            track.duration_ms for track in self.manual_tracks.all() if track.duration_ms
        )
        if not total_ms:
            return "0:00"

        total_seconds = total_ms // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:00"
        return f"{minutes}:00"


class ManualTrack(models.Model):
    """Individual tracks in manual playlists"""

    playlist = models.ForeignKey(
        ManualPlaylist, related_name="manual_tracks", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    album = models.CharField(max_length=255, blank=True)
    duration_ms = models.IntegerField(default=0, help_text="Duration in milliseconds")
    audio_file = models.FileField(
        upload_to="playlists/tracks/",
        blank=True,
        null=True,
        help_text="Upload audio file (MP3, WAV, etc.)",
    )
    youtube_url = models.URLField(
        blank=True, null=True, help_text="YouTube URL for the track"
    )
    apple_music_url = models.URLField(
        blank=True, null=True, help_text="Apple Music URL for the track"
    )
    track_number = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["track_number", "created_at"]
        verbose_name = "Manual Track"
        verbose_name_plural = "Manual Tracks"

    def __str__(self):
        return f"{self.name} by {self.artist}"

    @property
    def duration_formatted(self):
        """Format duration from milliseconds to MM:SS"""
        if not self.duration_ms:
            return "0:00"

        total_seconds = self.duration_ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"

    @property
    def has_audio_source(self):
        """Check if track has any playable audio source"""
        return bool(self.audio_file or self.youtube_url)

    @property
    def primary_audio_source(self):
        """Get the primary audio source for playback"""
        if self.audio_file:
            return {"type": "file", "url": self.audio_file.url}
        elif self.youtube_url:
            return {"type": "youtube", "url": self.youtube_url}
        return None
