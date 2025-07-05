# client/admin.py - Modern Admin Interface

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from django.utils import timezone

from .models import (
    Client,
    Address,
    Contact,
    FinancialPeriod,
    Revenue,
    WIPReport,
    ProjectFinancials,
    ServiceLocation,
)

# Inline admins for related models
class AddressInline(GenericTabularInline):
    """Inline admin for addresses"""
    model = Address
    extra = 1
    fields = (
        'label', 'attention_line', 'line1', 'line2', 
        'city', 'state_province', 'postal_code', 
        'is_primary', 'is_active'
    )
    readonly_fields = ('created_at', 'updated_at')

class ContactInline(GenericTabularInline):
    """Inline admin for contacts"""
    model = Contact
    extra = 1
    fields = (
        'contact_type', 'first_name', 'last_name', 'title',
        'phone', 'email', 'is_primary', 'is_active'
    )
    readonly_fields = ('created_at', 'updated_at')

class RevenueInline(admin.TabularInline):
    """Inline admin for revenue tracking"""
    model = Revenue
    extra = 0
    fields = (
        'period', 'contract_revenue', 'service_revenue', 
        'material_revenue', 'labor_revenue', 'total_revenue_display'
    )
    readonly_fields = ('total_revenue_display', 'created_at', 'updated_at')
    
    def total_revenue_display(self, obj):
        if obj.pk:
            return f"${obj.total_revenue:,.2f}"
        return "—"
    total_revenue_display.short_description = "Total Revenue"

# Main Client Admin
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        'company_name',
        'status_badge',
        'business_type',
        'primary_contact_display',
        'primary_city_display',
        'ytd_revenue_display',
        'total_revenue_display',
        'project_count',
        'date_of_contract'
    )

    list_filter = (
        'status',
        'business_type',
        'payment_terms',
        'date_of_contact',
        'date_of_contract',
        'created_at',
    )

    search_fields = (
        'company_name',
        'tax_id',
        'contacts__first_name',
        'contacts__last_name',
        'contacts__email',
        'addresses__city',
        'addresses__state_province'
    )

    readonly_fields = (
        'id',
        'ytd_revenue',
        'total_revenue',
        'created_at',
        'updated_at',
        'logo_preview',
        'quick_stats'
    )

    date_hierarchy = 'date_of_contact'

    fieldsets = (
        ('Company Information', {
            'fields': (
                'company_name',
                'company_url',
                ('logo', 'logo_preview'),
                'business_type',
                'tax_id'
            )
        }),
        ('Client Status', {
            'fields': (
                'status',
                'date_of_contact',
                'date_of_contract',
                'payment_terms',
                'credit_limit'
            )
        }),
        ('Financial Summary', {
            'fields': (
                'ytd_revenue',
                'total_revenue',
                'quick_stats'
            ),
            'classes': ('collapse',)
        }),
        ('Notes & Custom Data', {
            'fields': (
                'summary',
                'custom_fields'
            ),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': (
                'id',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    inlines = [AddressInline, ContactInline, RevenueInline]

    actions = ['update_revenue_totals', 'mark_as_active', 'mark_as_inactive']

    # Custom display methods
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'prospect': '#FFA500',  # Orange
            'active': '#28A745',    # Green
            'inactive': '#6C757D',  # Gray
            'former': '#DC3545'     # Red
        }
        color = colors.get(obj.status, '#6C757D')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def primary_contact_display(self, obj):
        """Display primary contact"""
        contact = obj.primary_contact
        if contact:
            return f"{contact.full_name}"
        return "—"
    primary_contact_display.short_description = 'Primary Contact'

    def primary_city_display(self, obj):
        """Display primary address city/state"""
        address = obj.primary_address
        if address:
            return f"{address.city}, {address.state_province}"
        return "—"
    primary_city_display.short_description = 'Location'

    def ytd_revenue_display(self, obj):
        """Display YTD revenue with formatting"""
        if obj.ytd_revenue:
            return f"${obj.ytd_revenue:,.2f}"
        return "—"
    ytd_revenue_display.short_description = 'YTD Revenue'

    def total_revenue_display(self, obj):
        """Display total revenue with formatting"""
        if obj.total_revenue:
            return f"${obj.total_revenue:,.2f}"
        return "—"
    total_revenue_display.short_description = 'Total Revenue'

    def project_count(self, obj):
        """Display number of projects across all locations"""
        try:
            from project.models import Project
            count = Project.objects.filter(locations__client=obj).count()  # Updated relationship
            if count > 0:
                url = reverse('admin:project_project_changelist') + (
                    f'?locations__client__id__exact={obj.id}'
                )
                return format_html('<a href="{}">{} projects</a>', url, count)
            return "0 projects"
        except Exception:
            return "—"
    project_count.short_description = 'Projects'

    def logo_preview(self, obj):
        """Display logo preview"""
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.logo.url
            )
        return "No logo"
    logo_preview.short_description = 'Logo Preview'

    def quick_stats(self, obj):
        """Display quick client statistics"""
        try:
            from project.models import Project
            projects = Project.objects.filter(locations__client=obj)  # Updated relationship
            
            stats = {
                'total_projects': projects.count(),
                'active_projects': projects.exclude(status__in=['c', 'm', 'l']).count(),
                'completed_projects': projects.filter(status='c').count(),
                'total_locations': obj.locations.count(),  # Updated from jobsites
                'active_locations': obj.locations.exclude(status__in=['inactive', 'complete']).count(),
            }
            
            html = "<table style='font-size: 12px;'>"
            html += f"<tr><td><strong>Locations:</strong></td><td>{stats['active_locations']}/{stats['total_locations']}</td></tr>"
            html += f"<tr><td><strong>Total Projects:</strong></td><td>{stats['total_projects']}</td></tr>"
            html += f"<tr><td><strong>Active Projects:</strong></td><td>{stats['active_projects']}</td></tr>"
            html += f"<tr><td><strong>Completed:</strong></td><td>{stats['completed_projects']}</td></tr>"
            html += "</table>"
            
            return mark_safe(html)
        except:
            return "Statistics unavailable"
    quick_stats.short_description = 'Quick Statistics'

    # Custom actions
    def update_revenue_totals(self, request, queryset):
        """Action to recalculate revenue totals"""
        from .models import update_client_revenue_totals
        update_client_revenue_totals()
        self.message_user(request, "Revenue totals updated successfully.")
    update_revenue_totals.short_description = "Update revenue totals"

    def mark_as_active(self, request, queryset):
        """Mark selected clients as active"""
        updated = queryset.update(status='active')
        self.message_user(request, f"{updated} clients marked as active.")
    mark_as_active.short_description = "Mark as active clients"

    def mark_as_inactive(self, request, queryset):
        """Mark selected clients as inactive"""
        updated = queryset.update(status='inactive')
        self.message_user(request, f"{updated} clients marked as inactive.")
    mark_as_inactive.short_description = "Mark as inactive clients"

# Address Admin
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        'content_object',
        'label',
        'full_address',
        'is_primary',
        'is_active'
    )
    
    list_filter = (
        'label',
        'is_primary',
        'is_active',
        'country',
        'state_province'
    )
    
    search_fields = (
        'line1',
        'city',
        'state_province',
        'postal_code'
    )
    
    def full_address(self, obj):
        return f"{obj.line1}, {obj.city}, {obj.state_province} {obj.postal_code}"
    full_address.short_description = 'Address'


