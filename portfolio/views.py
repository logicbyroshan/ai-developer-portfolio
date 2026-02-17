from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

# Import all models from your models.py
from .models import (
    Skill,
    Experience,
    Project,
    FAQ,
    Category,
    NewsletterSubscriber,
    ProjectComment,
    Achievement,
    SiteConfiguration,
    Resume,
    VideoResume,
    Technology,
    ContactSubmission,
    ProjectCommentLike,
)

# Import all forms from your forms.py
from .forms import ContactForm, NewsletterForm


# =========================================================================
# HOME PAGE VIEW
# =========================================================================
class HomeView(TemplateView):
    """View for the homepage. Gathers context from multiple models."""

    template_name = "portfolio-home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # =================================================================
        # NEW & UPDATED: Skill Categories for Skills Section
        # =================================================================

        # Get skill categories with counts and first few technologies
        skill_categories = []
        for category_code, category_name in Skill.SKILL_CATEGORIES:
            skills_in_category = Skill.objects.filter(category=category_code).order_by(
                "order"
            )
            if skills_in_category.exists():
                # Get the main/featured skill for this category or first skill
                main_skill = (
                    skills_in_category.filter(is_featured=True).first()
                    or skills_in_category.first()
                )

                # Get technologies from skills in this category
                technologies = Technology.objects.filter(
                    skill__category=category_code
                ).distinct()[
                    :6
                ]  # Limit to 6 technologies per category

                skill_categories.append(
                    {
                        "code": category_code,
                        "name": category_name,
                        "skills_count": skills_in_category.count(),
                        "technologies": technologies,
                        "main_skill": main_skill,  # This will be used for linking to detail page
                    }
                )

        context["skill_categories"] = skill_categories

        # =================================================================
        # Fetch data for the rest of the homepage sections
        # =================================================================
        context["skills"] = Skill.objects.all()
        context["experiences"] = Experience.objects.order_by("-start_date")[:3]
        context["projects"] = Project.objects.order_by("-created_date")[:3]
        context["achievements"] = Achievement.objects.order_by("-date_issued")[:3]
        from blog.models import Blog

        context["blogs"] = Blog.objects.order_by("-created_date")[:3]
        # FAQ section moved to about page

        return context


# =========================================================================
# PROJECT VIEWS
# =========================================================================
class ProjectListView(ListView):
    """View for the main projects list page with filtering and pagination."""

    model = Project
    template_name = "projects-list.html"
    context_object_name = "projects"
    paginate_by = 6

    def get_queryset(self):
        queryset = super().get_queryset()
        category_slug = self.request.GET.get("category")
        if category_slug and category_slug != "all":
            queryset = queryset.filter(
                categories__slug=category_slug, categories__category_type="PRO"
            )

        sort_by = self.request.GET.get("sort", "newest")
        if sort_by == "oldest":
            queryset = queryset.order_by("created_date")
        else:
            queryset = queryset.order_by("-created_date")

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(
            category_type=Category.CategoryType.PROJECT
        )
        return context


class ProjectDetailView(DetailView):
    """View for a single project detail page with comment functionality."""

    model = Project
    template_name = "project-detail.html"
    context_object_name = "project"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object  # Already fetched by DetailView

        # Get initial 5 comments for display
        initial_comments = project.comments.filter(is_approved=True).order_by(
            "-created_date"
        )[:5]
        context["comments"] = initial_comments

        # Add user's liked comments for proper state management
        if self.request.user.is_authenticated:
            user_liked_comments = ProjectCommentLike.objects.filter(
                user=self.request.user, comment__in=initial_comments
            ).values_list("comment_id", flat=True)
            context["user_liked_comments"] = list(user_liked_comments)
        else:
            context["user_liked_comments"] = []

        # Check if there are more comments beyond the initial 5
        total_comments_count = project.comments.filter(is_approved=True).count()
        context["has_more_comments"] = total_comments_count > 5
        context["total_comments"] = total_comments_count

        return context

    def post(self, request, *args, **kwargs):
        project = self.get_object()

        # Check if user is authenticated
        if not request.user.is_authenticated:
            login_url = (
                reverse("authentication:login")
                + f'?next={reverse("portfolio:project_detail", kwargs={"slug": project.slug})}%23comments'
            )
            return HttpResponseRedirect(login_url)

        body = request.POST.get("body")

        redirect_url = (
            reverse("portfolio:project_detail", kwargs={"slug": project.slug})
            + "#comments"
        )
        response = HttpResponseRedirect(redirect_url)

        if body:
            if len(body) > 5000:
                messages.error(request, "Comment is too long. Maximum 5000 characters.")
                return response
            # Create comment with authenticated user's name
            author_name = request.user.first_name or request.user.username
            ProjectComment.objects.create(
                project=project, author_name=author_name, body=body
            )
            messages.success(
                request, "Your comment has been posted and is awaiting approval."
            )
        else:
            messages.error(request, "Please enter your comment.")

        return response


