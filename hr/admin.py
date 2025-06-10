# hr/admin.py - Fixed HR Management Admin Interface

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django import forms

from .models import (
    Worker, JobPosition, TimeOffRequest, Clearance, Certification,
    WorkerClearance, WorkerCertification, PerformanceReview
)

# Custom forms for Worker
class WorkerCreationForm(forms.ModelForm):
    """A form for creating new workers. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = Worker
        fields = ('email', 'first_name', 'last_name')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        worker = super().save(commit=False)
        worker.set_password(self.cleaned_data["password1"])
        if commit:
            worker.save()
        return worker

class WorkerChangeForm(forms.ModelForm):
    """A form for updating workers. Includes all the fields on
    the worker, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = Worker
        fields = ('email', 'password', 'first_name', 'last_name', 'is_active', 'is_admin')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]

# Fixed TimeOff Inline
class TimeoffInline(admin.TabularInline):
    """Inline admin for worker TimeOffRequest requests"""
    model = TimeOffRequest
    fk_name = 'worker'  # Specify which FK to use (not 'approved_by')
    extra = 0
    fields = (
        'start_date', 'end_date', 'time_off_type', 'reason', 'is_paid', 
        'approval_status'
    )
    readonly_fields = ('created_at',)

# Main Worker Admin - FIXED
@admin.register(Worker)
class WorkerAdmin(BaseUserAdmin):
    # Override inherited filter_horizontal from BaseUserAdmin
    filter_horizontal = ()  # Empty tuple - Worker model doesn't have groups/permissions
    
    # The forms to add and change worker instances
    form = WorkerChangeForm
    add_form = WorkerCreationForm

    list_display = (
        'email',
        'full_name_display',
        'employee_id',
        'position_display',
        'compensation_display',
        'department_display',
        'hire_date_display',
        'status_indicator',
        'profile_image_preview'
    )

    list_filter = (
        'is_staff',
        'is_admin',
        'is_active',
        'date_of_hire',
        'department',
        'office',
        'company',
        'employment_status',
        'position'
    )

    search_fields = (
        'email',
        'first_name',
        'last_name',
        'employee_id',
        'phone_number'
    )

    readonly_fields = (
        'password',
        'full_name_display',
        'age_display',
        'tenure_display',
        'compensation_analysis',
        'clearance_summary',
        'certificate_summary',
        'timeoff_summary',
        'profile_image_preview',
        'resume_preview',
        'worker_statistics'
    )

    date_hierarchy = 'date_of_hire'

    fieldsets = (
        ('Authentication', {
            'fields': (
                'email',
                'password'
            )
        }),
        ('Personal Information', {
            'fields': (
                ('first_name', 'last_name'),
                'middle_name',
                'preferred_name',
                'full_name_display',
                ('date_of_birth', 'age_display'),
                'bio',
                ('profile_picture', 'profile_image_preview'),
                ('resume', 'resume_preview'),
                'phone_number',
                'emergency_contact_name',
                'emergency_contact_phone',
                'emergency_contact_relationship'
            )
        }),
        ('Employment Details', {
            'fields': (
                'employee_id',
                'position',
                ('date_of_hire', 'tenure_display'),
                'company',
                'department',
                'office',
                'manager',
                'employment_status',
                'date_of_termination'
            )
        }),
        ('Compensation', {
            'fields': (
                ('current_annual_salary', 'current_hourly_rate'),
                'compensation_analysis'
            )
        }),
        ('Professional Information', {
            'fields': (
                'skills',
                'roles'
            ),
            'classes': ('collapse',)
        }),
        ('Qualifications', {
            'fields': (
                'clearance_summary',
                'certificate_summary'
            ),
            'classes': ('collapse',)
        }),
        ('Permissions & Roles', {
            'fields': (
                'is_active',
                'is_staff',
                'is_admin',
                'is_superuser'
            )
        }),
        ('Time Off', {
            'fields': (
                'timeoff_summary',
            ),
            'classes': ('collapse',)
        }),
        ('Custom Data', {
            'fields': (
                'custom_fields',
            ),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': (
                'worker_statistics',
            ),
            'classes': ('collapse',)
        })
    )

    inlines = [TimeoffInline]

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    # Note: Worker model doesn't have groups/user_permissions fields
    # If you need these, your Worker model should extend User model
    # filter_horizontal = ('groups', 'user_permissions',)

    actions = [
        'activate_workers',
        'deactivate_workers',
        'generate_payroll_report',
        'send_welcome_email'
    ]

    # Custom display methods
    def full_name_display(self, obj):
        """Display full name with email fallback"""
        if obj.first_name and obj.last_name:
            return format_html(
                '<strong>{} {}</strong><br><small style="color: #666;">{}</small>',
                obj.first_name, obj.last_name, obj.email
            )
        return obj.email
    full_name_display.short_description = 'Worker'

    def position_display(self, obj):
        """Display position with compensation info"""
        if obj.position:
            pay_info = ""
            if obj.current_hourly_rate is not None and obj.current_hourly_rate > 0:
                pay_info = f"${float(obj.current_hourly_rate):,.2f}/hr"
            elif obj.current_annual_salary is not None and obj.current_annual_salary > 0:
                pay_info = f"${float(obj.current_annual_salary):,.0f}/yr"
            # Only return HTML if pay_info is not empty
            if pay_info:
                return format_html(
                    '<strong>{}</strong><br><small style="color: #666;">{}</small>',
                    obj.position.title,
                    pay_info
                )
            else:
                return obj.position.title
        return "No position assigned"
    position_display.short_description = 'Position'

    def compensation_display(self, obj):
        salary = obj.current_annual_salary
        hourly = obj.current_hourly_rate
        if salary is not None and float(salary) > 0:
            return f"${float(salary):,.0f} Salary"
        elif hourly is not None and float(hourly) > 0:
            return f"${float(hourly):,.2f}/hr Hourly"
        return "Not set"
    compensation_display.short_description = 'Compensation'

    def department_display(self, obj):
        """Display department"""
        if obj.department:
            return obj.department.name
        return "No department"
    department_display.short_description = 'Department'

    def hire_date_display(self, obj):
        """Display hire date with tenure"""
        if obj.date_of_hire:
            return format_html(
                '{}<br><small style="color: #666;">{}</small>',
                obj.date_of_hire.strftime('%m/%d/%Y'),
                f"{obj.years_of_service:.1f} years" if obj.years_of_service else ""
            )
        return "Not set"
    hire_date_display.short_description = 'Hire Date'

    def status_indicator(self, obj):
        """Display worker status"""
        if not obj.is_active:
            return format_html('<span style="color: #dc3545;">● Inactive</span>')
        elif obj.is_admin:
            return format_html('<span style="color: #28a745;">● Admin</span>')
        elif obj.is_staff:
            return format_html('<span style="color: #007bff;">● Staff</span>')
        else:
            return format_html('<span style="color: #28a745;">● Active</span>')
    status_indicator.short_description = 'Status'

    def profile_image_preview(self, obj):
        """Display profile image preview"""
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />',
                obj.profile_picture.url
            )
        return format_html('<div style="width: 40px; height: 40px; border-radius: 50%; background-color: #e9ecef; display: flex; align-items: center; justify-content: center; color: #6c757d; font-size: 12px;">No Photo</div>')
    profile_image_preview.short_description = 'Photo'

    def age_display(self, obj):
        """Calculate and display age"""
        age = obj.age
        if age:
            return f"{age} years old"
        return "Not provided"
    age_display.short_description = 'Age'

    def tenure_display(self, obj):
        """Calculate and display tenure"""
        years = obj.years_of_service
        if years > 0:
            return f"{years:.1f} years"
        return "New hire"
    tenure_display.short_description = 'Tenure'

    def compensation_analysis(self, obj):
        """Display compensation analysis"""
        html = "<table style='font-size: 12px;'>"
        
        if obj.current_annual_salary and obj.current_annual_salary > 0:
            html += f"<tr><td><strong>Salary:</strong></td><td>${obj.current_annual_salary:,.0f}/year</td></tr>"
            html += f"<tr><td><strong>Monthly:</strong></td><td>${obj.current_annual_salary/12:,.0f}</td></tr>"
        
        if obj.current_hourly_rate and obj.current_hourly_rate > 0:
            html += f"<tr><td><strong>Hourly:</strong></td><td>${obj.current_hourly_rate}/hour</td></tr>"
            html += f"<tr><td><strong>Annual (40hr/wk):</strong></td><td>${obj.current_hourly_rate * 40 * 52:,.0f}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    compensation_analysis.short_description = 'Compensation Analysis'

    def clearance_summary(self, obj):
        """Display clearance summary"""
        clearances = obj.current_clearances
        if clearances:
            html = "<ul style='margin: 0; padding-left: 15px; font-size: 12px;'>"
            for clearance in clearances:
                html += f"<li>{clearance.clearance.name}</li>"
            html += "</ul>"
            return mark_safe(html)
        return "No clearances"
    clearance_summary.short_description = 'Security Clearances'

    def certificate_summary(self, obj):
        """Display Certification summary"""
        certs = obj.current_certifications
        if certs:
            html = "<ul style='margin: 0; padding-left: 15px; font-size: 12px;'>"
            for cert in certs:
                html += f"<li>{cert.certification.name}</li>"
            html += "</ul>"
            return mark_safe(html)
        return "No certificates"
    certificate_summary.short_description = 'Certificates'

    def timeoff_summary(self, obj):
        """Display TimeOffRequest summary"""
        recent_request = obj.time_off_requests.order_by('-created_at').first()
        if recent_request:
            status_color = '#28a745' if recent_request.approval_status == 'approved' else '#ffc107'
            return format_html(
                'Latest: {} to {}<br><span style="color: {};">{}</span>',
                recent_request.start_date.strftime('%m/%d/%Y'),
                recent_request.end_date.strftime('%m/%d/%Y'),
                status_color, 
                recent_request.get_approval_status_display()
            )
        return "No time off requests"
    timeoff_summary.short_description = 'Time Off Status'

    def resume_preview(self, obj):
        """Display resume download link"""
        if obj.resume:
            return format_html(
                '<a href="{}" target="_blank">📄 View Resume</a>',
                obj.resume.url
            )
        return "No resume uploaded"
    resume_preview.short_description = 'Resume'

    def worker_statistics(self, obj):
        """Display comprehensive worker statistics"""
        html = "<table style='font-size: 12px;'>"
        
        html += f"<tr><td><strong>Employee ID:</strong></td><td>{obj.employee_id}</td></tr>"
        html += f"<tr><td><strong>Email:</strong></td><td>{obj.email}</td></tr>"
        html += f"<tr><td><strong>Phone:</strong></td><td>{obj.phone_number or 'Not provided'}</td></tr>"
        html += f"<tr><td><strong>Company:</strong></td><td>{obj.company.company_name if obj.company else 'Not assigned'}</td></tr>"
        
        if obj.primary_address:
            html += f"<tr><td><strong>Address:</strong></td><td>{obj.primary_address}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    worker_statistics.short_description = 'Worker Statistics'

    # Custom actions
    def activate_workers(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} workers activated.")
    activate_workers.short_description = "Activate selected workers"

    def deactivate_workers(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} workers deactivated.")
    deactivate_workers.short_description = "Deactivate selected workers"

    def generate_payroll_report(self, request, queryset):
        count = queryset.filter(is_active=True).count()
        self.message_user(request, f"Payroll report generated for {count} active workers.")
    generate_payroll_report.short_description = "Generate payroll report"

    def send_welcome_email(self, request, queryset):
        count = queryset.filter(is_active=True).count()
        self.message_user(request, f"Welcome emails queued for {count} workers.")
    send_welcome_email.short_description = "Send welcome emails"

    ordering = ['first_name', 'last_name']

