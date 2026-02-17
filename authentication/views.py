from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.views import View
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode, url_has_allowed_host_and_scheme
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

import logging

logger = logging.getLogger(__name__)


def _safe_next_url(request):
    """Validate and return next_url from session, falling back to '/'."""
    next_url = request.session.pop("next_url", "/")
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return next_url
    return "/"


class SignupView(View):
    """Simple signup view with name, email, and password."""

    def get(self, request):
        # Store the redirect URL for after signup
        next_url = request.GET.get("next", "/")
        request.session["next_url"] = next_url
        return render(request, "authentication/user-signup.html")

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True))
    def post(self, request):
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()

        # Basic validation
        if not all([name, email, password]):
            messages.error(request, "All fields are required.")
            return render(request, "authentication/user-signup.html")

        # Validate email format using Django's validator
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return render(request, "authentication/user-signup.html")

        # Validate password using Django's password validators
        try:
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, "authentication/user-signup.html")

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "User with this email already exists.")
            return render(request, "authentication/user-signup.html")

        try:
            # Create user with email as username (ensure consistency)
            user = User.objects.create_user(
                username=email,  # Use email as username for consistency
                email=email,
                password=password,
                first_name=name,
            )

            # Log the user in immediately
            login(request, user)
            messages.success(
                request, f"Welcome {name}! I'm thrilled to have you join me here."
            )

            # Redirect to the original page or home (safe redirect)
            return redirect(_safe_next_url(request))

        except Exception:
            logger.exception("Error creating user account for %s", email)
            messages.error(
                request,
                "An error occurred creating your account. Please try again.",
            )
            return render(request, "authentication/user-signup.html")


class LoginView(View):
    """Simple login view with email and password."""

    def get(self, request):
        # Store the redirect URL for after login
        next_url = request.GET.get("next", "/")
        request.session["next_url"] = next_url
        return render(request, "authentication/user-login.html")

    @method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True))
    def post(self, request):
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()

        # Basic validation
        if not all([email, password]):
            messages.error(request, "Both email and password are required.")
            return render(request, "authentication/user-login.html")

        # Try to find user by email first
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return render(request, "authentication/user-login.html")

        # Authenticate user using the actual username
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(
                    request, f"Welcome back {user.first_name or user.username}!"
                )

                # Redirect to the original page or home (safe redirect)
                return redirect(_safe_next_url(request))
            else:
                messages.error(
                    request,
                    "Your account is not active. Please reach out to me directly for assistance.",
                )
                return render(request, "authentication/user-login.html")
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, "authentication/user-login.html")


class ForgotPasswordView(View):
    """Handle forgot password requests."""

    def get(self, request):
        return render(request, "authentication/password-forgot.html")

    @method_decorator(ratelimit(key="ip", rate="3/m", method="POST", block=True))
    def post(self, request):
        email = request.POST.get("email", "").strip().lower()

        if not email:
            messages.error(request, "Email address is required.")
            return render(request, "authentication/password-forgot.html")

        try:
            user = User.objects.get(email=email)

            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Get current site
            current_site = get_current_site(request)

            # Create reset link
            reset_link = request.build_absolute_uri(
                reverse(
                    "authentication:reset_password", kwargs={"uidb64": uid, "token": token}
                )
            )

            # Log reset link in development only
            if settings.DEBUG:
                logger.debug("Password reset link for %s: %s", email, reset_link)

            # Prepare email context
            context = {
                "user": user,
                "reset_link": reset_link,
                "site_name": current_site.name,
                "domain": current_site.domain,
            }

            # Try to send email, but don't fail if email is not configured
            try:
                # Render email template
                subject = f"Password Reset - {current_site.name}"
                html_message = render_to_string("emails/password_reset.html", context)
                plain_message = render_to_string("emails/password_reset.txt", context)

                # Send email
                send_mail(
                    subject=subject,
                    message=plain_message,
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                logger.info("Password reset email sent to %s", email)
            except Exception as email_error:
                logger.error("Failed to send email to %s: %s", email, email_error)
                # Continue anyway - user can still use the printed link in development

            messages.success(
                request,
                "If an account with this email exists, you'll receive a password reset link shortly.",
            )
            return redirect("authentication:login")

        except User.DoesNotExist:
            # Don't reveal that the user doesn't exist for security
            messages.success(
                request,
                "If an account with this email exists, I'll send you a password reset link shortly.",
            )
            return redirect("authentication:login")
        except Exception as e:
            logger.exception("Password reset error")
            messages.error(
                request,
                "I encountered an error processing your password reset request. Please try again later.",
            )
            return render(request, "authentication/password-forgot.html")


class ResetPasswordView(View):
    """Handle password reset with token verification."""

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

            if default_token_generator.check_token(user, token):
                # Token is valid
                context = {
                    "uidb64": uidb64,
                    "token": token,
                    "user": user,
                }
                return render(request, "authentication/password-reset.html", context)
            else:
                messages.error(request, "Invalid or expired reset link.")
                return redirect("authentication:forgot_password")

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, "Invalid reset link.")
            return redirect("authentication:forgot_password")

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

            if not default_token_generator.check_token(user, token):
                messages.error(request, "Invalid or expired reset link.")
                return redirect("authentication:forgot_password")

            password = request.POST.get("password", "").strip()
            confirm_password = request.POST.get("confirm_password", "").strip()

            # Validation
            if not password:
                messages.error(request, "Password is required.")
                context = {"uidb64": uidb64, "token": token, "user": user}
                return render(request, "authentication/password-reset.html", context)

            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                context = {"uidb64": uidb64, "token": token, "user": user}
                return render(request, "authentication/password-reset.html", context)

            # Validate password using Django's password validators
            try:
                validate_password(password, user=user)
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
                context = {"uidb64": uidb64, "token": token, "user": user}
                return render(request, "authentication/password-reset.html", context)

            # Update password
            user.set_password(password)
            user.save()

            messages.success(
                request,
                "Your password has been reset successfully. You can now sign in.",
            )
            return redirect("authentication:login")

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, "Invalid reset link.")
            return redirect("authentication:forgot_password")


class LogoutView(View):
    """Handle user logout. POST only to prevent CSRF-via-GET."""

    def get(self, request):
        # Show a confirmation page instead of logging out via GET
        return render(request, "authentication/user-login.html")

    @method_decorator(require_POST)
    def post(self, request):
        logout(request)
        messages.success(request, "You have been successfully logged out.")
        return redirect("/")  # Redirect to home page
