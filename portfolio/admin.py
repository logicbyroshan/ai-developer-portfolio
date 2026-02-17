import csv
from django.http import HttpResponse
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count
from .models import (
    SiteConfiguration,
    Technology,
    Category,
    Project,
    ProjectImage,
    Experience,
    FAQ,
    Skill,
    Achievement,
    Resume,
    VideoResume,
    NewsletterSubscriber,
    ContactSubmission,
)

# =========================================================================
# CUSTOM ADMIN MIXIN
# =========================================================================


class BaseModelAdmin(admin.ModelAdmin):
    """Base admin class with common configurations"""

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Add CSS classes to form fields
        for field_name, field in form.base_fields.items():
            if hasattr(field.widget, "attrs"):
                field.widget.attrs.update({"class": "form-control"})
        return form


# =========================================================================
# INLINES
# =========================================================================


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ("image", "caption", "image_preview")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        try:
            if obj.image and hasattr(obj.image, 'url'):
                return format_html(
                    '<img src="{}" style="width: 80px; height: 60px; object-fit: cover; border-radius: 4px;">',
                    obj.image.url,
                )
        except (ValueError, AttributeError, OSError):
            pass
        return "No image"

    image_preview.short_description = "Preview"


# =========================================================================
# MODEL ADMINS
# =========================================================================


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(BaseModelAdmin):
    """Enhanced admin for Site Configuration"""

    fieldsets = (
        ("🏠 Hero Section", {"fields": ("hero_name",), "classes": ("wide",)}),
        (
            "📊 Hero Stats",
            {
                "fields": (
                    "hero_leetcode_rating",
                    "hero_opensource_contributions",
                    "hero_hackathons_count",
                ),
                "classes": ("wide",),
            },
        ),
        (
            "🌐 Social Media Links",
            {
                "fields": (
                    "twitter_url",
                    "github_url",
                    "linkedin_url",
                    "youtube_url",
                    "instagram_url",
                    "facebook_url",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "📞 Contact Information",
            {"fields": ("email", "phone", "location"), "classes": ("wide",)},
        ),
    )

    def has_add_permission(self, request):
        # Only allow one site configuration
        return not SiteConfiguration.objects.exists()


@admin.register(Resume)
class ResumeAdmin(BaseModelAdmin):
    list_display = ("title", "last_updated", "preview_thumbnail")
    readonly_fields = ("preview_thumbnail",)

    def preview_thumbnail(self, obj):
        try:
            if obj.preview_image and hasattr(obj.preview_image, 'url'):
                return format_html(
                    '<img src="{}" style="width: 100px; height: auto; border-radius: 5px;">',
                    obj.preview_image.url,
                )
        except (ValueError, AttributeError, OSError):
            pass
        return "No preview"

    preview_thumbnail.short_description = "Preview"


@admin.register(VideoResume)
class VideoResumeAdmin(BaseModelAdmin):
    def has_add_permission(self, request):
        # Only allow one video resume
        return not VideoResume.objects.exists()


@admin.register(Technology)
class TechnologyAdmin(BaseModelAdmin):
    list_display = ("name", "category", "icon_preview", "project_count")
    list_filter = ("category",)
    search_fields = ("name",)
    readonly_fields = ("icon_preview",)

    def icon_preview(self, obj):
        try:
            if obj.icon and hasattr(obj.icon, 'url'):
                return format_html(
                    '<img src="{}" style="width: 32px; height: 32px; object-fit: cover;">',
                    obj.icon.url,
                )
        except (ValueError, AttributeError, OSError):
            pass
        return "No icon"

    icon_preview.short_description = "Icon"

    def project_count(self, obj):
        count = obj.projects.count()
        return format_html(
            '<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            count,
        )

    project_count.short_description = "Projects"


@admin.register(Category)
class CategoryAdmin(BaseModelAdmin):
    list_display = ("name", "category_type", "colored_type")
    list_filter = ("category_type",)
    search_fields = ("name",)

    def colored_type(self, obj):
        colors = {
            "PRJ": "#007bff",  # Blue for projects
            "BLG": "#28a745",  # Green for blogs
            "SKL": "#ffc107",  # Yellow for skills
            "ACH": "#dc3545",  # Red for achievements
        }
        color = colors.get(obj.category_type, "#6c757d")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_category_type_display(),
        )

    colored_type.short_description = "Type"


@admin.register(Project)
class ProjectAdmin(BaseModelAdmin):
    inlines = [ProjectImageInline]
    list_display = (
        "title",
        "created_date",
        "cover_preview",
        "tech_count",
        "has_github",
        "has_live_url",
        "has_youtube",
    )
    list_filter = ("categories", "technologies", "created_date")
    search_fields = ("title", "summary")
    filter_horizontal = ("technologies", "categories")
    readonly_fields = ("cover_preview", "slug")
    date_hierarchy = "created_date"

    fieldsets = (
        (
            "📝 Basic Information",
            {"fields": ("title", "slug", "summary", "content"), "classes": ("wide",)},
        ),
        (
            "🖼️ Media",
            {
                "fields": ("cover_image", "cover_preview", "youtube_embed_code"),
                "classes": ("wide",),
            },
        ),
        (
            "🏷️ Categorization",
            {"fields": ("technologies", "categories"), "classes": ("wide",)},
        ),
        ("🔗 Links", {"fields": ("github_url", "live_url"), "classes": ("wide",)}),
    )

    def cover_preview(self, obj):
        try:
            if obj.cover_image and hasattr(obj.cover_image, 'url'):
                return format_html(
                    '<img src="{}" style="width: 100px; height: 60px; object-fit: cover; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">',
                    obj.cover_image.url,
                )
        except (ValueError, AttributeError, OSError):
            pass
        return "No cover image"

    cover_preview.short_description = "Cover Preview"

    def tech_count(self, obj):
        count = obj.technologies.count()
        return format_html(
            '<span style="background: #17a2b8; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{} tech{}</span>',
            count,
            "s" if count != 1 else "",
        )

    tech_count.short_description = "Technologies"

    def has_github(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            "#28a745" if obj.github_url else "#dc3545",
            "✓" if obj.github_url else "✗",
        )

    has_github.short_description = "GitHub"

    def has_live_url(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            "#28a745" if obj.live_url else "#dc3545",
            "✓" if obj.live_url else "✗",
        )

    has_live_url.short_description = "Live URL"

    def has_youtube(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            "#28a745" if obj.youtube_embed_code else "#dc3545",
            "✓" if obj.youtube_embed_code else "✗",
        )

    has_youtube.short_description = "Video"


@admin.register(Experience)
class ExperienceAdmin(BaseModelAdmin):
    list_display = (
        "role",
        "company_name",
        "experience_type",
        "duration",
        "start_date",
        "end_date",
    )
    list_filter = ("experience_type", "start_date")
    search_fields = ("role", "company_name", "responsibilities")
    filter_horizontal = ("technologies",)
    date_hierarchy = "start_date"

    def duration(self, obj):
        if obj.end_date:
            duration = obj.end_date - obj.start_date
            years = duration.days // 365
            months = (duration.days % 365) // 30
            if years > 0:
                return f"{years}y {months}m"
            return f"{months}m"
        return "Ongoing"

    duration.short_description = "Duration"


@admin.register(FAQ)
class FAQAdmin(BaseModelAdmin):
    list_display = ("question", "order", "answer_preview")
    list_editable = ("order",)
    ordering = ("order",)

    def answer_preview(self, obj):
        return obj.answer[:100] + "..." if len(obj.answer) > 100 else obj.answer

    answer_preview.short_description = "Answer Preview"


@admin.register(Skill)
class SkillAdmin(BaseModelAdmin):
    list_display = (
        "title",
        "category_badge",
        "proficiency_badge",
        "experience_years",
        "featured_status",
        "tech_count",
        "order",
        "is_featured",
    )
    list_filter = ("category", "proficiency_level", "is_featured")
    search_fields = ("title", "learning_journey")
    filter_horizontal = ("technologies",)
    list_editable = ("order", "is_featured")
    readonly_fields = ("slug",)

    def category_badge(self, obj):
        colors = {
            "languages_frameworks": "#007bff",
            "backend_database": "#28a745",
            "tools_platforms": "#ffc107",
            "soft_skills": "#6f42c1",
        }
        color = colors.get(obj.category, "#6c757d")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_category_display(),
        )

    category_badge.short_description = "Category"

    def proficiency_badge(self, obj):
        colors = {
            "beginner": "#ffc107",
            "intermediate": "#17a2b8",
            "advanced": "#28a745",
            "expert": "#dc3545",
        }
        color = colors.get(obj.proficiency_level, "#6c757d")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_proficiency_level_display(),
        )

    proficiency_badge.short_description = "Proficiency"

    def experience_years(self, obj):
        return f"{obj.years_of_experience} year{'s' if obj.years_of_experience != 1 else ''}"

    experience_years.short_description = "Experience"

    def featured_status(self, obj):
        return format_html(
            '<span style="color: {}; font-size: 16px;">{}</span>',
            "#ffc107" if obj.is_featured else "#6c757d",
            "⭐" if obj.is_featured else "☆",
        )

    featured_status.short_description = "Featured"

    def tech_count(self, obj):
        count = obj.technologies.count()
        return format_html(
            '<span style="background: #17a2b8; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            count,
        )

    tech_count.short_description = "Technologies"


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(BaseModelAdmin):
    list_display = ("email", "subscribed_date", "days_subscribed")
    search_fields = ("email",)
    readonly_fields = ("subscribed_date", "days_subscribed")
    actions = ["export_as_csv"]
    date_hierarchy = "subscribed_date"

    def days_subscribed(self, obj):
        from django.utils import timezone

        days = (timezone.now().date() - obj.subscribed_date.date()).days
        return f"{days} days"

    days_subscribed.short_description = "Subscribed For"

    @admin.action(description="📤 Export selected subscribers as CSV")
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={meta}.csv"
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        return response


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(BaseModelAdmin):
    list_display = (
        "name",
        "email",
        "subject_preview",
        "submitted_date",
        "read_status",
        "urgent_indicator",
        "days_ago",
    )
    list_filter = ("is_read", "is_urgent", "submitted_date")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = (
        "name",
        "email",
        "subject",
        "message",
        "submitted_date",
        "days_ago",
    )
    actions = ["mark_as_read", "mark_as_unread"]
    date_hierarchy = "submitted_date"

    def subject_preview(self, obj):
        return obj.subject[:50] + "..." if len(obj.subject) > 50 else obj.subject

    subject_preview.short_description = "Subject"

    def read_status(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            "#28a745" if obj.is_read else "#dc3545",
            "Read" if obj.is_read else "Unread",
        )

    read_status.short_description = "Status"

    def urgent_indicator(self, obj):
        if obj.is_urgent:
            return format_html(
                '<span style="color: #dc3545; font-size: 16px;">🔴</span>'
            )
        return ""

    urgent_indicator.short_description = "Urgent"

    def days_ago(self, obj):
        from django.utils import timezone

        days = (timezone.now().date() - obj.submitted_date.date()).days
        if days == 0:
            return "Today"
        elif days == 1:
            return "Yesterday"
        else:
            return f"{days} days ago"

    days_ago.short_description = "Received"

    @admin.action(description="✅ Mark selected submissions as read")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="📧 Mark selected submissions as unread")
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)


