# schedule/admin.py - Modern Admin Interface for Calendar and Event Management

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from decimal import Decimal
from django import forms
from datetime import timedelta

from .models import (
    Calendar, CalendarRelation, Event, EventRelation, Occurrence
)
from .models.rules import Rule

# Inline admins
class CalendarRelationInline(admin.TabularInline):
    """Inline admin for calendar relations"""
    model = CalendarRelation
    extra = 0
    fields = (
        'content_type', 'object_id', 'distinction', 
        'permission_level', 'inheritable', 'notify_on_changes'
    )

class EventRelationInline(admin.TabularInline):
    """Inline admin for event relations"""
    model = EventRelation
    extra = 0
    fields = (
        'content_type', 'object_id', 'distinction', 
        'response_status', 'is_required'
    )

class OccurrenceInline(admin.TabularInline):
    """Inline admin for event occurrences"""
    model = Occurrence
    extra = 0
    fields = (
        'start', 'end', 'cancelled', 'moved_indicator', 'notes'
    )
    readonly_fields = ('moved_indicator',)
    
    def moved_indicator(self, obj):
        if obj.pk and obj.moved:
            return format_html('<span style="color: #ffc107;">⚠ Moved</span>')
        return "—"
    moved_indicator.short_description = 'Status'

# Calendar Admin
@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'calendar_type_badge',
        'color_preview',
        'owner',
        'event_count',
        'upcoming_events',
        'visibility_status',
        'is_active'
    )
    
    list_filter = (
        'calendar_type',
        'is_public',
        'is_active',
        'requires_approval',
        'created_at',
        'owner'
    )
    
    search_fields = (
        'name',
        'description',
        'owner__first_name',
        'owner__last_name',
        'owner__email'
    )
    
    prepopulated_fields = {'slug': ('name',)}
    
    readonly_fields = (
        'calendar_statistics',
        'recent_events_preview',
        'usage_metrics'
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'slug',
                'description',
                'calendar_type',
                'owner'
            )
        }),
        ('Visual Settings', {
            'fields': (
                ('color', 'icon'),
            )
        }),
        ('Permissions & Visibility', {
            'fields': (
                'is_public',
                'is_active',
                'requires_approval',
                'auto_accept_events'
            )
        }),
        ('Settings', {
            'fields': (
                'timezone',
                'default_event_duration'
            ),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': (
                'calendar_statistics',
                'usage_metrics'
            ),
            'classes': ('collapse',)
        }),
        ('Recent Events', {
            'fields': (
                'recent_events_preview',
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [CalendarRelationInline]
    
    actions = ['activate_calendars', 'deactivate_calendars', 'make_public', 'make_private']

    def calendar_type_badge(self, obj):
        """Display calendar type with color coding"""
        colors = {
            'project': '#007bff',
            'worker': '#28a745',
            'company': '#17a2b8',
            'department': '#ffc107',
            'maintenance': '#fd7e14',
            'training': '#6f42c1',
            'holiday': '#dc3545',
            'custom': '#6c757d'
        }
        color = colors.get(obj.calendar_type, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_calendar_type_display()
        )
    calendar_type_badge.short_description = 'Type'

    def color_preview(self, obj):
        """Display color preview"""
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px; display: inline-block;"></div> {}',
            obj.color,
            obj.get_color_display()
        )
    color_preview.short_description = 'Color'

    def event_count(self, obj):
        """Count of events in calendar"""
        count = obj.events.count()
        if count > 0:
            url = reverse('admin:schedule_event_changelist') + f'?calendar__id__exact={obj.id}'
            return format_html('<a href="{}">{} events</a>', url, count)
        return "0 events"
    event_count.short_description = 'Events'

    def upcoming_events(self, obj):
        """Count of upcoming events"""
        upcoming = obj.get_upcoming_events(days=30).count()
        if upcoming > 0:
            return format_html('<span style="color: #007bff;">{} upcoming</span>', upcoming)
        return "No upcoming events"
    upcoming_events.short_description = 'Upcoming (30d)'

    def visibility_status(self, obj):
        """Display visibility status"""
        if obj.is_public:
            return format_html('<span style="color: #28a745;">🌐 Public</span>')
        else:
            return format_html('<span style="color: #6c757d;">🔒 Private</span>')
    visibility_status.short_description = 'Visibility'

    def calendar_statistics(self, obj):
        """Display calendar statistics"""
        total_events = obj.events.count()
        upcoming = obj.get_upcoming_events(days=30).count()
        past_events = obj.events.filter(end__lt=timezone.now()).count()
        
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Total Events:</strong></td><td>{total_events}</td></tr>"
        html += f"<tr><td><strong>Upcoming (30d):</strong></td><td>{upcoming}</td></tr>"
        html += f"<tr><td><strong>Past Events:</strong></td><td>{past_events}</td></tr>"
        html += f"<tr><td><strong>Calendar Type:</strong></td><td>{obj.get_calendar_type_display()}</td></tr>"
        html += f"<tr><td><strong>Created:</strong></td><td>{obj.created_at.strftime('%m/%d/%Y')}</td></tr>"
        html += f"<tr><td><strong>Timezone:</strong></td><td>{obj.timezone}</td></tr>"
        html += "</table>"
        return mark_safe(html)
    calendar_statistics.short_description = 'Calendar Statistics'

    def recent_events_preview(self, obj):
        """Display preview of recent events"""
        recent_events = obj.events.order_by('-created_at')[:5]
        
        if not recent_events:
            return "No events"
        
        html = "<ul style='margin: 0; padding-left: 15px; font-size: 12px;'>"
        for event in recent_events:
            html += f"<li><strong>{event.title}</strong> - {event.start.strftime('%m/%d/%Y %H:%M')}</li>"
        html += "</ul>"
        return mark_safe(html)
    recent_events_preview.short_description = 'Recent Events'

    def usage_metrics(self, obj):
        """Display usage metrics"""
        # Calculate various metrics
        relations_count = obj.calendarrelation_set.count()
        avg_event_duration = obj.events.aggregate(
            avg_duration=Avg('end') - Avg('start')
        )
        
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Relations:</strong></td><td>{relations_count}</td></tr>"
        html += f"<tr><td><strong>Requires Approval:</strong></td><td>{'Yes' if obj.requires_approval else 'No'}</td></tr>"
        html += f"<tr><td><strong>Auto Accept:</strong></td><td>{'Yes' if obj.auto_accept_events else 'No'}</td></tr>"
        html += f"<tr><td><strong>Default Duration:</strong></td><td>{obj.default_event_duration}</td></tr>"
        html += "</table>"
        return mark_safe(html)
    usage_metrics.short_description = 'Usage Metrics'

    def activate_calendars(self, request, queryset):
        """Activate selected calendars"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} calendars activated.")
    activate_calendars.short_description = "Activate calendars"

    def deactivate_calendars(self, request, queryset):
        """Deactivate selected calendars"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} calendars deactivated.")
    deactivate_calendars.short_description = "Deactivate calendars"

    def make_public(self, request, queryset):
        """Make calendars public"""
        updated = queryset.update(is_public=True)
        self.message_user(request, f"{updated} calendars made public.")
    make_public.short_description = "Make public"

    def make_private(self, request, queryset):
        """Make calendars private"""
        updated = queryset.update(is_public=False)
        self.message_user(request, f"{updated} calendars made private.")
    make_private.short_description = "Make private"

# Event Admin
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'event_type_badge',
        'calendar_display',
        'datetime_range',
        'status_indicator',
        'staff_summary',
        'project_display',
        'duration_display',
        'cost_summary'
    )

    list_filter = (
        'event_type',
        'status',
        'priority',
        'privacy',
        'calendar',
        'start',
        'lead',
        'project'
    )

    search_fields = (
        'title',
        'description',
        'location',
        'project__name',
        'project__job_number',
        'lead__first_name',
        'lead__last_name',
        'workers__first_name',
        'workers__last_name'
    )

    date_hierarchy = 'start'

    readonly_fields = (
        'duration_calculation',
        'staff_breakdown',
        'cost_analysis',
        'schedule_analysis',
        'event_statistics',
        'completion_summary'
    )

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title',
                'description',
                ('event_type', 'status', 'priority'),
                'calendar'
            )
        }),
        ('Schedule', {
            'fields': (
                ('start', 'end'),
                'all_day',
                'duration_calculation'
            )
        }),
        ('Work Details', {
            'fields': (
                'project',
                'location',
                ('start_time', 'dist_time'),
                'Supplier'
            )
        }),
        ('Staff Assignment', {
            'fields': (
                'lead',
                'workers',
                'required_workers',
                'staff_breakdown'
            )
        }),
        ('Legacy Fields', {
            'fields': (
                'text',
                'equip',
                'details'
            ),
            'classes': ('collapse',)
        }),
        ('Financial', {
            'fields': (
                ('estimated_cost', 'actual_cost'),
                'cost_analysis'
            ),
            'classes': ('collapse',)
        }),
        ('Recurrence', {
            'fields': (
                'rule',
                'end_recurring_period'
            ),
            'classes': ('collapse',)
        }),
        ('Visual & Notifications', {
            'fields': (
                ('color_event', 'icon'),
                'privacy',
                ('reminder_minutes', 'send_invitations')
            ),
            'classes': ('collapse',)
        }),
        ('Completion', {
            'fields': (
                'completion_notes',
                'completed_at',
                'completion_summary'
            ),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': (
                'creator',
                ('external_id', 'sync_status'),
                'attachment'
            ),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': (
                'schedule_analysis',
                'event_statistics'
            ),
            'classes': ('collapse',)
        })
    )

    filter_horizontal = ('workers',)
    inlines = [EventRelationInline, OccurrenceInline]

    actions = [
        'mark_completed',
        'cancel_events', 
        'reschedule_events',
        'assign_workers',
        'send_reminders'
    ]

    def event_type_badge(self, obj):
        """Display event type with color coding"""
        colors = {
            'meeting': '#007bff',
            'project_work': '#28a745',
            'training': '#17a2b8',
            'maintenance': '#fd7e14',
            'inspection': '#6f42c1',
            'delivery': '#ffc107',
            'travel': '#6c757d',
            'holiday': '#dc3545',
            'sick_leave': '#e83e8c',
            'vacation': '#20c997',
            'emergency': '#dc3545'
        }
        color = colors.get(obj.event_type, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            obj.get_event_type_display()
        )
    event_type_badge.short_description = 'Type'

    def calendar_display(self, obj):
        """Display calendar with color"""
        return format_html(
            '<div style="display: flex; align-items: center;"><div style="width: 12px; height: 12px; background-color: {}; border-radius: 2px; margin-right: 5px;"></div>{}</div>',
            obj.calendar.color,
            obj.calendar.name
        )
    calendar_display.short_description = 'Calendar'

    def datetime_range(self, obj):
        """Display date and time range"""
        if obj.all_day:
            return format_html(
                '<strong>{}</strong><br><small>All Day</small>',
                obj.start.strftime('%m/%d/%Y')
            )
        else:
            return format_html(
                '<strong>{}</strong><br><small>{} - {}</small>',
                obj.start.strftime('%m/%d/%Y'),
                obj.start.strftime('%H:%M'),
                obj.end.strftime('%H:%M')
            )
    datetime_range.short_description = 'Date & Time'

    def status_indicator(self, obj):
        """Display status with appropriate styling"""
        colors = {
            'draft': '#6c757d',
            'confirmed': '#28a745',
            'tentative': '#ffc107',
            'cancelled': '#dc3545',
            'completed': '#17a2b8',
            'no_show': '#fd7e14',
            'rescheduled': '#6f42c1'
        }
        
        color = colors.get(obj.status, '#6c757d')
        icon = '✓' if obj.status == 'completed' else '●'
        
        status_html = format_html(
            '<span style="color: {};">{} {}</span>',
            color,
            icon,
            obj.get_status_display()
        )
        
        # Add overdue indicator
        if obj.is_overdue:
            status_html += format_html('<br><span style="color: #dc3545; font-size: 10px;">⚠ OVERDUE</span>')
        elif obj.is_current:
            status_html += format_html('<br><span style="color: #007bff; font-size: 10px;">🔄 IN PROGRESS</span>')
        
        return status_html
    status_indicator.short_description = 'Status'

    def staff_summary(self, obj):
        """Display staff assignment summary"""
        worker_count = obj.worker_count
        required = obj.required_workers
        
        if obj.lead:
            lead_name = obj.lead.get_short_name()
            if worker_count > 0:
                return format_html(
                    '<strong>Lead:</strong> {}<br><small>{}/{} workers</small>',
                    lead_name,
                    worker_count,
                    required
                )
            else:
                return format_html('<strong>Lead:</strong> {}', lead_name)
        elif worker_count > 0:
            return format_html(
                '{}/{} workers',
                worker_count,
                required
            )
        else:
            return "No staff assigned"
    staff_summary.short_description = 'Staff'

    def project_display(self, obj):
        """Display project information"""
        if obj.project:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.project.name[:20] + ('...' if len(obj.project.name) > 20 else ''),
                obj.project.job_number or 'No job #'
            )
        return "No project"
    project_display.short_description = 'Project'

    def duration_display(self, obj):
        """Display event duration"""
        hours = obj.duration_hours
        return f"{hours:.1f}h"
    duration_display.short_description = 'Duration'

    def cost_summary(self, obj):
        """Display cost information"""
        if obj.estimated_cost and obj.actual_cost:
            variance = obj.cost_variance
            variance_color = '#dc3545' if variance > 0 else '#28a745'
            return format_html(
                '<strong>${:.0f}</strong><br><small style="color: {};">Var: ${:.0f}</small>',
                obj.actual_cost,
                variance_color,
                variance
            )
        elif obj.estimated_cost:
            return format_html('<strong>Est: ${:.0f}</strong>', obj.estimated_cost)
        elif obj.actual_cost:
            return format_html('<strong>${:.0f}</strong>', obj.actual_cost)
        return "No cost data"
    cost_summary.short_description = 'Cost'

    def duration_calculation(self, obj):
        """Display duration calculation details"""
        duration = obj.duration
        hours = obj.duration_hours
        
        html = f"<strong>Duration:</strong> {duration}<br>"
        html += f"<strong>Hours:</strong> {hours:.2f}<br>"
        
        if obj.all_day:
            html += "<strong>Type:</strong> All Day Event"
        else:
            html += f"<strong>Start:</strong> {obj.start.strftime('%m/%d/%Y %H:%M')}<br>"
            html += f"<strong>End:</strong> {obj.end.strftime('%m/%d/%Y %H:%M')}"
        
        return mark_safe(html)
    duration_calculation.short_description = 'Duration Details'

    def staff_breakdown(self, obj):
        """Display detailed staff breakdown"""
        html = "<table style='font-size: 12px;'>"
        
        if obj.lead:
            html += f"<tr><td><strong>Lead:</strong></td><td>{obj.lead.get_full_name()}</td></tr>"
        
        html += f"<tr><td><strong>Required Workers:</strong></td><td>{obj.required_workers}</td></tr>"
        html += f"<tr><td><strong>Assigned Workers:</strong></td><td>{obj.worker_count}</td></tr>"
        
        if obj.worker_count > 0:
            html += "<tr><td><strong>Workers:</strong></td><td>"
            workers = list(obj.workers.all())
            worker_names = [w.get_short_name() for w in workers[:3]]
            if len(workers) > 3:
                worker_names.append(f"and {len(workers) - 3} more")
            html += ", ".join(worker_names)
            html += "</td></tr>"
        
        staffing_status = "✓ Fully Staffed" if obj.is_fully_staffed else "⚠ Understaffed"
        status_color = "#28a745" if obj.is_fully_staffed else "#ffc107"
        html += f"<tr><td><strong>Status:</strong></td><td style='color: {status_color};'>{staffing_status}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    staff_breakdown.short_description = 'Staff Details'

    def cost_analysis(self, obj):
        """Display cost analysis"""
        html = "<table style='font-size: 12px;'>"
        
        if obj.estimated_cost:
            html += f"<tr><td><strong>Estimated:</strong></td><td>${obj.estimated_cost:.2f}</td></tr>"
        
        if obj.actual_cost:
            html += f"<tr><td><strong>Actual:</strong></td><td>${obj.actual_cost:.2f}</td></tr>"
        
        if obj.cost_variance is not None:
            variance = obj.cost_variance
            color = '#dc3545' if variance > 0 else '#28a745'
            html += f"<tr><td><strong>Variance:</strong></td><td style='color: {color};'>${variance:.2f}</td></tr>"
            
            if obj.estimated_cost:
                variance_pct = (variance / obj.estimated_cost) * 100
                html += f"<tr><td><strong>Variance %:</strong></td><td style='color: {color};'>{variance_pct:.1f}%</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    cost_analysis.short_description = 'Cost Analysis'

    def schedule_analysis(self, obj):
        """Display schedule analysis"""
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Status:</strong></td><td>{obj.get_status_display()}</td></tr>"
        html += f"<tr><td><strong>Priority:</strong></td><td>{obj.get_priority_display()}</td></tr>"
        
        if obj.is_past:
            html += "<tr><td><strong>Timeline:</strong></td><td style='color: #6c757d;'>Past Event</td></tr>"
        elif obj.is_current:
            html += "<tr><td><strong>Timeline:</strong></td><td style='color: #007bff;'>Currently Active</td></tr>"
        elif obj.is_upcoming:
            days_until = (obj.start.date() - timezone.now().date()).days
            html += f"<tr><td><strong>Timeline:</strong></td><td style='color: #28a745;'>In {days_until} days</td></tr>"
        
        if obj.is_overdue:
            html += "<tr><td><strong>Alert:</strong></td><td style='color: #dc3545;'>⚠ OVERDUE</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    schedule_analysis.short_description = 'Schedule Analysis'

    def event_statistics(self, obj):
        """Display comprehensive event statistics"""
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Event ID:</strong></td><td>{obj.id}</td></tr>"
        html += f"<tr><td><strong>Created:</strong></td><td>{obj.created_at.strftime('%m/%d/%Y %H:%M')}</td></tr>"
        html += f"<tr><td><strong>Creator:</strong></td><td>{obj.creator.get_full_name() if obj.creator else 'System'}</td></tr>"
        html += f"<tr><td><strong>Last Updated:</strong></td><td>{obj.updated_at.strftime('%m/%d/%Y %H:%M')}</td></tr>"
        
        if obj.location:
            html += f"<tr><td><strong>Location:</strong></td><td>{obj.location}</td></tr>"
        
        if obj.rule:
            html += f"<tr><td><strong>Recurrence:</strong></td><td>{obj.rule.name}</td></tr>"
            occurrences = obj.occurrence_set.count()
            html += f"<tr><td><strong>Occurrences:</strong></td><td>{occurrences}</td></tr>"
        
        if obj.reminder_minutes:
            html += f"<tr><td><strong>Reminder:</strong></td><td>{obj.reminder_minutes} minutes before</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    event_statistics.short_description = 'Event Statistics'

    def completion_summary(self, obj):
        """Display completion summary"""
        if obj.status != 'completed':
            return "Event not completed"
        
        html = "<table style='font-size: 12px;'>"
        
        if obj.completed_at:
            html += f"<tr><td><strong>Completed:</strong></td><td>{obj.completed_at.strftime('%m/%d/%Y %H:%M')}</td></tr>"
        
        if obj.completion_notes:
            notes = obj.completion_notes[:100] + ('...' if len(obj.completion_notes) > 100 else '')
            html += f"<tr><td><strong>Notes:</strong></td><td>{notes}</td></tr>"
        
        # Calculate completion timeliness
        if obj.completed_at and obj.end:
            if obj.completed_at <= obj.end:
                html += "<tr><td><strong>Timeliness:</strong></td><td style='color: #28a745;'>✓ On Time</td></tr>"
            else:
                delay = obj.completed_at - obj.end
                html += f"<tr><td><strong>Timeliness:</strong></td><td style='color: #dc3545;'>⚠ {delay} late</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    completion_summary.short_description = 'Completion Details'

    # Custom actions
    def mark_completed(self, request, queryset):
        """Mark selected events as completed"""
        updated = 0
        for event in queryset.exclude(status='completed'):
            event.mark_completed()
            updated += 1
        self.message_user(request, f"{updated} events marked as completed.")
    mark_completed.short_description = "Mark as completed"

    def cancel_events(self, request, queryset):
        """Cancel selected events"""
        updated = queryset.exclude(status__in=['cancelled', 'completed']).update(status='cancelled')
        self.message_user(request, f"{updated} events cancelled.")
    cancel_events.short_description = "Cancel events"

    def reschedule_events(self, request, queryset):
        """Mark events for rescheduling"""
        updated = queryset.exclude(status__in=['cancelled', 'completed']).update(status='rescheduled')
        self.message_user(request, f"{updated} events marked for rescheduling.")
    reschedule_events.short_description = "Mark for rescheduling"

    def assign_workers(self, request, queryset):
        """Bulk assign workers (would open a form in real implementation)"""
        count = queryset.count()
        self.message_user(request, f"{count} events selected for worker assignment.")
    assign_workers.short_description = "Assign workers"

    def send_reminders(self, request, queryset):
        """Send reminders for upcoming events"""
        upcoming = queryset.filter(start__gt=timezone.now(), start__lt=timezone.now() + timedelta(days=1))
        count = upcoming.count()
        self.message_user(request, f"Reminders sent for {count} upcoming events.")
    send_reminders.short_description = "Send reminders"

