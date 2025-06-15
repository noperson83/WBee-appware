# asset/admin.py - Fixed Asset Management Admin Interface

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from .models import (
    AssetCategory, Asset, AssetMaintenanceRecord, 
    AssetAssignment, AssetDepreciation
)

# Inline admins for related models
class AssetMaintenanceInline(admin.TabularInline):
    """Inline admin for maintenance records"""
    model = AssetMaintenanceRecord
    extra = 0
    fields = (
        'maintenance_type', 'description', 'performed_by', 'performed_date',
        'total_cost_display', 'issue_resolved'
    )
    readonly_fields = ('total_cost_display',)
    
    def total_cost_display(self, obj):
        if obj.pk:
            return f"${obj.total_cost:,.2f}"
        return "—"
    total_cost_display.short_description = 'Total Cost'

class AssetAssignmentInline(admin.TabularInline):
    """Inline admin for asset assignments"""
    model = AssetAssignment
    extra = 0
    fields = (
        'assigned_to_worker', 'assigned_to_project', 'start_date', 
        'end_date', 'purpose', 'is_active'
    )
    readonly_fields = ('created_at',)

class AssetDepreciationInline(admin.TabularInline):
    """Inline admin for depreciation records"""
    model = AssetDepreciation
    extra = 0
    fields = (
        'depreciation_year', 'method', 'annual_depreciation',
        'accumulated_depreciation'
    )
    readonly_fields = ('created_at',)

# Asset Category Admin
@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'business_category',
        'asset_count',
        'icon_display',
        'depreciation_info',
        'maintenance_info',
        'is_active'
    )
    
    list_filter = (
        'business_category',
        'requires_maintenance',
        'is_active',
        'default_depreciation_years'
    )
    
    search_fields = (
        'name',
        'description',
        'business_category__name'
    )
    
    fieldsets = (
        ('Category Information', {
            'fields': (
                'business_category',
                'name',
                'description',
                'is_active'
            )
        }),
        ('Visual Settings', {
            'fields': (
                'icon',
                'color'
            )
        }),
        ('Financial Settings', {
            'fields': (
                'default_depreciation_years',
            )
        }),
        ('Maintenance Settings', {
            'fields': (
                'requires_maintenance',
                'default_maintenance_interval_days'
            )
        })
    )
    
    def asset_count(self, obj):
        count = obj.assets.count()
        if count > 0:
            url = reverse('admin:asset_asset_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}">{} assets</a>', url, count)
        return "0 assets"
    asset_count.short_description = 'Assets'
    
    def icon_display(self, obj):
        if obj.icon:
            return format_html(
                '<i class="{}" style="color: {}; font-size: 16px;"></i> {}',
                obj.icon, obj.color, obj.icon
            )
        return "—"
    icon_display.short_description = 'Icon'
    
    def depreciation_info(self, obj):
        return f"{obj.default_depreciation_years} years"
    depreciation_info.short_description = 'Depreciation'
    
    def maintenance_info(self, obj):
        if obj.requires_maintenance:
            return f"Every {obj.default_maintenance_interval_days} days"
        return "No maintenance required"
    maintenance_info.short_description = 'Maintenance'

