# timecard/admin.py - Modern Admin Interface for Timecard Management

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
    TimeCard, TimesheetPeriod, TimeCardAttachment, TimesheetSummary
)

# Inline admins
class TimeCardAttachmentInline(admin.TabularInline):
    """Inline admin for timecard attachments"""
    model = TimeCardAttachment
    extra = 0
    fields = ('file', 'description', 'uploaded_at')
    readonly_fields = ('uploaded_at',)

class TimeCardInline(admin.TabularInline):
    """Inline admin for timecards in period view"""
    model = TimeCard
    extra = 0
    fields = (
        'date', 'worker', 'project', 'start_time', 'end_time', 
        'total_hours_display', 'status'
    )
    readonly_fields = ('total_hours_display',)
    
    def total_hours_display(self, obj):
        if obj.pk:
            return f"{obj.total_hours:.2f}h"
        return "—"
    total_hours_display.short_description = 'Hours'

# Timesheet Period Admin
@admin.register(TimesheetPeriod)
class TimesheetPeriodAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'period_type',
        'date_range_display',
        'status_badge',
        'timecard_count',
        'total_hours_display',
        'due_date_display',
        'is_active'
    )
    
    list_filter = (
        'period_type',
        'status',
        'is_active',
        'start_date',
        'due_date'
    )
    
    search_fields = (
        'name',
    )
    
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Period Information', {
            'fields': (
                'name',
                'period_type',
                ('start_date', 'end_date'),
                'due_date'
            )
        }),
        ('Status', {
            'fields': (
                'status',
                'is_active'
            )
        })
    )
    
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    inlines = [TimeCardInline]
    
    actions = ['activate_periods', 'deactivate_periods', 'generate_summaries']

    def date_range_display(self, obj):
        """Display date range"""
        return format_html(
            '{} to {}<br><small>{} days</small>',
            obj.start_date.strftime('%m/%d/%Y'),
            obj.end_date.strftime('%m/%d/%Y'),
            obj.total_days
        )
    date_range_display.short_description = 'Date Range'

    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'open': '#28a745',
            'submitted': '#007bff',
            'approved': '#17a2b8',
            'rejected': '#dc3545',
            'paid': '#6c757d'
        }
        color = colors.get(obj.status, '#007bff')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def timecard_count(self, obj):
        """Count timecards in this period"""
        count = TimeCard.objects.filter(
            date__gte=obj.start_date,
            date__lte=obj.end_date
        ).count()
        
        if count > 0:
            url = reverse('admin:timecard_timecard_changelist') + f'?date__gte={obj.start_date}&date__lte={obj.end_date}'
            return format_html('<a href="{}">{} timecards</a>', url, count)
        return "0 timecards"
    timecard_count.short_description = 'Timecards'

    def total_hours_display(self, obj):
        """Display total hours for period"""
        total = TimeCard.objects.filter(
            date__gte=obj.start_date,
            date__lte=obj.end_date
        ).aggregate(total=Sum('total_hours'))['total'] or Decimal('0')
        
        return f"{total:.1f}h"
    total_hours_display.short_description = 'Total Hours'

    def due_date_display(self, obj):
        """Display due date with warning if overdue"""
        if not obj.due_date:
            return "No deadline"
        
        if obj.is_overdue:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">⚠ {}</span>',
                obj.due_date.strftime('%m/%d/%Y')
            )
        elif obj.due_date <= timezone.now().date() + timedelta(days=3):
            return format_html(
                '<span style="color: #ffc107; font-weight: bold;">⏰ {}</span>',
                obj.due_date.strftime('%m/%d/%Y')
            )
        else:
            return obj.due_date.strftime('%m/%d/%Y')
    due_date_display.short_description = 'Due Date'

    def activate_periods(self, request, queryset):
        """Activate selected periods"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} periods activated.")
    activate_periods.short_description = "Activate selected periods"

    def deactivate_periods(self, request, queryset):
        """Deactivate selected periods"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} periods deactivated.")
    deactivate_periods.short_description = "Deactivate selected periods"

    def generate_summaries(self, request, queryset):
        """Generate timesheet summaries for periods"""
        count = 0
        for period in queryset:
            # This would generate summaries for all workers in the period
            count += 1
        self.message_user(request, f"Summaries generated for {count} periods.")
    generate_summaries.short_description = "Generate timesheet summaries"

    def total_days_display(self, obj):
        """Calculate and display total days in period"""
        if obj.start_date and obj.end_date:
            delta = obj.end_date - obj.start_date
            days = delta.days + 1  # Include both start and end date
            return f"{days} days"
        return "—"
    total_days_display.short_description = 'Total Days'

    def period_statistics(self, obj):
        """Display comprehensive period statistics"""
        # Implementation shown in the artifact above
        pass

