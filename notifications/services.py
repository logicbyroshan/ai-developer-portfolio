from django.conf import settings
from .models import NotificationSettings, EmailTemplate
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """
    Service class to handle email notifications for contact submissions
    """

    def __init__(self):
        self.settings = NotificationSettings.get_settings()

    def send_admin_notification(self, contact_submission, notification):
        """
        Send notification email to admin about new contact submission
        """
        logger.debug("send_admin_notification() called, enabled=%s", self.settings.admin_notification_enabled)

        if not self.settings.admin_notification_enabled:
            logger.info("Admin notifications are disabled")
            return False

        try:
            # Get email template or use default
            template = self._get_template("admin_notification")

            if template:
                subject = template.subject
                html_content = template.html_content
                text_content = template.text_content
                logger.debug("Using custom template: %s", template.name)
            else:
                # Default template
                subject = f"New Contact Form Submission from {contact_submission.name}"
                html_content = self._get_default_admin_html_template()
                text_content = self._get_default_admin_text_template()
                logger.debug("Using default template")

            # Prepare template context
            context = {
                "contact_name": contact_submission.name,
                "contact_email": contact_submission.email,
                "contact_subject": contact_submission.subject or "No subject provided",
                "contact_message": contact_submission.message,
                "submission_date": contact_submission.submitted_date,
                "site_name": getattr(settings, "SITE_NAME", "Portfolio Website"),
                "site_url": getattr(settings, "SITE_URL", "http://localhost:8000"),
            }

            # Render templates with context
            rendered_html = self._render_template_string(html_content, context)
            rendered_text = self._render_template_string(text_content, context)
            rendered_subject = self._render_template_string(subject, context)

            logger.debug("Sending admin email from=%s to=%s", self.settings.from_email, self.settings.admin_email)

            # Send email
            from django.core.mail import EmailMultiAlternatives

            email = EmailMultiAlternatives(
                subject=rendered_subject,
                body=rendered_text,
                from_email=self.settings.from_email,
                to=[self.settings.admin_email],
            )
            email.attach_alternative(rendered_html, "text/html")
            email.send(fail_silently=False)

            notification.mark_admin_email_sent()
            logger.info(
                "Admin notification sent for contact submission %s", contact_submission.id
            )
            return True

        except Exception as e:
            error_msg = str(e)
            logger.exception("Failed to send admin notification")
            try:
                notification.mark_admin_email_sent(error=error_msg)
            except Exception as inner_e:
                logger.error("Failed to mark admin email as failed: %s", inner_e)
            return False

    def send_thankyou_notification(self, contact_submission, notification):
        """
        Send thank you email to user who submitted contact form
        """
        logger.debug("send_thankyou_notification() called, enabled=%s", self.settings.thankyou_notification_enabled)

        if not self.settings.thankyou_notification_enabled:
            logger.info("Thank you notifications are disabled")
            return False

        try:
            # Get email template or use default
            template = self._get_template("user_thankyou")

            if template:
                subject = template.subject
                html_content = template.html_content
                text_content = template.text_content
                logger.debug("Using custom template: %s", template.name)
            else:
                # Default template
                subject = "Thank you for contacting us!"
                html_content = self._get_default_thankyou_html_template()
                text_content = self._get_default_thankyou_text_template()
                logger.debug("Using default template")

            # Prepare template context
            context = {
                "user_name": contact_submission.name,
                "user_email": contact_submission.email,
                "contact_subject": contact_submission.subject or "your inquiry",
                "submission_date": contact_submission.submitted_date,
                "site_name": getattr(settings, "SITE_NAME", "Roshan Damor Portfolio"),
                "site_url": getattr(settings, "SITE_URL", "http://localhost:8000"),
                "admin_name": "Roshan Damor",
                "reply_email": self.settings.reply_to_email,
            }

            # Render templates with context
            rendered_html = self._render_template_string(html_content, context)
            rendered_text = self._render_template_string(text_content, context)
            rendered_subject = self._render_template_string(subject, context)

            logger.debug("Sending thank-you email from=%s to=%s", self.settings.from_email, contact_submission.email)

            # Send email
            from django.core.mail import EmailMultiAlternatives

            email = EmailMultiAlternatives(
                subject=rendered_subject,
                body=rendered_text,
                from_email=self.settings.from_email,
                to=[contact_submission.email],
                reply_to=[self.settings.reply_to_email],
            )
            email.attach_alternative(rendered_html, "text/html")
            email.send(fail_silently=False)

            notification.mark_thankyou_email_sent()
            logger.info(
                "Thank you notification sent for contact submission %s", contact_submission.id
            )
            return True

        except Exception as e:
            error_msg = str(e)
            logger.exception("Failed to send thank you notification")
            try:
                notification.mark_thankyou_email_sent(error=error_msg)
            except Exception as inner_e:
                logger.error("Failed to mark thankyou email as failed: %s", inner_e)
            return False

    def _get_template(self, template_type):
        """Get active email template by type"""
        try:
            return EmailTemplate.objects.filter(
                template_type=template_type, is_active=True
            ).first()
        except EmailTemplate.DoesNotExist:
            return None

    def _render_template_string(self, template_string, context):
        """Render template string with context variables using safe string replacement.

        Uses simple {{variable}} replacement instead of Django's Template engine
        to prevent server-side template injection (SSTI) from DB-stored templates.
        """
        result = template_string
        for key, value in context.items():
            result = result.replace("{{ " + key + " }}", str(value))
            result = result.replace("{{" + key + "}}", str(value))
        return result

    def _get_default_admin_html_template(self):
        """Default HTML template for admin notification"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>New Contact Form Submission</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #0f172a; color: #e2e8f0; }
                .container { max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.3); border: 1px solid #334155; }
                .header { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; }
                .header h1 { margin: 0; font-size: 24px; font-weight: 600; }
                .header p { margin: 10px 0 0 0; opacity: 0.9; }
                .content { padding: 30px; }
                .field { margin-bottom: 20px; padding: 15px; background: rgba(15, 23, 42, 0.5); border-radius: 5px; border-left: 4px solid #10b981; }
                .field-label { font-weight: 600; color: #10b981; margin-bottom: 5px; font-size: 14px; text-transform: uppercase; }
                .field-value { color: #cbd5e1; line-height: 1.5; }
                .footer { background: #0f172a; padding: 20px; text-align: center; font-size: 14px; color: #64748b; border-top: 1px solid #334155; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📬 New Contact Message!</h1>
                    <p>Someone wants to connect with you</p>
                </div>
                <div class="content">
                    <div class="field">
                        <div class="field-label">👤 From:</div>
                        <div class="field-value">{{ contact_name }} ({{ contact_email }})</div>
                    </div>
                    <div class="field">
                        <div class="field-label">📋 Subject:</div>
                        <div class="field-value">{{ contact_subject }}</div>
                    </div>
                    <div class="field">
                        <div class="field-label">💬 Message:</div>
                        <div class="field-value" style="white-space: pre-line;">{{ contact_message }}</div>
                    </div>
                    <div class="field">
                        <div class="field-label">⏰ Submitted:</div>
                        <div class="field-value">{{ submission_date }}</div>
                    </div>
                </div>
                <div class="footer">
                    <p style="color: #10b981; font-weight: 600;">🚀 Portfolio Contact System</p>
                    <p>This notification was sent from {{ site_name }}</p>
                    <p><a href="{{ site_url }}" style="color: #10b981;">Visit Website</a></p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_default_admin_text_template(self):
        """Default text template for admin notification"""
        return """
        📬 NEW CONTACT MESSAGE!
        
        👤 From: {{ contact_name }} ({{ contact_email }})
        📋 Subject: {{ contact_subject }}
        ⏰ Submitted: {{ submission_date }}
        
        💬 Message:
        {{ contact_message }}
        
        ---
        🚀 Portfolio Contact System
        This notification was sent from {{ site_name }}
        {{ site_url }}
        """

    def _get_default_thankyou_html_template(self):
        """Default HTML template for thank you email"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Thank You for Your Message</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #0f172a; color: #e2e8f0; }
                .container { max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.3); border: 1px solid #334155; }
                .header { background: linear-gradient(135deg, #00A9FF 0%, #0078D4 100%); color: white; padding: 30px; text-align: center; }
                .header h1 { margin: 0; font-size: 24px; font-weight: 600; }
                .header p { margin: 10px 0 0 0; opacity: 0.9; }
                .content { padding: 30px; line-height: 1.6; color: #cbd5e1; }
                .highlight { background: linear-gradient(135deg, rgba(0, 169, 255, 0.1), rgba(0, 120, 212, 0.1)); padding: 15px; border-radius: 5px; border-left: 4px solid #00A9FF; margin: 20px 0; }
                .footer { background: #0f172a; padding: 20px; text-align: center; font-size: 14px; color: #64748b; border-top: 1px solid #334155; }
                .button { display: inline-block; background: #00A9FF; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; font-weight: 500; }
                .personal-note { background: rgba(15, 23, 42, 0.5); border-left: 4px solid #00A9FF; border-radius: 0 8px 8px 0; padding: 20px; margin: 25px 0; font-style: italic; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✨ Thank You for Reaching Out!</h1>
                    <p>I've received your message and I'm excited to connect</p>
                </div>
                <div class="content">
                    <p>Hi {{ user_name }},</p>
                    
                    <p>Thank you so much for taking the time to contact me through my portfolio! I've successfully received your message about "{{ contact_subject }}" and I truly appreciate you reaching out.</p>
                    
                    <div class="highlight">
                        <strong>🚀 What happens next?</strong><br>
                        • I personally review every message that comes through<br>
                        • I'll get back to you within a few hours (usually much sooner!)<br>
                        • You'll receive my response directly at {{ user_email }}<br>
                        • I'm always excited to discuss new opportunities and collaborations
                    </div>
                    
                    <div class="personal-note">
                        <strong>Personal Note:</strong> I believe in building meaningful connections, and I'm looking forward to learning more about your project or opportunity. Whether it's about web development, AI solutions, or just a friendly chat about tech, I'm here for it!
                    </div>
                    
                    <p>While you're waiting for my response, feel free to explore my latest projects and blog posts.</p>
                    
                    <p style="text-align: center;">
                        <a href="{{ site_url }}" class="button">🌐 Explore My Portfolio</a>
                    </p>
                    
                    <p>Thanks again for considering me for your project. I can't wait to hear more about what you're working on!</p>
                    
                    <p>Best regards,<br>
                    <strong>{{ admin_name }}</strong><br>
                    Full-Stack Developer & AI Enthusiast</p>
                </div>
                <div class="footer">
                    <p>This email was sent automatically from my portfolio contact form.</p>
                    <p>For urgent matters, reach me directly at: <a href="mailto:{{ reply_email }}" style="color: #00A9FF;">{{ reply_email }}</a></p>
                    <p style="color: #00A9FF; font-weight: 600;">{{ site_name }}</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_default_thankyou_text_template(self):
        """Default text template for thank you email"""
        return """
        ✨ Thank You for Reaching Out!
        
        Hi {{ user_name }},
        
        Thank you so much for taking the time to contact me through my portfolio! I've successfully received your message about "{{ contact_subject }}" and I truly appreciate you reaching out.
        
        🚀 What happens next?
        • I personally review every message that comes through
        • I'll get back to you within a few hours (usually much sooner!)
        • You'll receive my response directly at {{ user_email }}
        • I'm always excited to discuss new opportunities and collaborations
        
        Personal Note: I believe in building meaningful connections, and I'm looking forward to learning more about your project or opportunity. Whether it's about web development, AI solutions, or just a friendly chat about tech, I'm here for it!
        
        While you're waiting for my response, feel free to explore my latest projects and blog posts.
        
        Visit my portfolio: {{ site_url }}
        
        Thanks again for considering me for your project. I can't wait to hear more about what you're working on!
        
        Best regards,
        {{ admin_name }}
        Full-Stack Developer & AI Enthusiast
        
        ---
        This email was sent automatically from my portfolio contact form.
        For urgent matters, reach me directly at: {{ reply_email }}
        """