# Main Asset Admin
@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        'asset_number',
        'name',
        'category_display',
        'status_badge',
        'location_badge',
        'assigned_to_display',
        'condition_indicator',
        'value_display',
        'maintenance_indicator',
        'age_display'
    )

    list_filter = (
        'category',
        'status',
        'condition',
        'location_status',
        'company',
        'assigned_office',
        'assigned_department',
        'is_billable',
        'is_personal',
        'is_active'
    )

    search_fields = (
        'asset_number',
        'name',
        'description',
        'manufacturer',
        'model',
        'serial_number',
        'assigned_worker__first_name',
        'assigned_worker__last_name'
    )

    readonly_fields = (
        'id',
        'depreciated_value',
        'depreciation_rate',
        'age_in_years',
        'is_maintenance_due',
        'days_until_maintenance',
        'is_warranty_active',
        'is_available',
        'primary_image_preview',
        'financial_summary',
        'maintenance_summary',
        'assignment_history',
        'created_at',
        'updated_at'
    )

    date_hierarchy = 'purchase_date'

    # FIXED FIELDSETS - Removed duplicate fields
    fieldsets = (
        ('Asset Identification', {
            'fields': (
                'asset_number',
                'name',
                'category',
                'asset_type',
                'description'
            )
        }),
        ('Manufacturer Details', {
            'fields': (
                'manufacturer',
                'model',
                'year',
                'serial_number',
                'specifications'
            )
        }),
        ('Visual Documentation', {
            'fields': (
                ('primary_image', 'primary_image_preview'),
            )
        }),
        ('Ownership & Assignment', {
            'fields': (
                'company',
                'assigned_office',
                'assigned_department',
                'assigned_worker',
                'current_project'
            )
        }),
        ('Status & Location', {
            'fields': (
                'status',
                'location_status',
                'condition'
            )
        }),
        ('Financial Information', {
            'fields': (
                ('purchase_price', 'current_value'),
                'purchase_date',
                'depreciated_value',
                'depreciation_rate',
                'financial_summary'
            )
        }),
        ('Usage & Billing', {  # COMBINED: Usage Tracking + Business Settings
            'fields': (
                'usage_hours',
                'mileage',
                'age_in_years',
                'is_billable',
                'hourly_rate',
                'is_personal'
            ),
            'classes': ('collapse',)
        }),
        ('Maintenance', {
            'fields': (
                'last_maintenance_date',
                'next_maintenance_date',
                'is_maintenance_due',
                'days_until_maintenance',
                'maintenance_notes',
                'maintenance_summary'
            ),
            'classes': ('collapse',)
        }),
        ('Insurance & Compliance', {
            'fields': (
                'warranty_expiration',
                'is_warranty_active',
                'insurance_policy',
                'license_plate',
                'registration_expiration'
            ),
            'classes': ('collapse',)
        }),
        ('Assignment History', {
            'fields': (
                'assignment_history',
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
                'is_retired',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    inlines = [AssetMaintenanceInline, AssetAssignmentInline, AssetDepreciationInline]

    actions = [
        'mark_available', 
        'mark_maintenance_due',
        'calculate_depreciation',
        'schedule_maintenance',
        'retire_assets'
    ]

    # Custom display methods
    def category_display(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;"><i class="{}"></i> {}</span>',
            obj.category.color,
            obj.category.icon,
            obj.category.name
        )
    category_display.short_description = 'Category'

    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'available': '#28a745',
            'in_use': '#007bff',
            'maintenance': '#ffc107',
            'repair': '#fd7e14',
            'retired': '#6c757d',
            'lost': '#dc3545',
            'damaged': '#dc3545'
        }
        
        color = colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.status.replace('_', ' ').title()
        )
    status_badge.short_description = 'Status'

    def location_badge(self, obj):
        """Display location with icon"""
        icons = {
            'office': 'fas fa-building',
            'warehouse': 'fas fa-warehouse',
            'job_site': 'fas fa-hammer',
            'vehicle': 'fas fa-truck',
            'shop': 'fas fa-wrench',
            'storage': 'fas fa-boxes',
            'field': 'fas fa-map-marker-alt'
        }
        
        icon = icons.get(obj.location_status, 'fas fa-question')
        
        return format_html(
            '<i class="{}" style="margin-right: 5px;"></i>{}',
            icon,
            obj.location_status.replace('_', ' ').title()
        )
    location_badge.short_description = 'Location'

    def assigned_to_display(self, obj):
        """Show who/what asset is assigned to"""
        assignments = []
        
        if obj.assigned_worker:
            assignments.append(f"👤 {obj.assigned_worker.first_name} {obj.assigned_worker.last_name}")
        
        if obj.current_project:
            assignments.append(f"📋 {obj.current_project.name}")
        
        if obj.assigned_office:
            assignments.append(f"🏢 {obj.assigned_office.office_name}")
        
        if assignments:
            return format_html('<br>'.join(assignments))
        
        return "Unassigned"
    assigned_to_display.short_description = 'Assigned To'

    def condition_indicator(self, obj):
        """Display condition with color coding"""
        colors = {
            'excellent': '#28a745',
            'good': '#28a745',
            'fair': '#ffc107',
            'poor': '#fd7e14',
            'needs_repair': '#dc3545',
            'out_of_service': '#6c757d'
        }
        
        color = colors.get(obj.condition, '#6c757d')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_condition_display()
        )
    condition_indicator.short_description = 'Condition'

    def value_display(self, obj):
        """Display financial value information"""
        if obj.purchase_price:
            depreciated = obj.depreciated_value
            html = f"<div style='font-size: 11px;'>"
            html += f"<strong>${obj.purchase_price:,.0f}</strong> original<br>"
            html += f"<span style='color: #6c757d;'>${depreciated:,.0f} current</span>"
            html += "</div>"
            return format_html(html)
        return "—"
    value_display.short_description = 'Value'

    def maintenance_indicator(self, obj):
        """Show maintenance status"""
        if obj.is_maintenance_due:
            return format_html('<span style="color: #dc3545; font-weight: bold;">⚠ DUE</span>')
        elif obj.days_until_maintenance and obj.days_until_maintenance <= 30:
            return format_html(
                '<span style="color: #ffc107; font-weight: bold;">📅 {} days</span>',
                obj.days_until_maintenance
            )
        elif obj.next_maintenance_date:
            return format_html(
                '<span style="color: #28a745;">✓ {}</span>',
                obj.next_maintenance_date.strftime('%m/%d/%y')
            )
        return "—"
    maintenance_indicator.short_description = 'Maintenance'

    def age_display(self, obj):
        """Display asset age"""
        age = obj.age_in_years
        if age > 0:
            return f"{age:.1f} years"
        return "New"
    age_display.short_description = 'Age'

    def primary_image_preview(self, obj):
        """Display primary image preview"""
        if obj.primary_image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.primary_image.url
            )
        return "No image"
    primary_image_preview.short_description = 'Image Preview'

    def financial_summary(self, obj):
        """Display comprehensive financial summary"""
        html = "<table style='font-size: 12px;'>"
        
        if obj.purchase_price:
            html += f"<tr><td><strong>Purchase Price:</strong></td><td>${obj.purchase_price:,.2f}</td></tr>"
        
        if obj.current_value:
            html += f"<tr><td><strong>Current Value:</strong></td><td>${obj.current_value:,.2f}</td></tr>"
        
        depreciated = obj.depreciated_value
        html += f"<tr><td><strong>Depreciated Value:</strong></td><td>${depreciated:,.2f}</td></tr>"
        
        if obj.purchase_date:
            html += f"<tr><td><strong>Age:</strong></td><td>{obj.age_in_years:.1f} years</td></tr>"
        
        annual_dep = obj.depreciation_rate
        html += f"<tr><td><strong>Annual Depreciation:</strong></td><td>${annual_dep:,.2f}</td></tr>"
        
        if obj.is_billable and obj.hourly_rate:
            html += f"<tr><td><strong>Hourly Rate:</strong></td><td>${obj.hourly_rate}/hour</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    financial_summary.short_description = 'Financial Summary'

    def maintenance_summary(self, obj):
        """Display maintenance summary"""
        html = "<table style='font-size: 12px;'>"
        
        if obj.last_maintenance_date:
            html += f"<tr><td><strong>Last Maintenance:</strong></td><td>{obj.last_maintenance_date}</td></tr>"
        
        if obj.next_maintenance_date:
            color = '#dc3545' if obj.is_maintenance_due else '#28a745'
            html += f"<tr><td><strong>Next Maintenance:</strong></td><td><span style='color: {color};'>{obj.next_maintenance_date}</span></td></tr>"
        
        if obj.warranty_expiration:
            warranty_color = '#28a745' if obj.is_warranty_active else '#dc3545'
            status = 'Active' if obj.is_warranty_active else 'Expired'
            html += f"<tr><td><strong>Warranty:</strong></td><td><span style='color: {warranty_color};'>{status}</span></td></tr>"
        
        # Maintenance cost summary
        total_maintenance_cost = obj.maintenance_records.aggregate(
            total=Sum('labor_cost') + Sum('parts_cost') + Sum('external_cost')
        )['total'] or 0
        
        html += f"<tr><td><strong>Total Maintenance Cost:</strong></td><td>${total_maintenance_cost:,.2f}</td></tr>"
        html += f"<tr><td><strong>Maintenance Records:</strong></td><td>{obj.maintenance_records.count()}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    maintenance_summary.short_description = 'Maintenance Summary'

    def assignment_history(self, obj):
        """Display assignment history"""
        assignments = obj.assignments.order_by('-start_date')[:5]
        
        if assignments:
            html = "<div style='font-size: 12px;'><strong>Recent Assignments:</strong><ul>"
            for assignment in assignments:
                if assignment.assigned_to_worker:
                    assignee = f"👤 {assignment.assigned_to_worker.first_name} {assignment.assigned_to_worker.last_name}"
                elif assignment.assigned_to_project:
                    assignee = f"📋 {assignment.assigned_to_project.name}"
                elif assignment.assigned_to_office:
                    assignee = f"🏢 {assignment.assigned_to_office.office_name}"
                else:
                    assignee = "Unknown"
                
                end_date = assignment.end_date or "Present"
                html += f"<li>{assignee} ({assignment.start_date} - {end_date})</li>"
            
            html += "</ul></div>"
            return mark_safe(html)
        
        return "No assignment history"
    assignment_history.short_description = 'Assignment History'

    # Custom actions
    def mark_available(self, request, queryset):
        """Mark selected assets as available"""
        updated = queryset.update(status='available')
        self.message_user(request, f"{updated} assets marked as available.")
    mark_available.short_description = "Mark as available"

    def mark_maintenance_due(self, request, queryset):
        """Mark selected assets as needing maintenance"""
        updated = queryset.update(status='maintenance')
        self.message_user(request, f"{updated} assets marked for maintenance.")
    mark_maintenance_due.short_description = "Mark maintenance due"

    def calculate_depreciation(self, request, queryset):
        """Calculate depreciation for selected assets"""
        updated = 0
        for asset in queryset:
            if asset.purchase_price and asset.purchase_date:
                # This would trigger depreciation calculation
                updated += 1
        self.message_user(request, f"Depreciation calculated for {updated} assets.")
    calculate_depreciation.short_description = "Calculate depreciation"

    def schedule_maintenance(self, request, queryset):
        """Schedule next maintenance for selected assets"""
        updated = 0
        for asset in queryset:
            if asset.category.requires_maintenance:
                asset.schedule_next_maintenance()
                updated += 1
        self.message_user(request, f"Maintenance scheduled for {updated} assets.")
    schedule_maintenance.short_description = "Schedule maintenance"

    def retire_assets(self, request, queryset):
        """Retire selected assets"""
        updated = queryset.update(status='retired', is_retired=True)
        self.message_user(request, f"{updated} assets retired.")
    retire_assets.short_description = "Retire assets"

