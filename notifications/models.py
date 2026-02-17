from django.db import models
from django.utils import timezone
from django.conf import settings

class ContactNotification(models.Model):
    """
    Model to track contact form submission notifications
    """
    class NotificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT_TO_ADMIN = 'sent_admin', 'Sent to Admin'
        THANKYOU_SENT = 'thankyou_sent', 'Thank You Sent'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    # Contact submission details
    contact_submission = models.OneToOneField(
        'portfolio.ContactSubmission',
        on_delete=models.CASCADE,
        related_name='notification'
    )
    
    # Notification tracking
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
        db_index=True,
    )
    
    # Admin notification tracking
    admin_email_sent = models.BooleanField(default=False)
    admin_email_sent_at = models.DateTimeField(null=True, blank=True)
    admin_email_error = models.TextField(null=True, blank=True)
    
    # User thank you tracking
    thankyou_email_sent = models.BooleanField(default=False)
    thankyou_email_sent_at = models.DateTimeField(null=True, blank=True)
    thankyou_email_error = models.TextField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Notification'
        verbose_name_plural = 'Contact Notifications'
    
    def __str__(self):
        return f"Notification for {self.contact_submission.name} - {self.status}"
    
    def mark_admin_email_sent(self, error=None):
        """Mark admin email as sent or failed"""
        self.admin_email_sent = error is None
        self.admin_email_sent_at = timezone.now()
        if error:
            self.admin_email_error = str(error)
            self.status = self.NotificationStatus.FAILED
        else:
            self.admin_email_error = None
            self.status = self.NotificationStatus.SENT_TO_ADMIN
        self.save()
    
    def mark_thankyou_email_sent(self, error=None):
        """Mark thank you email as sent or failed"""
        self.thankyou_email_sent = error is None
        self.thankyou_email_sent_at = timezone.now()
        if error:
            self.thankyou_email_error = str(error)
            if self.status != self.NotificationStatus.FAILED:
                self.status = self.NotificationStatus.FAILED
        else:
            self.thankyou_email_error = None
            # Mark as completed if both emails sent successfully
            if self.admin_email_sent:
                self.status = self.NotificationStatus.COMPLETED
                # Mark original contact submission as read
                self.contact_submission.is_read = True
                self.contact_submission.save()
            else:
                self.status = self.NotificationStatus.THANKYOU_SENT
        self.save()

class EmailTemplate(models.Model):
    """
    Model to store email templates for different notification types
    """
    class TemplateType(models.TextChoices):
        ADMIN_NOTIFICATION = 'admin_notification', 'Admin Notification'
        USER_THANKYOU = 'user_thankyou', 'User Thank You'
    
    name = models.CharField(max_length=100, unique=True)
    template_type = models.CharField(
        max_length=20,
        choices=TemplateType.choices
    )
    subject = models.CharField(max_length=200)
    html_content = models.TextField(
        help_text="HTML email content. Use {{variable}} for dynamic content."
    )
    text_content = models.TextField(
        help_text="Plain text email content. Use {{variable}} for dynamic content."
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['template_type', 'name']
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

class NotificationSettings(models.Model):
    """
    Model to store notification settings (singleton pattern)
    """
    # Admin notification settings
    admin_email = models.EmailField(
        default='contact@roshandamor.me',
        help_text="Email address to receive contact form notifications"
    )
    admin_notification_enabled = models.BooleanField(
        default=True,
        help_text="Enable/disable admin email notifications"
    )
    
    # User thank you settings
    thankyou_notification_enabled = models.BooleanField(
        default=True,
        help_text="Enable/disable thank you emails to users"
    )
    auto_mark_as_read = models.BooleanField(
        default=True,
        help_text="Automatically mark contact submissions as read after successful notification"
    )
    
    # Email settings
    from_email = models.EmailField(
        default='noreply@roshandamor.me',
        help_text="From email address for outgoing notifications"
    )
    reply_to_email = models.EmailField(
        default='contact@roshandamor.me',
        help_text="Reply-to email address for user notifications"
    )
    
    # Notification delays (in seconds)
    admin_notification_delay = models.PositiveIntegerField(
        default=0,
        help_text="Delay before sending admin notification (seconds)"
    )
    thankyou_notification_delay = models.PositiveIntegerField(
        default=30,
        help_text="Delay before sending thank you email (seconds)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Settings'
        verbose_name_plural = 'Notification Settings'
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)"""
        if not self.pk and NotificationSettings.objects.exists():
            # If this is a new instance and one already exists, update the existing one
            existing = NotificationSettings.objects.first()
            existing.admin_email = self.admin_email
            existing.admin_notification_enabled = self.admin_notification_enabled
            existing.thankyou_notification_enabled = self.thankyou_notification_enabled
            existing.auto_mark_as_read = self.auto_mark_as_read
            existing.from_email = self.from_email
            existing.reply_to_email = self.reply_to_email
            existing.admin_notification_delay = self.admin_notification_delay
            existing.thankyou_notification_delay = self.thankyou_notification_delay
            existing.save()
            return existing
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get the notification settings instance"""
        settings, created = cls.objects.get_or_create(
            id=1,
            defaults={
                'admin_email': 'contact@roshandamor.me',
                'from_email': 'noreply@roshandamor.me',
                'reply_to_email': 'contact@roshandamor.me',
            }
        )
        return settings
    
    def __str__(self):
        return "Notification Settings"