@admin.register(ServiceLocation)
class ServiceLocationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'client',
        'city',
        'state_province',
    )
    search_fields = (
        'name',
        'city',
        'state_province',
        'client__company_name',
    )

# Contact Admin
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'content_object',
        'contact_type',
        'email',
        'phone',
        'is_primary',
        'is_active'
    )
    
    list_filter = (
        'contact_type',
        'is_primary',
        'is_active'
    )
    
    search_fields = (
        'first_name',
        'last_name',
        'email',
        'phone'
    )

# Financial Period Admin
@admin.register(FinancialPeriod)
class FinancialPeriodAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'period_type',
        'start_date',
        'end_date',
        'is_current',
        'duration_days'
    )
    
    list_filter = (
        'period_type',
        'is_current',
        'start_date'
    )
    
    date_hierarchy = 'start_date'
    
    def duration_days(self, obj):
        return (obj.end_date - obj.start_date).days
    duration_days.short_description = 'Duration (days)'

# Revenue Admin
@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_display = (
        'client',
        'period',
        'contract_revenue',
        'service_revenue',
        'total_revenue_display',
        'created_at'
    )
    
    list_filter = (
        'period',
        'client',
        'created_at'
    )
    
    search_fields = (
        'client__company_name',
        'period__name'
    )
    
    readonly_fields = ('total_revenue_display',)
    
    def total_revenue_display(self, obj):
        return f"${obj.total_revenue:,.2f}"
    total_revenue_display.short_description = 'Total Revenue'

# WIP Report Admin
@admin.register(WIPReport)
class WIPReportAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'report_date',
        'period',
        'total_wip',
        'total_invoiced',
        'projects_installing'
    )
    
    list_filter = (
        'period',
        'report_date'
    )
    
    date_hierarchy = 'report_date'
    
    readonly_fields = (
        'total_backlog',
        'total_wip',
        'total_invoiced',
        'total_paid',
        'projects_prospecting',
        'projects_quoted',
        'projects_installing',
        'projects_complete',
        'projects_invoiced',
        'projects_paid'
    )

# Project Financials Admin
@admin.register(ProjectFinancials)
class ProjectFinancialsAdmin(admin.ModelAdmin):
    list_display = (
        'project_id',
        'percent_complete',
        'budgeted_material_cost',
        'actual_material_cost',
        'material_variance_display',
        'invoiced_to_date'
    )
    
    list_filter = (
        'percent_complete',
        'created_at'
    )
    
    search_fields = ('project_id',)
    
    readonly_fields = (
        'labor_variance_display',
        'material_variance_display'
    )
    
    def labor_variance_display(self, obj):
        variance = obj.labor_variance
        color = 'red' if variance > 0 else 'green'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, f"{variance:.2f} hours"
        )
    labor_variance_display.short_description = 'Labor Variance'
    
    def material_variance_display(self, obj):
        variance = obj.material_variance
        color = 'red' if variance > 0 else 'green'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, f"${variance:,.2f}"
        )
    material_variance_display.short_description = 'Material Variance'
