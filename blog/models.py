from django.db import models
from django.utils.text import slugify
from tinymce.models import HTMLField
from portfolio.models import Category
from roshan.models import AboutMeConfiguration
from django.core.exceptions import ValidationError
import nh3
import math
import re
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


def sanitize_html(value):
    if value:
        return nh3.clean(
            value, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES
        )
    return value


class Blog(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, editable=False)
    summary = models.TextField(help_text="A short excerpt for the blog list page.")
    content = HTMLField()
    reading_time = models.PositiveIntegerField(default=0)
    cover_image = models.FileField(
        upload_to="blog_covers/",
        validators=[validate_image_file],
        help_text="Upload blog cover image (supports JPG, PNG, WebP, SVG, etc.)",
    )
    categories = models.ManyToManyField(
        Category, limit_choices_to={"category_type": Category.CategoryType.BLOG}
    )
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_date"]

    def calculate_reading_time(self):
        """Estimate reading time based on word count (avg: 200 words/minute)."""
        # Remove HTML tags from TinyMCE content
        text = re.sub(r"<[^>]+>", "", self.content)
        word_count = len(text.split())
        minutes = math.ceil(word_count / 200)
        return minutes if minutes > 0 else 1

    def save(self, *args, **kwargs):
        if not self.slug or self.slug != slugify(self.title):
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Blog.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        self.summary = sanitize_html(self.summary)
        self.content = sanitize_html(self.content)
        # Calculate reading time automatically
        self.reading_time = self.calculate_reading_time()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def author_name(self):
        """Get author name from SiteConfiguration."""
        try:
            from portfolio.models import SiteConfiguration

            site_config = SiteConfiguration.objects.first()
            return site_config.hero_name if site_config else "Roshan Damor"
        except Exception:
            return "Roshan Damor"

    @property
    def author_avatar(self):
        """Get author avatar from AboutMeConfiguration."""
        try:
            about_config = AboutMeConfiguration.objects.first()
            return (
                about_config.profile_image
                if about_config and about_config.profile_image
                else None
            )
        except AboutMeConfiguration.DoesNotExist:
            return None


class Comment(models.Model):
    post = models.ForeignKey(Blog, related_name="comments", on_delete=models.CASCADE)
    author_name = models.CharField(max_length=100)
    body = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["created_date"]

    def __str__(self):
        return f"Comment by {self.author_name} on {self.post.title}"

    @property
    def total_likes(self):
        """Get total number of likes for this comment."""
        return self.user_likes.count()

    def is_liked_by_user(self, user):
        """Check if a specific user has liked this comment."""
        if user.is_authenticated:
            return self.user_likes.filter(user=user).exists()
        return False


class CommentLike(models.Model):
    """Model to track individual user likes on blog comments."""

    comment = models.ForeignKey(
        Comment, related_name="user_likes", on_delete=models.CASCADE
    )
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("comment", "user")  # Prevent duplicate likes
        verbose_name = "Comment Like"
        verbose_name_plural = "Comment Likes"

    def __str__(self):
        return f"{self.user.username} likes comment on {self.comment.post.title}"
