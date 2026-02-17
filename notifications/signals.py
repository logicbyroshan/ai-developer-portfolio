from django.db.models.signals import post_save
from django.dispatch import receiver
from portfolio.models import ContactSubmission
from .models import ContactNotification
from .services import EmailNotificationService
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ContactSubmission)
def handle_contact_submission(sender, instance, created, **kwargs):
    """
    Signal handler to automatically process new contact form submissions.
    Creates notification record and triggers email notifications.
    """
    logger.debug("Notification signal triggered: created=%s, contact_id=%s", created, instance.id)

    if created:  # Only process newly created submissions
        try:
            # Create notification record
            notification = ContactNotification.objects.create(
                contact_submission=instance,
                status=ContactNotification.NotificationStatus.PENDING,
            )

            logger.info("Created notification record %s for contact submission %s", notification.id, instance.id)

            # Initialize email service
            email_service = EmailNotificationService()

            # Send admin notification
            admin_success = email_service.send_admin_notification(
                instance, notification
            )

            # Send thank you notification to user
            thankyou_success = email_service.send_thankyou_notification(
                instance, notification
            )

            # Update notification status based on email results
            if admin_success and thankyou_success:
                notification.status = ContactNotification.NotificationStatus.COMPLETED
                notification.save()
                logger.info("All notifications completed for contact submission %s", instance.id)
            elif admin_success:
                logger.warning("Admin notified but thank you email failed for submission %s", instance.id)
            else:
                notification.status = ContactNotification.NotificationStatus.FAILED
                notification.save()
                logger.error("Failed to send admin notification for contact submission %s", instance.id)

        except Exception as e:
            logger.exception("Error processing contact submission %s", instance.id)
            # Try to update notification status if it exists
            try:
                notification = ContactNotification.objects.get(
                    contact_submission=instance
                )
                notification.status = ContactNotification.NotificationStatus.FAILED
                notification.admin_email_error = str(e)
                notification.save()
            except ContactNotification.DoesNotExist:
                pass