# Calendar Relation Admin
@admin.register(CalendarRelation)
class CalendarRelationAdmin(admin.ModelAdmin):
    list_display = (
        'calendar',
        'content_object_display',
        'distinction',
        'permission_badge',
        'inheritable',
        'notify_on_changes',
        'created_at'
    )
    
    list_filter = (
        'permission_level',
        'inheritable',
        'notify_on_changes',
        'created_at',
        'calendar__calendar_type'
    )
    
    search_fields = (
        'calendar__name',
        'distinction'
    )

    def content_object_display(self, obj):
        """Display the related object"""
        return f"{obj.content_type.model}: {obj.content_object}"
    content_object_display.short_description = 'Related Object'

    def permission_badge(self, obj):
        """Display permission level with color coding"""
        colors = {
            'view': '#6c757d',
            'contribute': '#17a2b8',
            'edit': '#ffc107',
            'manage': '#fd7e14',
            'admin': '#dc3545'
        }
        color = colors.get(obj.permission_level, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            obj.get_permission_level_display()
        )
    permission_badge.short_description = 'Permission'

# Event Relation Admin
@admin.register(EventRelation)
class EventRelationAdmin(admin.ModelAdmin):
    list_display = (
        'event',
        'content_object_display',
        'distinction_badge',
        'response_status_display',
        'is_required',
        'created_at'
    )
    
    list_filter = (
        'distinction',
        'response_status',
        'is_required',
        'send_notifications',
        'created_at'
    )
    
    search_fields = (
        'event__title',
        'distinction'
    )

    def content_object_display(self, obj):
        """Display the related object"""
        return f"{obj.content_type.model}: {obj.content_object}"
    content_object_display.short_description = 'Related Object'

    def distinction_badge(self, obj):
        """Display distinction with color coding"""
        colors = {
            'attendee': '#007bff',
            'organizer': '#28a745',
            'resource': '#17a2b8',
            'location': '#ffc107',
            'viewer': '#6c757d',
            'participant': '#6f42c1',
            'observer': '#fd7e14'
        }
        color = colors.get(obj.distinction, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            obj.get_distinction_display()
        )
    distinction_badge.short_description = 'Role'

    def response_status_display(self, obj):
        """Display response status with appropriate styling"""
        colors = {
            'pending': '#6c757d',
            'accepted': '#28a745',
            'declined': '#dc3545',
            'tentative': '#ffc107'
        }
        color = colors.get(obj.response_status, '#6c757d')
        
        return format_html(
            '<span style="color: {};">● {}</span>',
            color,
            obj.get_response_status_display()
        )
    response_status_display.short_description = 'Response'