def load_more_project_comments(request, slug):
    """AJAX view to load more project comments."""
    if request.method == "GET":
        project = get_object_or_404(Project, slug=slug)
        offset = int(request.GET.get("offset", 0))
        offset = max(0, offset)  # Prevent negative offsets

        total_comments = project.comments.filter(is_approved=True).count()
        offset = min(offset, total_comments)  # Cap offset at total count

        # Load 10 comments starting from the offset
        comments = project.comments.filter(is_approved=True).order_by("-created_date")[
            offset : offset + 10
        ]

        # Get user's liked comments if authenticated
        user_liked_comments = []
        if request.user.is_authenticated:
            user_liked_comments = ProjectCommentLike.objects.filter(
                user=request.user, comment__in=comments
            ).values_list("comment_id", flat=True)
            user_liked_comments = list(user_liked_comments)

        comments_data = []
        for comment in comments:
            comments_data.append(
                {
                    "id": comment.id,
                    "author_name": comment.author_name,
                    "body": comment.body,
                    "likes": comment.total_likes,  # Use the new property
                    "is_liked": comment.id in user_liked_comments,
                    "created_at": comment.created_date.strftime(
                        "%B %d, %Y at %I:%M %p"
                    ),
                }
            )

        return JsonResponse(
            {"comments": comments_data, "has_more": total_comments > (offset + 10)}
        )

    return JsonResponse({"error": "Invalid request"}, status=400)


# =========================================================================
# EXPERIENCE VIEWS
# =========================================================================
class ExperienceListView(ListView):
    """View for the main experience list page."""

    model = Experience
    template_name = "experience-list.html"
    context_object_name = "experiences"
    paginate_by = 4

    def get_queryset(self):
        queryset = super().get_queryset()
        exp_type = self.request.GET.get("category")
        if exp_type and exp_type != "all":
            queryset = queryset.filter(experience_type=exp_type)

        sort_by = self.request.GET.get("sort", "newest")
        if sort_by == "oldest":
            queryset = queryset.order_by("start_date")
        else:
            queryset = queryset.order_by("-start_date")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["experience_types"] = Category.objects.filter(
            category_type=Category.CategoryType.EXPERIENCE
        )
        return context


class ExperienceDetailView(DetailView):
    """View for a single experience dtl page."""

    model = Experience
    template_name = "experience-detail.html"
    context_object_name = "experience"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experience = self.get_object()
        # Get related experiences (excluding current one, limit to 3)
        context["related_experiences"] = Experience.objects.exclude(
            id=experience.id
        ).order_by("-start_date")[:3]
        return context


# =========================================================================
# SKILL DETAIL VIEW
# =========================================================================
class SkillDetailView(DetailView):
    """View for a single skill dtl page, showing related projects."""

    model = Skill
    template_name = "skill-detail.html"
    context_object_name = "skill"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        skill = self.get_object()
        skill_technologies = skill.technologies.all()
        context["related_projects"] = (
            Project.objects.filter(technologies__in=skill_technologies)
            .distinct()
            .order_by("-created_date")[:2]
        )
        return context