# JobPosition Admin - FIXED
@admin.register(JobPosition)
class PositionPayAdmin(admin.ModelAdmin):
    list_display = (
        'title',  # FIXED: was 'name'
        'department',
        'compensation_type',
        'compensation_display',
        'workers_assigned',
        'clearance_count',
        'certificate_count'
    )

    list_filter = (
        'compensation_type',  # FIXED: was 'hors'
        'employment_type',
        'job_level',
        'is_active'
    )

    search_fields = (
        'title',
        'position_code',
        'description'
    )

    fieldsets = (
        ('Position Information', {
            'fields': (
                'title',
                'position_code',
                'department',
                'description',
                'responsibilities',
                'requirements'
            )
        }),
        ('Compensation', {
            'fields': (
                'compensation_type',
                'min_hourly_rate',
                'max_hourly_rate',
                'min_annual_salary',
                'max_annual_salary'
            )
        }),
        ('Employment Details', {
            'fields': (
                'employment_type',
                'job_level',
                'reports_to',
                'is_billable'
            )
        }),
        ('Requirements', {
            'fields': (
                'required_clearances',
                'required_certifications'
            )
        })
    )


    def compensation_display(self, obj):
        """Display compensation information (plain string, no HTML)"""
        if obj.compensation_type == 'hourly':
            if obj.min_hourly_rate and obj.max_hourly_rate:
                return "${:.2f} - ${:.2f}/hr".format(
                    float(obj.min_hourly_rate), float(obj.max_hourly_rate)
                )
        elif obj.compensation_type == 'salary':
            if obj.min_annual_salary and obj.max_annual_salary:
                return "${:,.0f} - ${:,.0f}/year".format(
                    float(obj.min_annual_salary), float(obj.max_annual_salary)
                )
        return "Not configured"
    compensation_display.short_description = 'Compensation Range'

    def workers_assigned(self, obj):
        """Count of workers in this position"""
        count = obj.current_employees
        if count > 0:
            url = reverse('admin:hr_worker_changelist') + f'?position__id__exact={obj.id}'
            return format_html('<a href="{}">{} workers</a>', url, count)
        return "0 workers"
    workers_assigned.short_description = 'Workers'

    def clearance_count(self, obj):
        """Count of required clearances"""
        return obj.required_clearances.count()
    clearance_count.short_description = 'Clearances'

    def certificate_count(self, obj):
        """Count of required certificates"""
        return obj.required_certifications.count()
    certificate_count.short_description = 'Certificates'

