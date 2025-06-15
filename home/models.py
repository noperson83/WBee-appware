# home/models.py
"""
Clean, simple Django 5 models for home dashboard.
Only essential functionality - no bloat.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# Shared abstract models for consistency
from client.models import TimeStampedModel, UUIDModel

User = get_user_model()


class UserPreference(TimeStampedModel):
    """Simple user preferences for dashboard customization."""
    
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # Dashboard preferences
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    sidebar_collapsed = models.BooleanField(default=False)
    items_per_page = models.PositiveIntegerField(default=25, validators=[MinValueValidator(10), MaxValueValidator(100)])
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    browser_notifications = models.BooleanField(default=True)
    
    # Display preferences
    timezone = models.CharField(max_length=50, default='America/Phoenix')
    date_format = models.CharField(max_length=20, default='%Y-%m-%d')
    
    # Metadata handled by TimeStampedModel
    
    class Meta:
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'
    
    def __str__(self):
        return f"{self.user.first_name}'s Preferences"


class Announcement(UUIDModel, TimeStampedModel):
    """Simple company announcements."""
    
    TYPE_CHOICES = [
        ('general', 'General'),
        ('urgent', 'Urgent'),
        ('maintenance', 'Maintenance'),
        ('policy', 'Policy Update'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='general')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Publishing
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_announcements')
    is_active = models.BooleanField(default=True)
    publish_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    # Display options
    show_on_dashboard = models.BooleanField(default=True)
    require_acknowledgment = models.BooleanField(default=False)
    
    # Metadata handled by TimeStampedModel
    
    class Meta:
        ordering = ['-priority', '-publish_date']
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'
    
    def __str__(self):
        return self.title
    
    @property
    def is_expired(self):
        """Check if announcement has expired."""
        if self.expiry_date:
            return timezone.now() > self.expiry_date
        return False
    
    @property
    def is_visible(self):
        """Check if announcement should be visible."""
        now = timezone.now()
        return (
            self.is_active and 
            self.publish_date <= now and 
            not self.is_expired
        )


class AnnouncementAcknowledgment(models.Model):
    """Track user acknowledgments of announcements."""
    
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='acknowledgments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='acknowledgments')
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['announcement', 'user']
        verbose_name = 'Announcement Acknowledgment'
        verbose_name_plural = 'Announcement Acknowledgments'
    
    def __str__(self):
        return f"{self.user.first_name} acknowledged {self.announcement.title}"


class QuickAction(UUIDModel, TimeStampedModel):
    """Quick action buttons for dashboard."""
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True)
    url = models.CharField(max_length=500,blank=True,null=True)
    icon = models.CharField(max_length=50, default='fas fa-star')
    color = models.CharField(max_length=20, default='primary')
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    # Permissions (simple approach)
    required_permission = models.CharField(max_length=100, blank=True)
    
    # Metadata handled by TimeStampedModel
    
    class Meta:
        ordering = ['sort_order', 'title']
        verbose_name = 'Quick Action'
        verbose_name_plural = 'Quick Actions'
    
    def __str__(self):
        return self.title


class DashboardMetric(UUIDModel, TimeStampedModel):
    """Simple metrics for dashboard display."""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    format_string = models.CharField(max_length=50, default='{value}')
    color = models.CharField(max_length=20, default='primary')
    icon = models.CharField(max_length=50, default='fas fa-chart-line')
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Dashboard Metric'
        verbose_name_plural = 'Dashboard Metrics'
    
    def __str__(self):
        return self.name
    
    def formatted_value(self):
        """Return formatted value string."""
        return self.format_string.format(value=self.value)


# Signal to create user preferences automatically
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_preference(sender, instance, created, **kwargs):
    """Create user preferences when user is created."""
    if created:
        UserPreference.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_preference(sender, instance, **kwargs):
    """Save user preferences when user is saved."""
    if hasattr(instance, 'preferences'):
        instance.preferences.save()
