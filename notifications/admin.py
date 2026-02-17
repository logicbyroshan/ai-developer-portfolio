from django.contrib import admin
from .models import ContactNotification, EmailTemplate, NotificationSettings

@admin.register(ContactNotification)
class ContactNotificationAdmin(admin.ModelAdmin):
    """Admin interface for ContactNotification model"""
    
    list_display = [
        'id', 
        'contact_name',
        'contact_email', 
        'status',
        'admin_email_sent',
        'thankyou_email_sent',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'admin_email_sent',
        'thankyou_email_sent',
        'created_at',
    ]
    
    search_fields = [
        'contact_submission__name',
        'contact_submission__email',
        'contact_submission__subject',
    ]
    
    readonly_fields = [
        'contact_submission',
        'created_at',
        'updated_at',
        'admin_email_sent_at',
        'thankyou_email_sent_at',
    ]
    
    ordering = ['-created_at']
    
    date_hierarchy = 'created_at'
    
    def contact_name(self, obj):
        """Display contact submission name"""
        return obj.contact_submission.name
    contact_name.short_description = 'Contact Name'
    
    def contact_email(self, obj):
        """Display contact submission email"""
        return obj.contact_submission.email
    contact_email.short_description = 'Contact Email'
    
    def has_add_permission(self, request):
        """Disable manual creation of notifications"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only allow deletion of failed notifications"""
        if obj and obj.status == ContactNotification.FAILED:
            return True
        return False

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Admin interface for EmailTemplate model"""
    
    list_display = [
        'name',
        'template_type',
        'is_active',
        'created_at',
        'updated_at'
    ]
    
    list_filter = [
        'template_type',
        'is_active',
        'created_at',
    ]
    
    search_fields = [
        'name',
        'subject',
        'description',
    ]
    
    fields = [
        'name',
        'description',
        'template_type',
        'is_active',
        'subject',
        'html_content',
        'text_content',
    ]
    
    ordering = ['template_type', 'name']
    
    def save_model(self, request, obj, form, change):
        """Ensure only one active template per type"""
        if obj.is_active:
            # Deactivate other templates of the same type
            EmailTemplate.objects.filter(
                template_type=obj.template_type,
                is_active=True
            ).exclude(id=obj.id).update(is_active=False)
        
        super().save_model(request, obj, form, change)

@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    """Admin interface for NotificationSettings model"""
    
    fieldsets = [
        ('Email Configuration', {
            'fields': [
                'admin_email',
                'from_email',
                'reply_to_email',
            ]
        }),
        ('Notification Controls', {
            'fields': [
                'admin_notification_enabled',
                'thankyou_notification_enabled',
            ]
        }),
        ('Timestamps', {
            'fields': [
                'created_at',
                'updated_at',
            ],
            'classes': ['collapse'],
        }),
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        """Only allow one settings instance"""
        if NotificationSettings.objects.exists():
            return False
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of settings"""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Redirect to change view if settings exist"""
        if NotificationSettings.objects.exists():
            settings_obj = NotificationSettings.objects.first()
            from django.shortcuts import redirect
            return redirect('admin:notifications_notificationsettings_change', settings_obj.id)
        return super().changelist_view(request, extra_context)

# Custom admin site configuration
admin.site.site_header = "Roshan Damor — Portfolio Admin"
admin.site.site_title = "Portfolio Admin"
admin.site.index_title = "Dashboard"
