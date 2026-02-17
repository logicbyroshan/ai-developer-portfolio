"""
Test utilities and helper functions.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import tempfile
import io


class BaseTestCase(TestCase):
    """Base test case with common setup and utilities."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )

    def create_test_image(self, filename="test.jpg", size=(100, 100), format="JPEG"):
        """Create a test image file for upload testing."""
        image = Image.new("RGB", size, color="red")
        temp_file = io.BytesIO()
        image.save(temp_file, format=format)
        temp_file.seek(0)
        return SimpleUploadedFile(
            filename, temp_file.getvalue(), content_type=f"image/{format.lower()}"
        )

    def create_test_file(self, filename="test.txt", content=b"test content"):
        """Create a test file for upload testing."""
        return SimpleUploadedFile(filename, content)

    def login_user(self, user=None):
        """Log in a user for testing authenticated views."""
        if user is None:
            user = self.user
        self.client.force_login(user)
        return user

    def login_admin(self):
        """Log in admin user for testing admin views."""
        return self.login_user(self.admin_user)

    def assertContainsText(self, response, text):
        """Assert that response contains specific text."""
        self.assertContains(response, text)

    def assertNotContainsText(self, response, text):
        """Assert that response does not contain specific text."""
        self.assertNotContains(response, text)

    def assertRedirectsToLogin(self, response):
        """Assert that response redirects to login page."""
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))


def skip_if_no_db(test_func):
    """Decorator to skip tests if database is not available."""

    def wrapper(*args, **kwargs):
        try:
            return test_func(*args, **kwargs)
        except Exception as e:
            if "database" in str(e).lower():
                import unittest

                raise unittest.SkipTest(f"Database not available: {e}")
            raise

    return wrapper


class MockAPIResponse:
    """Mock API response for testing external API calls."""

    def __init__(self, json_data=None, status_code=200):
        self.json_data = json_data or {}
        self.status_code = status_code

    def json(self):
        return self.json_data

    @property
    def text(self):
        return str(self.json_data)


def create_mock_gemini_response():
    """Create a mock Gemini API response."""
    return MockAPIResponse(
        {
            "candidates": [
                {"content": {"parts": [{"text": "This is a test AI response."}]}}
            ]
        }
    )
