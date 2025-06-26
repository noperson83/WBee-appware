# company/admin.py - Modern Admin Interface for Company Management

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from django.utils import timezone

from .models import Company, Office, Department, CompanySettings
from client.models import Address, Contact

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

class OfficeInline(admin.TabularInline):
    """Inline admin for offices"""
    model = Office
    extra = 0
    fields = (
        'office_name', 'office_code', 'office_type', 
        'employee_capacity', 'office_manager', 'is_active'
    )
    readonly_fields = ('employee_count_display', 'created_at')
    
    def employee_count_display(self, obj):
        if obj.pk:
            return f"{obj.employee_count} employees"
        return "—"
    employee_count_display.short_description = 'Employees'

class DepartmentInline(admin.TabularInline):
    """Inline admin for departments"""
    model = Department
    extra = 0
    fields = (
        'name', 'department_code', 'department_head', 
        'annual_budget', 'is_billable', 'is_active'
    )
    readonly_fields = ('employee_count_display', 'created_at')
    
    def employee_count_display(self, obj):
        if obj.pk:
            return f"{obj.employee_count} employees"
        return "—"
    employee_count_display.short_description = 'Employees'

class SubsidiaryInline(admin.TabularInline):
    """Inline admin for subsidiary companies"""
    model = Company
    fk_name = 'parent_company'
    extra = 0
    fields = (
        'company_name', 'business_category', 'primary_contact_name', 
        'is_active'
    )
    readonly_fields = ('total_employees_display',)
    
    def total_employees_display(self, obj):
        if obj.pk:
            return f"{obj.total_employees} employees"
        return "—"
    total_employees_display.short_description = 'Employees'