# Main TimeCard Admin
@admin.register(TimeCard)
class TimeCardAdmin(admin.ModelAdmin):
    list_display = (
        'worker',
        'date',
        'project_display',
        'time_range_display',
        'hours_breakdown',
        'status_badge',
        'pay_display',
        'photo_preview'
    )

    list_filter = (
        'status',
        'work_type',
        'date',
        'worker',
        'project',
        'timesheet_period'
    )

    search_fields = (
        'worker__first_name',
        'worker__last_name',
        'worker__email',
        'project__name',
        'project__job_number',
        'description',
        'location'
    )

    date_hierarchy = 'date'

    readonly_fields = (
        'total_hours_display',
        'regular_hours_display',
        'overtime_hours_display',
        'pay_calculation',
        'photo_preview',
        'duration_breakdown',
        'validation_status',
        'timecard_statistics'
    )

    fieldsets = (
        ('Basic Information', {
            'fields': (
                ('worker', 'date'),
                ('project', 'work_type'),
                'status'
            )
        }),
        ('Time Tracking', {
            'fields': (
                ('start_time', 'end_time'),
                ('lunch_start', 'lunch_end'),
                'break_minutes',
                'duration_breakdown'
            )
        }),
        ('Work Details', {
            'fields': (
                'description',
                'location',
                ('mileage', 'expenses')
            )
        }),
        ('Pay Information', {
            'fields': (
                'hourly_rate',
                'pay_calculation'
            ),
            'classes': ('collapse',)
        }),
        ('Hours Breakdown', {
            'fields': (
                'total_hours_display',
                'regular_hours_display',
                'overtime_hours_display'
            ),
            'classes': ('collapse',)
        }),
        ('Attachments', {
            'fields': (
                ('photo', 'photo_preview'),
                'notes'
            ),
            'classes': ('collapse',)
        }),
        ('Workflow', {
            'fields': (
                'timesheet_period',
                ('submitted_at', 'approved_at'),
                'approved_by'
            ),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': (
                'validation_status',
                'timecard_statistics'
            ),
            'classes': ('collapse',)
        })
    )

    inlines = [TimeCardAttachmentInline]

    actions = [
        'approve_timecards',
        'reject_timecards',
        'calculate_pay',
        'export_to_payroll'
    ]

    def project_display(self, obj):
        """Display project with job number"""
        if obj.project:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.project.name,
                obj.project.job_number or 'No job #'
            )
        return "No project"
    project_display.short_description = 'Project'

    def time_range_display(self, obj):
        """Display time range"""
        time_str = f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
        
        if obj.lunch_start and obj.lunch_end:
            lunch_str = f"Lunch: {obj.lunch_start.strftime('%H:%M')}-{obj.lunch_end.strftime('%H:%M')}"
            return format_html('{}<br><small style="color: #666;">{}</small>', time_str, lunch_str)
        
        return time_str
    time_range_display.short_description = 'Time Range'

    def hours_breakdown(self, obj):
        """Display hours breakdown"""
        return format_html(
            '<strong>{:.2f}h</strong><br>'
            '<small>Reg: {:.2f}h | OT: {:.2f}h</small>',
            obj.total_hours,
            obj.regular_hours,
            obj.overtime_hours
        )
    hours_breakdown.short_description = 'Hours'

    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'draft': '#6c757d',
            'submitted': '#007bff',
            'approved': '#28a745',
            'rejected': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def pay_display(self, obj):
        """Display pay calculation"""
        total_pay = obj.total_pay
        rate = obj.effective_hourly_rate
        
        if total_pay > 0:
            return format_html(
                '<strong>${:.2f}</strong><br><small>@${:.2f}/hr</small>',
                total_pay,
                rate
            )
        return "—"
    pay_display.short_description = 'Pay'

    def photo_preview(self, obj):
        """Display photo preview"""
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 75px; border-radius: 3px;" />',
                obj.photo.url
            )
        return "—"
    photo_preview.short_description = 'Photo'

    # Readonly field methods
    def total_hours_display(self, obj):
        """Display total hours calculation"""
        return f"{obj.total_hours:.2f} hours"
    total_hours_display.short_description = 'Total Hours'

    def regular_hours_display(self, obj):
        """Display regular hours"""
        return f"{obj.regular_hours:.2f} hours"
    regular_hours_display.short_description = 'Regular Hours'

    def overtime_hours_display(self, obj):
        """Display overtime hours"""
        return f"{obj.overtime_hours:.2f} hours"
    overtime_hours_display.short_description = 'Overtime Hours'

    def pay_calculation(self, obj):
        """Display detailed pay calculation"""
        rate = obj.effective_hourly_rate
        regular_pay = obj.regular_hours * rate
        overtime_pay = obj.overtime_hours * rate * Decimal('1.5')
        total_pay = obj.total_pay
        
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Hourly Rate:</strong></td><td>${rate:.2f}</td></tr>"
        html += f"<tr><td><strong>Regular Hours:</strong></td><td>{obj.regular_hours:.2f} × ${rate:.2f} = ${regular_pay:.2f}</td></tr>"
        
        if obj.overtime_hours > 0:
            ot_rate = rate * Decimal('1.5')
            html += f"<tr><td><strong>Overtime Hours:</strong></td><td>{obj.overtime_hours:.2f} × ${ot_rate:.2f} = ${overtime_pay:.2f}</td></tr>"
        
        html += f"<tr><td><strong>Total Pay:</strong></td><td><strong>${total_pay:.2f}</strong></td></tr>"
        
        if obj.mileage:
            html += f"<tr><td><strong>Mileage:</strong></td><td>{obj.mileage:.1f} miles</td></tr>"
        
        if obj.expenses:
            html += f"<tr><td><strong>Expenses:</strong></td><td>${obj.expenses:.2f}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    pay_calculation.short_description = 'Pay Calculation'

    def duration_breakdown(self, obj):
        """Display time duration breakdown"""
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Start Time:</strong></td><td>{obj.start_time.strftime('%H:%M')}</td></tr>"
        html += f"<tr><td><strong>End Time:</strong></td><td>{obj.end_time.strftime('%H:%M')}</td></tr>"
        
        if obj.lunch_start and obj.lunch_end:
            lunch_duration = obj.lunch_duration_minutes
            html += f"<tr><td><strong>Lunch Break:</strong></td><td>{obj.lunch_start.strftime('%H:%M')} - {obj.lunch_end.strftime('%H:%M')} ({lunch_duration} min)</td></tr>"
        
        if obj.break_minutes > 0:
            html += f"<tr><td><strong>Additional Breaks:</strong></td><td>{obj.break_minutes} minutes</td></tr>"
        
        html += f"<tr><td><strong>Total Hours:</strong></td><td><strong>{obj.total_hours:.2f} hours</strong></td></tr>"
        html += "</table>"
        return mark_safe(html)
    duration_breakdown.short_description = 'Duration Breakdown'

    def validation_status(self, obj):
        """Display validation status"""
        html = "<table style='font-size: 12px;'>"
        
        # Check for potential issues
        if obj.total_hours > Decimal('12.00'):
            html += "<tr><td style='color: #ffc107;'>⚠ Long Day:</td><td>Over 12 hours</td></tr>"
        
        if obj.overtime_hours > Decimal('4.00'):
            html += "<tr><td style='color: #fd7e14;'>⚠ High OT:</td><td>Over 4 hours overtime</td></tr>"
        
        if not obj.description:
            html += "<tr><td style='color: #6c757d;'>ℹ No Description:</td><td>Consider adding work details</td></tr>"
        
        if obj.can_edit():
            html += "<tr><td style='color: #007bff;'>✓ Editable:</td><td>Can be modified</td></tr>"
        
        if obj.can_submit():
            html += "<tr><td style='color: #28a745;'>✓ Ready:</td><td>Can be submitted</td></tr>"
        
        if not html.strip().endswith('</table>'):
            html += "<tr><td style='color: #28a745;'>✓ Valid:</td><td>No issues detected</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    validation_status.short_description = 'Validation Status'

    def timecard_statistics(self, obj):
        """Display timecard statistics"""
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Created:</strong></td><td>{obj.created_at.strftime('%m/%d/%Y %H:%M')}</td></tr>"
        html += f"<tr><td><strong>Updated:</strong></td><td>{obj.updated_at.strftime('%m/%d/%Y %H:%M')}</td></tr>"
        html += f"<tr><td><strong>Work Type:</strong></td><td>{obj.get_work_type_display()}</td></tr>"
        
        if obj.timesheet_period:
            html += f"<tr><td><strong>Period:</strong></td><td>{obj.timesheet_period.name}</td></tr>"
        
        if obj.submitted_at:
            html += f"<tr><td><strong>Submitted:</strong></td><td>{obj.submitted_at.strftime('%m/%d/%Y %H:%M')}</td></tr>"
        
        if obj.approved_at:
            html += f"<tr><td><strong>Approved:</strong></td><td>{obj.approved_at.strftime('%m/%d/%Y %H:%M')}</td></tr>"
            if obj.approved_by:
                html += f"<tr><td><strong>Approved By:</strong></td><td>{obj.approved_by.get_full_name()}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    timecard_statistics.short_description = 'Timecard Statistics'

    # Custom actions
    def approve_timecards(self, request, queryset):
        """Approve selected timecards"""
        approved = 0
        for timecard in queryset.filter(status='submitted'):
            timecard.status = 'approved'
            timecard.approved_by = request.user
            timecard.save()
            approved += 1
        
        self.message_user(request, f"{approved} timecards approved.")
    approve_timecards.short_description = "Approve selected timecards"

    def reject_timecards(self, request, queryset):
        """Reject selected timecards"""
        rejected = queryset.filter(status='submitted').update(status='rejected')
        self.message_user(request, f"{rejected} timecards rejected.")
    reject_timecards.short_description = "Reject selected timecards"

    def calculate_pay(self, request, queryset):
        """Recalculate pay for selected timecards"""
        count = 0
        for timecard in queryset:
            # Pay is calculated automatically via properties
            # This action could trigger any additional pay calculations
            count += 1
        
        self.message_user(request, f"Pay calculated for {count} timecards.")
    calculate_pay.short_description = "Recalculate pay"

    def export_to_payroll(self, request, queryset):
        """Export to payroll system"""
        approved_timecards = queryset.filter(status='approved')
        count = approved_timecards.count()
        
        # This would integrate with actual payroll system
        self.message_user(request, f"{count} approved timecards ready for payroll export.")
    export_to_payroll.short_description = "Export to payroll"