# TimeOffRequest Admin - FIXED
@admin.register(TimeOffRequest)
class TimeoffAdmin(admin.ModelAdmin):
    list_display = (
        'worker',  # FIXED: correct field name
        'date_range_display',
        'time_off_type',
        'days_requested',
        'pay_status',
        'approval_status_display',
        'created_at'
    )

    list_filter = (
        'approval_status',  # FIXED: was 'approved'
        'is_paid',         # FIXED: was 'paidtime'
        'time_off_type',   # FIXED: was 'timeoff_req'
        'start_date',      # FIXED: was 'from_req'
        'end_date',        # FIXED: was 'to_req'
        'created_at'
    )

    search_fields = (
        'worker__first_name',
        'worker__last_name',
        'worker__email',
        'reason'
    )

    readonly_fields = (
        'created_at',  # FIXED: was 'timeoff_req'
        'updated_at',
        'duration_days'
    )

    fieldsets = (
        ('Request Information', {
            'fields': (
                'worker',
                'time_off_type',
                'created_at'
            )
        }),
        ('Time Off Details', {
            'fields': (
                ('start_date', 'end_date'),
                'duration_days',
                'reason',
                'is_paid'
            )
        }),
        ('Approval', {
            'fields': (
                'approval_status',
                'approved_by',
                'approved_date',
                'manager_notes'
            )
        })
    )

    def date_range_display(self, obj):
        """Display date range"""
        return format_html(
            '{} to {}',
            obj.start_date.strftime('%m/%d/%Y'),
            obj.end_date.strftime('%m/%d/%Y')
        )
    date_range_display.short_description = 'Date Range'

    def days_requested(self, obj):
        """Calculate days requested"""
        return f"{obj.duration_days} day{'s' if obj.duration_days != 1 else ''}"
    days_requested.short_description = 'Duration'

    def pay_status(self, obj):
        """Display pay status"""
        if obj.is_paid:
            return format_html('<span style="color: #28a745;">💰 Paid</span>')
        else:
            return format_html('<span style="color: #6c757d;">🚫 Unpaid</span>')
    pay_status.short_description = 'Pay Status'

    def approval_status_display(self, obj):
        """Display approval status"""
        colors = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'denied': '#dc3545',
            'cancelled': '#6c757d'
        }
        color = colors.get(obj.approval_status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_approval_status_display()
        )
    approval_status_display.short_description = 'Status'

