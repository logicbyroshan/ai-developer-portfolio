from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import Blog, Comment, CommentLike
from portfolio.models import Category


class BlogListView(ListView):
    """View for the main blog list page with filtering and pagination."""

    model = Blog
    template_name = "blog-list.html"
    context_object_name = "blogs"
    paginate_by = 6

    def get_queryset(self):
        queryset = super().get_queryset()
        category_slug = self.request.GET.get("category")
        if category_slug and category_slug != "all":
            queryset = queryset.filter(
                categories__slug=category_slug, categories__category_type="BLG"
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
            category_type=Category.CategoryType.BLOG
        )
        return context


class BlogDetailView(DetailView):
    """Handles GET for viewing and POST for commenting."""

    model = Blog
    template_name = "blog-detail.html"
    context_object_name = "blog"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object  # Already fetched by DetailView
        context["comments"] = post.comments.filter(is_approved=True)

        # Add user's liked comments for proper state management
        if self.request.user.is_authenticated:
            user_liked_comments = CommentLike.objects.filter(
                user=self.request.user, comment__in=context["comments"]
            ).values_list("comment_id", flat=True)
            context["user_liked_comments"] = list(user_liked_comments)
        else:
            context["user_liked_comments"] = []

        post_categories = post.categories.all()
        context["suggested_posts"] = (
            Blog.objects.filter(categories__in=post_categories)
            .exclude(pk=post.pk)
            .distinct()
            .order_by("-created_date")[:2]
        )
        return context

    def post(self, request, *args, **kwargs):
        post = self.get_object()

        # Check if user is authenticated
        if not request.user.is_authenticated:
            login_url = (
                reverse("authentication:login")
                + f'?next={reverse("blog:blog_detail", kwargs={"slug": post.slug})}%23comments'
            )
            return HttpResponseRedirect(login_url)

        body = request.POST.get("body")

        redirect_url = (
            reverse("blog:blog_detail", kwargs={"slug": post.slug}) + "#comments"
        )
        response = HttpResponseRedirect(redirect_url)

        if body:
            if len(body) > 5000:
                messages.error(request, "Comment is too long. Maximum 5000 characters.")
                return response
            # Create comment with authenticated user's name
            author_name = request.user.first_name or request.user.username
            Comment.objects.create(post=post, author_name=author_name, body=body)
            messages.success(
                request, "Your comment has been posted and is awaiting approval."
            )
        else:
            messages.error(request, "Please enter your comment.")

        return response


@login_required
@require_POST
def toggle_comment_like(request, comment_id):
    """AJAX view to toggle like/unlike for blog comments."""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse(
            {"success": False, "error": "Authentication required", "redirect": True},
            status=401,
        )

    try:
        comment = get_object_or_404(Comment, id=comment_id)
        like, created = CommentLike.objects.get_or_create(
            comment=comment, user=request.user
        )

        if not created:
            # Unlike - delete the like
            like.delete()
            liked = False
        else:
            # Like - like object was created
            liked = True

        return JsonResponse(
            {"success": True, "liked": liked, "total_likes": comment.total_likes}
        )

    except Comment.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Comment not found"}, status=404
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