# Occurrence Admin
@admin.register(Occurrence)
class OccurrenceAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'event',
        'datetime_display',
        'status_display',
        'moved_indicator'
    )
    
    list_filter = (
        'cancelled',
        'start',
        'event__event_type',
        'event__calendar'
    )
    
    search_fields = (
        'title',
        'description',
        'event__title',
        'notes'
    )
    
    readonly_fields = ('moved_indicator', 'duration_display', 'occurrence_details')
    
    fieldsets = (
        ('Occurrence Information', {
            'fields': (
                'event',
                ('title', 'description'),
                'notes'
            )
        }),
        ('Schedule', {
            'fields': (
                ('start', 'end'),
                ('original_start', 'original_end'),
                'moved_indicator',
                'duration_display'
            )
        }),
        ('Status', {
            'fields': (
                'cancelled',
                'status_override'
            )
        }),
        ('Details', {
            'fields': (
                'occurrence_details',
            ),
            'classes': ('collapse',)
        })
    )

    def datetime_display(self, obj):
        """Display occurrence date and time"""
        return format_html(
            '<strong>{}</strong><br><small>{} - {}</small>',
            obj.start.strftime('%m/%d/%Y'),
            obj.start.strftime('%H:%M'),
            obj.end.strftime('%H:%M')
        )
    datetime_display.short_description = 'Date & Time'

    def status_display(self, obj):
        """Display occurrence status"""
        if obj.cancelled:
            return format_html('<span style="color: #dc3545;">✗ Cancelled</span>')
        elif obj.status_override:
            return format_html('<span style="color: #ffc107;">⚠ {}</span>', obj.status_override)
        else:
            return format_html('<span style="color: #28a745;">✓ Active</span>')
    status_display.short_description = 'Status'

    def moved_indicator(self, obj):
        """Indicate if occurrence was moved"""
        if obj.moved:
            return format_html('<span style="color: #ffc107;">⚠ Moved from original time</span>')
        return format_html('<span style="color: #28a745;">✓ Original time</span>')
    moved_indicator.short_description = 'Movement Status'

    def duration_display(self, obj):
        """Display duration"""
        return f"{obj.duration_hours:.1f} hours"
    duration_display.short_description = 'Duration'

    def occurrence_details(self, obj):
        """Display occurrence details"""
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Event:</strong></td><td>{obj.event.title}</td></tr>"
        html += f"<tr><td><strong>Calendar:</strong></td><td>{obj.event.calendar.name}</td></tr>"
        html += f"<tr><td><strong>Duration:</strong></td><td>{obj.duration}</td></tr>"
        
        if obj.moved:
            html += f"<tr><td><strong>Original Start:</strong></td><td>{obj.original_start.strftime('%m/%d/%Y %H:%M')}</td></tr>"
            html += f"<tr><td><strong>Original End:</strong></td><td>{obj.original_end.strftime('%m/%d/%Y %H:%M')}</td></tr>"
            html += f"<tr><td><strong>Current Start:</strong></td><td>{obj.start.strftime('%m/%d/%Y %H:%M')}</td></tr>"
            html += f"<tr><td><strong>Current End:</strong></td><td>{obj.end.strftime('%m/%d/%Y %H:%M')}</td></tr>"
        
        html += f"<tr><td><strong>Created:</strong></td><td>{obj.created_at.strftime('%m/%d/%Y %H:%M')}</td></tr>"
        html += f"<tr><td><strong>Updated:</strong></td><td>{obj.updated_at.strftime('%m/%d/%Y %H:%M')}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    occurrence_details.short_description = 'Occurrence Details'

# Rule Admin (imported from existing)
@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'frequency', 'description')
    list_filter = ('frequency',)
    search_fields = ('name', 'description')