@admin.register(Achievement)
class AchievementAdmin(BaseModelAdmin):
    list_display = (
        "title",
        "issuing_organization",
        "category_badge",
        "date_issued",
        "has_credential",
        "has_image",
    )
    list_filter = ("category", "date_issued")
    search_fields = ("title", "issuing_organization", "summary")
    readonly_fields = ("image_preview",)
    date_hierarchy = "date_issued"

    fieldsets = (
        (
            "🏆 Achievement Details",
            {
                "fields": (
                    "title",
                    "issuing_organization",
                    "summary",
                    "date_issued",
                    "category",
                ),
                "classes": ("wide",),
            },
        ),
        ("🔗 Verification", {"fields": ("credential_url",), "classes": ("wide",)}),
        ("🖼️ Image", {"fields": ("image", "image_preview"), "classes": ("wide",)}),
    )

    def category_badge(self, obj):
        return format_html(
            '<span style="background: #6f42c1; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            obj.category.name,
        )

    category_badge.short_description = "Category"

    def has_credential(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            "#28a745" if obj.credential_url else "#dc3545",
            "✓" if obj.credential_url else "✗",
        )

    has_credential.short_description = "Credential URL"

    def has_image(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            "#28a745" if obj.image else "#dc3545",
            "✓" if obj.image else "✗",
        )

    has_image.short_description = "Has Image"

    def image_preview(self, obj):
        try:
            if obj.image and hasattr(obj.image, 'url'):
                return format_html(
                    '<img src="{}" style="width: 150px; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">',
                    obj.image.url,
                )
        except (ValueError, AttributeError, OSError):
            pass
        return "No image uploaded"

    image_preview.short_description = "Image Preview"