# Main Company Admin
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        'company_name',
        'business_category_display',
        'business_type',
        'total_locations_display',
        'total_employees_display',
        'revenue_growth_display',
        'is_multi_location',
        'is_active'
    )

    list_filter = (
        'business_type',
        'business_category',
        'is_multi_location',
        'is_active',
        'timezone',
        'currency',
        'created_at'
    )

    search_fields = (
        'company_name',
        'legal_name',
        'description',
        'primary_contact_name',
        'primary_email',
        'tax_id'
    )

    readonly_fields = (
        'id',
        'total_locations',
        'total_departments',
        'total_employees',
        'revenue_growth',
        'logo_preview',
        'button_image_preview',
        'company_statistics',
        'subsidiary_tree',
        'created_at',
        'updated_at'
    )

    fieldsets = (
        ('Company Information', {
            'fields': (
                'company_name',
                'legal_name',
                'company_url',
                'business_config',
                'business_category',
                'business_type'
            )
        }),
        ('Visual Branding', {
            'fields': (
                ('logo', 'logo_preview'),
                ('button_image', 'button_image_preview'),
                'brand_colors'
            ),
            'classes': ('collapse',)
        }),
        ('Primary Contact', {
            'fields': (
                'primary_contact_name',
                'primary_contact_title',
                'primary_phone',
                'primary_email'
            )
        }),
        ('Business Details', {
            'fields': (
                'description',
                'mission_statement',
                'founded_date'
            )
        }),
        ('Legal & Tax Information', {
            'fields': (
                'tax_id',
                'business_license'
            ),
            'classes': ('collapse',)
        }),
        ('Financial Information', {
            'fields': (
                'current_year_revenue',
                'previous_year_revenue',
                'revenue_growth'
            ),
            'classes': ('collapse',)
        }),
        ('Company Structure', {
            'fields': (
                'is_multi_location',
                'parent_company',
                'subsidiary_tree'
            ),
            'classes': ('collapse',)
        }),
        ('System Settings', {
            'fields': (
                'timezone',
                'currency',
                'fiscal_year_start',
                'default_payment_terms'
            ),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': (
                'total_locations',
                'total_departments', 
                'total_employees',
                'company_statistics'
            ),
            'classes': ('collapse',)
        }),
        ('Custom Data', {
            'fields': (
                'custom_fields',
            ),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': (
                'id',
                'is_active',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    inlines = [AddressInline, ContactInline, OfficeInline, DepartmentInline, SubsidiaryInline]

    actions = ['activate_companies', 'deactivate_companies', 'setup_default_data']

    # Custom display methods
    def business_category_display(self, obj):
        if obj.business_category:
            return format_html(
                '<span style="color: {}; font-weight: bold;"><i class="{}"></i> {}</span>',
                obj.business_category.color,
                obj.business_category.icon,
                obj.business_category.name
            )
        return "—"
    business_category_display.short_description = 'Business Category'

    def total_locations_display(self, obj):
        count = obj.total_locations
        if count > 0:
            url = reverse('admin:company_office_changelist') + f'?company__id__exact={obj.id}'
            return format_html('<a href="{}">{} locations</a>', url, count)
        return "0 locations"
    total_locations_display.short_description = 'Locations'

    def total_employees_display(self, obj):
        count = obj.total_employees
        if count > 0:
            # This would link to HR admin when available
            return f"{count} employees"
        return "0 employees"
    total_employees_display.short_description = 'Employees'

    def revenue_growth_display(self, obj):
        growth = obj.revenue_growth
        if growth > 0:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">+{:.1f}%</span>',
                growth
            )
        elif growth < 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">{:.1f}%</span>',
                growth
            )
        else:
            return "0%"
    revenue_growth_display.short_description = 'Growth'

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.logo.url
            )
        return "No logo"
    logo_preview.short_description = 'Logo Preview'

    def button_image_preview(self, obj):
        if obj.button_image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.button_image.url
            )
        return "No button image"
    button_image_preview.short_description = 'Button Preview'

    def company_statistics(self, obj):
        """Display comprehensive company statistics"""
        try:
            # Calculate some basic stats
            offices = obj.offices.filter(is_active=True)
            departments = obj.departments.filter(is_active=True)
            
            html = "<table style='font-size: 12px;'>"
            html += f"<tr><td><strong>Active Offices:</strong></td><td>{offices.count()}</td></tr>"
            html += f"<tr><td><strong>Active Departments:</strong></td><td>{departments.count()}</td></tr>"
            html += f"<tr><td><strong>Total Employees:</strong></td><td>{obj.total_employees}</td></tr>"
            
            if obj.current_year_revenue:
                html += f"<tr><td><strong>Current Year Revenue:</strong></td><td>${obj.current_year_revenue:,.2f}</td></tr>"
            
            if obj.previous_year_revenue:
                html += f"<tr><td><strong>Previous Year Revenue:</strong></td><td>${obj.previous_year_revenue:,.2f}</td></tr>"
            
            if obj.revenue_growth:
                color = '#28a745' if obj.revenue_growth > 0 else '#dc3545'
                html += f"<tr><td><strong>Revenue Growth:</strong></td><td><span style='color: {color};'>{obj.revenue_growth:.1f}%</span></td></tr>"
            
            # Subsidiary information
            if obj.has_subsidiaries:
                html += f"<tr><td><strong>Subsidiaries:</strong></td><td>{obj.subsidiaries.count()}</td></tr>"
            
            if obj.is_subsidiary:
                html += f"<tr><td><strong>Parent Company:</strong></td><td>{obj.parent_company.company_name}</td></tr>"
            
            html += "</table>"
            return mark_safe(html)
        except:
            return "Statistics unavailable"
    company_statistics.short_description = 'Company Statistics'

    def subsidiary_tree(self, obj):
        """Display subsidiary structure"""
        if obj.has_subsidiaries:
            html = "<div style='font-size: 12px;'>"
            html += "<strong>Subsidiaries:</strong><ul>"
            for subsidiary in obj.subsidiaries.all():
                status = "✓" if subsidiary.is_active else "✗"
                html += f"<li>{status} {subsidiary.company_name}</li>"
            html += "</ul></div>"
            return mark_safe(html)
        elif obj.is_subsidiary:
            return format_html(
                "<div style='font-size: 12px;'><strong>Parent:</strong> {}</div>",
                obj.parent_company.company_name
            )
        return "No subsidiaries"
    subsidiary_tree.short_description = 'Company Structure'

    # Custom actions
    def activate_companies(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} companies activated.")
    activate_companies.short_description = "Activate selected companies"

    def deactivate_companies(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} companies deactivated.")
    deactivate_companies.short_description = "Deactivate selected companies"

    def setup_default_data(self, request, queryset):
        """Set up default departments and settings"""
        from .models import setup_default_company_data
        updated = 0
        for company in queryset:
            setup_default_company_data(company)
            updated += 1
        self.message_user(request, f"Default data setup for {updated} companies.")
    setup_default_data.short_description = "Setup default departments & settings"