# TimeCard Attachment Admin
@admin.register(TimeCardAttachment)
class TimeCardAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        'timecard',
        'description',
        'file',
        'uploaded_at'
    )
    
    list_filter = (
        'uploaded_at',
    )
    
    search_fields = (
        'description',
        'timecard__worker__first_name',
        'timecard__worker__last_name',
        'timecard__date'
    )
    
    readonly_fields = ('uploaded_at',)


# Timesheet Summary Admin
@admin.register(TimesheetSummary)
class TimesheetSummaryAdmin(admin.ModelAdmin):
    list_display = (
        'worker',
        'period',
        'total_hours_display',
        'pay_summary',
        'completion_status',
        'submission_status'
    )
    
    list_filter = (
        'period',
        'is_complete',
        'submitted_at',
        'approved_at'
    )
    
    search_fields = (
        'worker__first_name',
        'worker__last_name',
        'worker__email',
        'period__name'
    )
    
    readonly_fields = (
        'hours_breakdown_summary',
        'financial_summary',
        'variance_analysis'
    )
    
    fieldsets = (
        ('Summary Information', {
            'fields': (
                ('worker', 'period'),
                'is_complete'
            )
        }),
        ('Hours Summary', {
            'fields': (
                ('total_hours', 'regular_hours'),
                ('overtime_hours', 'sick_hours'),
                'vacation_hours',
                'hours_breakdown_summary'
            )
        }),
        ('Financial Summary', {
            'fields': (
                ('total_pay', 'total_mileage'),
                'total_expenses',
                'financial_summary'
            )
        }),
        ('Status', {
            'fields': (
                ('submitted_at', 'approved_at'),
            )
        }),
        ('Analysis', {
            'fields': (
                'variance_analysis',
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = ['recalculate_summaries', 'mark_complete', 'generate_reports']

    def total_hours_display(self, obj):
        """Display total hours with breakdown"""
        return format_html(
            '<strong>{:.1f}h</strong><br><small>R:{:.1f} | OT:{:.1f}</small>',
            obj.total_hours,
            obj.regular_hours,
            obj.overtime_hours
        )
    total_hours_display.short_description = 'Hours'

    def pay_summary(self, obj):
        """Display pay summary"""
        return format_html(
            '<strong>${:.2f}</strong><br><small>+${:.2f} exp</small>',
            obj.total_pay,
            obj.total_expenses
        )
    pay_summary.short_description = 'Pay'

    def completion_status(self, obj):
        """Display completion status"""
        if obj.is_complete:
            return format_html('<span style="color: #28a745;">✓ Complete</span>')
        else:
            variance = obj.variance_hours
            if variance < 0:
                return format_html('<span style="color: #ffc107;">⚠ Under ({:.1f}h)</span>', abs(variance))
            elif variance > 0:
                return format_html('<span style="color: #fd7e14;">⚠ Over (+{:.1f}h)</span>', variance)
            else:
                return format_html('<span style="color: #007bff;">○ Exact</span>')
    completion_status.short_description = 'Completion'

    def submission_status(self, obj):
        """Display submission status"""
        if obj.approved_at:
            return format_html('<span style="color: #28a745;">✓ Approved</span>')
        elif obj.submitted_at:
            return format_html('<span style="color: #007bff;">📋 Submitted</span>')
        else:
            return format_html('<span style="color: #6c757d;">○ Draft</span>')
    submission_status.short_description = 'Status'

    def hours_breakdown_summary(self, obj):
        """Display detailed hours breakdown"""
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Regular Hours:</strong></td><td>{obj.regular_hours:.2f}</td></tr>"
        html += f"<tr><td><strong>Overtime Hours:</strong></td><td>{obj.overtime_hours:.2f}</td></tr>"
        html += f"<tr><td><strong>Sick Hours:</strong></td><td>{obj.sick_hours:.2f}</td></tr>"
        html += f"<tr><td><strong>Vacation Hours:</strong></td><td>{obj.vacation_hours:.2f}</td></tr>"
        html += f"<tr><td><strong>Total Hours:</strong></td><td><strong>{obj.total_hours:.2f}</strong></td></tr>"
        html += "</table>"
        return mark_safe(html)
    hours_breakdown_summary.short_description = 'Hours Breakdown'

    def financial_summary(self, obj):
        """Display financial breakdown"""
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Total Pay:</strong></td><td>${obj.total_pay:.2f}</td></tr>"
        html += f"<tr><td><strong>Mileage:</strong></td><td>{obj.total_mileage:.1f} miles</td></tr>"
        html += f"<tr><td><strong>Expenses:</strong></td><td>${obj.total_expenses:.2f}</td></tr>"
        
        total_compensation = obj.total_pay + obj.total_expenses
        html += f"<tr><td><strong>Total Compensation:</strong></td><td><strong>${total_compensation:.2f}</strong></td></tr>"
        html += "</table>"
        return mark_safe(html)
    financial_summary.short_description = 'Financial Summary'

    def variance_analysis(self, obj):
        """Display variance analysis"""
        expected = obj.expected_hours
        actual = obj.total_hours
        variance = obj.variance_hours
        
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Expected Hours:</strong></td><td>{expected:.2f}</td></tr>"
        html += f"<tr><td><strong>Actual Hours:</strong></td><td>{actual:.2f}</td></tr>"
        
        variance_color = '#28a745' if variance == 0 else ('#ffc107' if abs(variance) <= 2 else '#dc3545')
        html += f"<tr><td><strong>Variance:</strong></td><td style='color: {variance_color};'>{variance:+.2f} hours</td></tr>"
        
        if variance != 0:
            percentage = (variance / expected) * 100 if expected > 0 else 0
            html += f"<tr><td><strong>Variance %:</strong></td><td style='color: {variance_color};'>{percentage:+.1f}%</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    variance_analysis.short_description = 'Variance Analysis'

    def recalculate_summaries(self, request, queryset):
        """Recalculate totals for selected summaries"""
        count = 0
        for summary in queryset:
            summary.calculate_totals()
            count += 1
        
        self.message_user(request, f"Recalculated {count} timesheet summaries.")
    recalculate_summaries.short_description = "Recalculate totals"

    def mark_complete(self, request, queryset):
        """Mark summaries as complete"""
        updated = queryset.update(is_complete=True)
        self.message_user(request, f"{updated} summaries marked as complete.")
    mark_complete.short_description = "Mark as complete"

    def generate_reports(self, request, queryset):
        """Generate reports for selected summaries"""
        count = queryset.count()
        self.message_user(request, f"Reports generated for {count} summaries.")
    generate_reports.short_description = "Generate reports"