# Clearance Admin - FIXED
@admin.register(Clearance)
class ClearanceAdmin(admin.ModelAdmin):
    list_display = (
        'name',  # FIXED: was 'clearances'
        'clearance_code',
        'clearance_level',
        'issuing_authority',
        'workers_with_clearance',
        'positions_requiring'
    )

    search_fields = ('name', 'clearance_code', 'issuing_authority')

    def workers_with_clearance(self, obj):
        """Count workers with this clearance"""
        count = obj.workers.count()
        if count > 0:
            url = reverse('admin:hr_worker_changelist') + f'?clearances__id__exact={obj.id}'
            return format_html('<a href="{}">{} workers</a>', url, count)
        return "0 workers"
    workers_with_clearance.short_description = 'Workers'

    def positions_requiring(self, obj):
        """Count positions requiring this clearance"""
        count = obj.required_for_positions.count()
        if count > 0:
            url = reverse('admin:hr_jobposition_changelist') + f'?required_clearances__id__exact={obj.id}'
            return format_html('<a href="{}">{} positions</a>', url, count)
        return "0 positions"
    positions_requiring.short_description = 'Required By'

# Certification Admin - FIXED
@admin.register(Certification)
class CertificateAdmin(admin.ModelAdmin):
    list_display = (
        'name',  # FIXED: was 'certificates'
        'certification_code',
        'issuing_organization',
        'workers_with_certificate',
        'positions_requiring'
    )

    search_fields = ('name', 'certification_code', 'issuing_organization')

    def workers_with_certificate(self, obj):
        """Count workers with this Certification"""
        count = obj.workers.count()
        if count > 0:
            url = reverse('admin:hr_worker_changelist') + f'?certifications__id__exact={obj.id}'
            return format_html('<a href="{}">{} workers</a>', url, count)
        return "0 workers"
    workers_with_certificate.short_description = 'Workers'

    def positions_requiring(self, obj):
        """Count positions requiring this Certification"""
        count = obj.required_for_positions.count()
        if count > 0:
            url = reverse('admin:hr_jobposition_changelist') + f'?required_certifications__id__exact={obj.id}'
            return format_html('<a href="{}">{} positions</a>', url, count)
        return "0 positions"
    positions_requiring.short_description = 'Required By'