# Office Admin
@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = (
        'office_name',
        'company',
        'office_type',
        'office_manager',
        'employee_count_display',
        'utilization_display',
        'is_active'
    )

    list_filter = (
        'office_type',
        'company',
        'is_active',
        'opened_date'
    )

    search_fields = (
        'office_name',
        'office_code',
        'description',
        'office_manager',
        'company__company_name'
    )

    readonly_fields = (
        'id',
        'employee_count',
        'utilization_rate',
        'created_at',
        'updated_at'
    )

    fieldsets = (
        ('Office Information', {
            'fields': (
                'company',
                'office_name',
                'office_code',
                'office_type'
            )
        }),
        ('Details', {
            'fields': (
                'description',
                'office_manager',
                'phone_number',
                'email'
            )
        }),
        ('Capacity & Logistics', {
            'fields': (
                'employee_capacity',
                'square_footage',
                'employee_count',
                'utilization_rate'
            )
        }),
        ('Operating Information', {
            'fields': (
                'operating_hours',
                'opened_date',
                'is_active'
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

    inlines = [AddressInline]

    def employee_count_display(self, obj):
        count = obj.employee_count
        if count > 0:
            # Would link to HR admin when available
            return f"{count} employees"
        return "0 employees"
    employee_count_display.short_description = 'Employees'

    def utilization_display(self, obj):
        rate = obj.utilization_rate
        if obj.employee_capacity:
            if rate >= 90:
                color = '#dc3545'  # Red - overutilized
            elif rate >= 75:
                color = '#ffc107'  # Yellow - high utilization
            else:
                color = '#28a745'  # Green - good utilization
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color, rate
            )
        return "—"
    utilization_display.short_description = 'Utilization'

# Department Admin
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'company',
        'department_hierarchy',
        'department_head',
        'employee_count_display',
        'budget_display',
        'is_billable',
        'is_active'
    )

    list_filter = (
        'company',
        'is_billable',
        'is_active',
        'parent_department'
    )

    search_fields = (
        'name',
        'department_code',
        'description',
        'department_head',
        'company__company_name'
    )

    readonly_fields = (
        'id',
        'employee_count',
        'is_sub_department',
        'has_sub_departments',
        'full_department_path',
        'created_at',
        'updated_at'
    )

    fieldsets = (
        ('Department Information', {
            'fields': (
                'company',
                'name',
                'department_code',
                'description'
            )
        }),
        ('Hierarchy', {
            'fields': (
                'parent_department',
                'full_department_path',
                'is_sub_department',
                'has_sub_departments'
            )
        }),
        ('Management', {
            'fields': (
                'department_head',
                'primary_office',
                'employee_count'
            )
        }),
        ('Financial', {
            'fields': (
                'annual_budget',
                'cost_center_code',
                'is_billable'
            ),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': (
                'id',
                'is_active',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def department_hierarchy(self, obj):
        """Show department hierarchy"""
        if obj.parent_department:
            return format_html(
                '<span style="color: #6c757d;">{}</span> → <strong>{}</strong>',
                obj.parent_department.name, obj.name
            )
        elif obj.has_sub_departments:
            return format_html('<strong>{}</strong> (has {} sub-depts)', obj.name, obj.sub_departments.count())
        else:
            return obj.name
    department_hierarchy.short_description = 'Hierarchy'

    def employee_count_display(self, obj):
        count = obj.employee_count
        if count > 0:
            return f"{count} employees"
        return "0 employees"
    employee_count_display.short_description = 'Employees'

    def budget_display(self, obj):
        if obj.annual_budget:
            return f"${obj.annual_budget:,.2f}"
        return "—"
    budget_display.short_description = 'Annual Budget'

# Company Settings Admin
@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = (
        'company',
        'invoice_prefix',
        'next_invoice_number',
        'project_prefix',
        'next_project_number'
    )

    search_fields = (
        'company__company_name',
    )

    readonly_fields = (
        'created_at',
        'updated_at'
    )

    fieldsets = (
        ('Company', {
            'fields': ('company',)
        }),
        ('Numbering Settings', {
            'fields': (
                ('invoice_prefix', 'next_invoice_number'),
                ('project_prefix', 'next_project_number')
            )
        }),
        ('Email Configuration', {
            'fields': (
                'smtp_server',
                'smtp_port',
                'smtp_username',
                'smtp_use_tls'
            ),
            'classes': ('collapse',)
        }),
        ('System Preferences', {
            'fields': (
                'date_format',
                'notification_settings'
            ),
            'classes': ('collapse',)
        }),
        ('Integrations', {
            'fields': (
                'integrations',
            ),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def has_add_permission(self, request):
        # Only allow one settings per company
        return True

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of company settings
        return False