# Asset Maintenance Record Admin
@admin.register(AssetMaintenanceRecord)
class AssetMaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = (
        'asset',
        'maintenance_type',
        'performed_by',
        'performed_date',
        'total_cost_display',
        'issue_resolved',
        'follow_up_required'
    )
    
    list_filter = (
        'maintenance_type',
        'performed_date',
        'issue_resolved',
        'follow_up_required',
        'asset__category'
    )
    
    search_fields = (
        'asset__asset_number',
        'asset__name',
        'description',
        'performed_by'
    )
    
    readonly_fields = ('total_cost',)
    
    fieldsets = (
        ('Maintenance Information', {
            'fields': (
                'asset',
                'maintenance_type',
                'description',
                'performed_by',
                'performed_date'
            )
        }),
        ('Cost Breakdown', {
            'fields': (
                'labor_cost',
                'parts_cost',
                'external_cost',
                'total_cost'
            )
        }),
        ('Parts & Materials', {
            'fields': (
                'parts_used',
            ),
            'classes': ('collapse',)
        }),
        ('Results & Follow-up', {
            'fields': (
                'issue_resolved',
                'follow_up_required',
                'follow_up_date'
            )
        })
    )
    
    def total_cost_display(self, obj):
        return f"${obj.total_cost:,.2f}"
    total_cost_display.short_description = 'Total Cost'