# =========================================================================
# FORM HANDLING & API-LIKE VIEWS
# =========================================================================
class ContactSubmissionView(View):
    """Handles the submission of the main contact form."""

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True))
    def post(self, request, *args, **kwargs):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            form = ContactForm(request.POST)
            if form.is_valid():
                form.save()
                return JsonResponse(
                    {
                        "status": "success",
                        "message": "Thank you for your message! I'll get back to you soon.",
                    }
                )
            else:
                errors = []
                for field, field_errors in form.errors.items():
                    for error in field_errors:
                        errors.append(f"{field}: {error}")
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Please check the fields: " + ", ".join(errors),
                    },
                    status=400,
                )
        else:
            form = ContactForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(
                    request, "Thank you for your message! I'll get back to you soon."
                )
            else:
                messages.error(
                    request,
                    "There was an error. Please check the fields and try again.",
                )
            return redirect(reverse("portfolio:home") + "#contact")


class NewsletterSubscribeHomeView(View):
    """Handles the submission of the newsletter form on the homepage."""

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True))
    def post(self, request, *args, **kwargs):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            form = NewsletterForm(request.POST)
            if form.is_valid():
                subscriber, created = NewsletterSubscriber.objects.get_or_create(
                    email=form.cleaned_data["email"]
                )
                if created:
                    return JsonResponse(
                        {
                            "status": "success",
                            "message": "Thanks for subscribing! You'll receive updates soon.",
                        }
                    )
                else:
                    return JsonResponse(
                        {"status": "info", "message": "You are already subscribed!"}
                    )
            else:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Please provide a valid email address.",
                    },
                    status=400,
                )
        else:
            form = NewsletterForm(request.POST)
            if form.is_valid():
                subscriber, created = NewsletterSubscriber.objects.get_or_create(
                    email=form.cleaned_data["email"]
                )
                if created:
                    messages.success(request, "Thanks for subscribing!")
                else:
                    messages.info(request, "You are already subscribed!")
            else:
                messages.error(request, "Please provide a valid email address.")
            return redirect(reverse("portfolio:home") + "#newsletter")


class NewsletterSubscribeAjaxView(View):
    """Handles AJAX requests for newsletter subscriptions from the modal."""

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email")
        if not email or "@" not in email or "." not in email:
            return JsonResponse(
                {"success": False, "message": "Please enter a valid email address."},
                status=400,
            )

        subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)

        if created:
            message = "Thank you for subscribing!"
        else:
            message = "You are already subscribed!"

        return JsonResponse({"success": True, "message": message})


class AchievementListView(ListView):
    model = Achievement
    template_name = "achievements-list.html"
    context_object_name = "achievements"
    paginate_by = 6

    def get_queryset(self):
        queryset = super().get_queryset()

        category = self.request.GET.get("category")
        if category and category != "all":
            queryset = queryset.filter(category__id=category)

        sort_by = self.request.GET.get("sort", "newest")
        if sort_by == "oldest":
            queryset = queryset.order_by("date_issued")
        else:
            queryset = queryset.order_by("-date_issued")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["achievement_categories"] = Category.objects.filter(
            category_type=Category.CategoryType.ACHIEVEMENT
        )
        return context


# =========================================================================
# COMMENT LIKE VIEWS
# =========================================================================


@login_required
@require_POST
def toggle_project_comment_like(request, comment_id):
    """AJAX view to toggle like/unlike for project comments."""
    try:
        comment = get_object_or_404(ProjectComment, id=comment_id)
        like, created = ProjectCommentLike.objects.get_or_create(
            comment=comment, user=request.user
        )

        if not created:
            like.delete()
            liked = False
        else:
            liked = True

        return JsonResponse(
            {"success": True, "liked": liked, "total_likes": comment.total_likes}
        )

    except ProjectComment.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Comment not found"}, status=404
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ======================= CUSTOM ERROR HANDLERS =======================


def custom_bad_request(request, exception=None):
    """
    Custom 400 Bad Request error handler.
    """
    return render(request, "400.html", status=400)


def custom_permission_denied(request, exception=None):
    """
    Custom 403 Permission Denied error handler.
    """
    return render(request, "403.html", status=403)


def custom_page_not_found(request, exception=None):
    """
    Custom 404 Page Not Found error handler.
    """
    return render(request, "404.html", status=404)


def custom_server_error(request):
    """
    Custom 500 Server Error handler.
    """
    return render(request, "500.html", status=500)
