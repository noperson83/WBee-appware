# home/admin.py
"""
Clean Django admin configuration for home app.
Simple, focused admin without unnecessary complexity.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import UserPreference, Announcement, AnnouncementAcknowledgment, QuickAction, DashboardMetric


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    """Admin interface for user preferences."""
    
    list_display = [
        'user', 'theme', 'items_per_page', 'timezone',
        'email_notifications', 'browser_notifications', 'updated_at'
    ]
    
    list_filter = [
        'theme', 'timezone', 'email_notifications',
        'browser_notifications', 'created_at'
    ]
    
    search_fields = ['user__first_name', 'user__first_name', 'user__last_name']
    ordering = ['-updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Dashboard Preferences', {
            'fields': ('theme', 'sidebar_collapsed', 'items_per_page'),
        }),
        ('Notification Preferences', {
            'fields': ('email_notifications', 'browser_notifications'),
        }),
        ('Display Preferences', {
            'fields': ('date_format', 'timezone'),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """Admin interface for company announcements."""
    
    list_display = [
        'title', 'announcement_type', 'priority', 'created_by',
        'publish_date', 'expiry_date', 'is_active', 'acknowledgment_count'
    ]
    
    list_filter = [
        'announcement_type', 'priority', 'is_active',
        'show_on_dashboard', 'publish_date', 'created_at'
    ]
    
    search_fields = ['title', 'content', 'created_by__first_name']
    ordering = ['-priority', '-publish_date']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'announcement_type', 'priority')
        }),
        ('Publishing', {
            'fields': ('publish_date', 'expiry_date', 'is_active'),
        }),
        ('Display Options', {
            'fields': ('show_on_dashboard', 'require_acknowledgment'),
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    
    def acknowledgment_count(self, obj):
        """Show acknowledgment count."""
        if obj.require_acknowledgment:
            count = obj.acknowledgments.count()
            return format_html('<span class="badge badge-info">{} acks</span>', count)
        return '—'
    acknowledgment_count.short_description = 'Acknowledgments'
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current user."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['publish_announcements', 'unpublish_announcements']
    
    def publish_announcements(self, request, queryset):
        """Publish selected announcements."""
        updated = queryset.update(is_active=True, publish_date=timezone.now())
        self.message_user(request, f'{updated} announcements published.')
    publish_announcements.short_description = 'Publish selected announcements'
    
    def unpublish_announcements(self, request, queryset):
        """Unpublish selected announcements."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} announcements unpublished.')
    unpublish_announcements.short_description = 'Unpublish selected announcements'


@admin.register(AnnouncementAcknowledgment)
class AnnouncementAcknowledgmentAdmin(admin.ModelAdmin):
    """Admin interface for announcement acknowledgments."""
    
    list_display = ['announcement', 'user', 'acknowledged_at']
    list_filter = ['acknowledged_at', 'announcement__announcement_type']
    search_fields = [
        'announcement__title', 'user__first_name', 
        'user__first_name', 'user__last_name'
    ]
    ordering = ['-acknowledged_at']
    
    def has_add_permission(self, request):
        """Prevent manual addition of acknowledgments."""
        return False


@admin.register(QuickAction)
class QuickActionAdmin(admin.ModelAdmin):
    """Admin interface for quick actions."""
    
    list_display = [
        'title', 'url', 'icon', 'color',
        'required_permission', 'is_active', 'sort_order'
    ]
    
    list_filter = ['color', 'is_active']
    search_fields = ['title', 'description', 'url']
    ordering = ['sort_order', 'title']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'sort_order')
        }),
        ('Action Configuration', {
            'fields': ('url',),
        }),
        ('Display', {
            'fields': ('icon', 'color'),
        }),
        ('Permissions', {
            'fields': ('required_permission', 'is_active'),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['activate_actions', 'deactivate_actions']
    
    def activate_actions(self, request, queryset):
        """Activate selected quick actions."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} quick actions activated.')
    activate_actions.short_description = 'Activate selected actions'
    
    def deactivate_actions(self, request, queryset):
        """Deactivate selected quick actions."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} quick actions deactivated.')
    deactivate_actions.short_description = 'Deactivate selected actions'


@admin.register(DashboardMetric)
class DashboardMetricAdmin(admin.ModelAdmin):
    """Admin interface for dashboard metrics."""
    
    list_display = [
        'name', 'value', 'formatted_value', 'color',
        'icon', 'is_active', 'last_updated'
    ]
    
    list_filter = ['color', 'is_active', 'last_updated']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'value')
        }),
        ('Display', {
            'fields': ('format_string', 'color', 'icon'),
        }),
        ('Status', {
            'fields': ('is_active', 'last_updated'),
        }),
    )
    
    readonly_fields = ['last_updated']
    
    actions = ['activate_metrics', 'deactivate_metrics']
    
    def activate_metrics(self, request, queryset):
        """Activate selected metrics."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} metrics activated.')
    activate_metrics.short_description = 'Activate selected metrics'
    
    def deactivate_metrics(self, request, queryset):
        """Deactivate selected metrics."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} metrics deactivated.')
    deactivate_metrics.short_description = 'Deactivate selected metrics'


# Customize admin site header and title
admin.site.site_header = 'WBEE Universal Company Manager'
admin.site.site_title = 'WBEE Admin'
admin.site.index_title = 'Dashboard & Home Management'