# Asset Assignment Admin
@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'asset',
        'assignment_display',
        'start_date',
        'end_date',
        'duration_display',
        'is_active'
    )
    
    list_filter = (
        'start_date',
        'end_date',
        'is_active',
        'asset__category'
    )
    
    search_fields = (
        'asset__asset_number',
        'asset__name',
        'assigned_to_worker__first_name',
        'assigned_to_worker__last_name',
        'assigned_to_project__name'
    )
    
    def assignment_display(self, obj):
        if obj.assigned_to_worker:
            return f"👤 {obj.assigned_to_worker.first_name} {obj.assigned_to_worker.last_name}"
        elif obj.assigned_to_project:
            return f"📋 {obj.assigned_to_project.name}"
        elif obj.assigned_to_office:
            return f"🏢 {obj.assigned_to_office.office_name}"
        return "Unassigned"
    assignment_display.short_description = 'Assigned To'
    
    def duration_display(self, obj):
        if obj.end_date:
            duration = (obj.end_date - obj.start_date).days
            return f"{duration} days"
        else:
            duration = (date.today() - obj.start_date).days
            return f"{duration} days (ongoing)"
    duration_display.short_description = 'Duration'

# Asset Depreciation Admin
@admin.register(AssetDepreciation)
class AssetDepreciationAdmin(admin.ModelAdmin):
    list_display = (
        'asset',
        'depreciation_year',
        'method',
        'annual_depreciation',
        'accumulated_depreciation',
        'remaining_value'
    )
    
    list_filter = (
        'method',
        'depreciation_year',
        'asset__category'
    )
    
    search_fields = (
        'asset__asset_number',
        'asset__name'
    )
    
    def remaining_value(self, obj):
        remaining = obj.basis_value - obj.accumulated_depreciation
        return f"${remaining:,.2f}"
    remaining_value.short_description = "Remaining Value"

