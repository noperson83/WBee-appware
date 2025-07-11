# project/admin.py - Modern Admin Interface for Projects

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from decimal import Decimal

from .models import (
    ProjectTemplate, ProjectCategory, Project, ScopeOfWork, ProjectMaterial,
    ProjectChange, ProjectMilestone
)
from material.models import MaterialLifecycle

# Inline admins for related models
class ScopeOfWorkInline(admin.TabularInline):
    """Inline admin for scope of work items"""
    model = ScopeOfWork
    extra = 1
    fields = (
        'area', 'system_type', 'priority', 'phase', 
        'percent_complete', 'estimated_cost', 'actual_cost'
    )
    readonly_fields = ('created_at', 'updated_at')

class ProjectMaterialInline(admin.TabularInline):
    """Inline admin for project materials"""
    model = ProjectMaterial
    extra = 0
    fields = (
        'product', 'material_type', 'task', 'quantity', 'unit_cost',
        'status', 'delivered_date', 'installed_date'
    )
    readonly_fields = ('total_cost_display', 'created_at')
    
    def total_cost_display(self, obj):
        if obj.pk:
            return f"${obj.total:,.2f}"
        return "—"
    total_cost_display.short_description = 'Total Cost'

class ProjectChangeInline(admin.TabularInline):
    """Inline admin for project changes"""
    model = ProjectChange
    extra = 0
    fields = (
        'change_type', 'description', 'cost_impact', 
        'schedule_impact_days', 'is_approved'
    )
    readonly_fields = ('created_at',)

class ProjectMilestoneInline(admin.TabularInline):
    """Inline admin for project milestones"""
    model = ProjectMilestone
    extra = 0
    fields = (
        'name', 'target_date', 'actual_date', 
        'is_critical', 'is_complete'
    )
    readonly_fields = ('created_at',)

# Project Category Admin
@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'business_category',
        'workflow_stage',
        'billable',
        'requires_scheduling',
        'tracks_inventory',
        'is_active'
    )
    list_filter = (
        'business_category',
        'workflow_stage',
        'billable',
        'requires_scheduling',
        'tracks_inventory',
        'is_active'
    )
    search_fields = (
        'name',
        'workflow_stage',
        'business_category__name'
    )
    ordering = ('business_category', 'sort_order', 'name')
    fieldsets = (
        ('Category Info', {
            'fields': (
                'business_category',
                'name',
                'icon',
                'color',
                'workflow_stage',
                'sort_order',
                'is_active'
            )
        }),
        ('Behavior', {
            'fields': (
                'tracks_inventory',
                'requires_scheduling',
                'billable'
            )
        })
    )

# Project Template Admin
@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'business_category',
        'estimated_duration_days',
        'default_markup',
        'projects_using_template',
        'is_active'
    )
    
    list_filter = (
        'business_category',
        'is_active',
        'created_at'
    )
    
    search_fields = (
        'name',
        'description',
        'business_category__name'
    )
    
    fieldsets = (
        ('Template Information', {
            'fields': (
                'name',
                'business_category',
                'description',
                'is_active'
            )
        }),
        ('Default Settings', {
            'fields': (
                'estimated_duration_days',
                'default_markup',
                'default_burden'
            )
        }),
        ('Template Content', {
            'fields': (
                'template_tasks',
                'required_materials'
            ),
            'classes': ('collapse',)
        })
    )
    
    def projects_using_template(self, obj):
        count = obj.projects.count()
        if count > 0:
            url = reverse('admin:project_project_changelist') + f'?template__id__exact={obj.id}'
            return format_html('<a href="{}">{} projects</a>', url, count)
        return "0 projects"
    projects_using_template.short_description = 'Projects Using Template'

# Main Project Admin
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'job_number',
        'name',
        'display_locations',
        'business_term_display',
        'status_badge',
        'project_manager',
        'progress_bar',
        'financial_summary',
        'due_date',
        'overdue_indicator'
    )

    list_filter = (
        'status',
        'priority',
        # filtering by business category is not supported without a direct field
        'project_manager',
        'start_date',
        'due_date',
        'created_at'
    )

    search_fields = (
        'job_number',
        'name',
        'description',
        'service_locations__name',
        'service_locations__client__company_name',
        'project_manager__first_name',
        'project_manager__last_name'
    )

    readonly_fields = (
        'id',
        'profit_margin_display',
        'outstanding_balance_display',
        'revenue_to_date_display',
        'is_profitable_display',
        'days_until_due_display',
        'project_duration_display',
        'task_completion_display',
        'material_costs_summary',
        'featured_image_preview',
        'project_statistics',
        'created_at',
        'updated_at'
    )

    date_hierarchy = 'start_date'

    fieldsets = (
        ('Project Identification', {
            'fields': (
                'job_number',
                'revision',
                'name',
                'service_locations',
                'template',
                'status',
                'priority'
            )
        }),
        ('Description & Scope', {
            'fields': (
                'description',
                'scope_overview',
                ('featured_image', 'featured_image_preview'),
                'site_contact'
            )
        }),
        ('Team Assignment', {
            'fields': (
                'project_manager',
                'estimator',
                'supervisor',
                'team_leads',
                'team_members'
            )
        }),
        ('Timeline', {
            'fields': (
                'date_requested',
                'start_date',
                'due_date',
                'completed_date',
                'days_until_due_display',
                'project_duration_display'
            )
        }),
        ('Financial Information', {
            'fields': (
                ('estimated_cost', 'contract_value'),
                ('markup_percentage', 'burden_percentage', 'license_markup'),
                ('invoiced_amount', 'paid_amount', 'paid_date'),
                'profit_margin_display',
                'outstanding_balance_display',
                'revenue_to_date_display',
                'is_profitable_display'
            )
        }),
        ('Progress Tracking', {
            'fields': (
                'percent_complete',
                'task_completion_display',
                'client_satisfaction_rating'
            )
        }),
        ('Classification', {
            'fields': (
                'tax_status',
                'division',
                'project_type'
            ),
            'classes': ('collapse',)
        }),
        ('Material Costs', {
            'fields': (
                'material_costs_summary',
            ),
            'classes': ('collapse',)
        }),
        ('Notes & Terms', {
            'fields': (
                'internal_notes',
                'pricing_disclaimer'
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
                'project_statistics',
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

    inlines = [ScopeOfWorkInline, ProjectMaterialInline, ProjectChangeInline, ProjectMilestoneInline]

    actions = [
        'mark_complete',
        'calculate_material_costs',
        'update_progress',
        'generate_invoices'
    ]

    def display_locations(self, obj):
        return ", ".join(obj.service_locations.values_list('name', flat=True))
    display_locations.short_description = 'Service Locations'

    # Custom display methods
    def business_term_display(self, obj):
        """Show business-specific term for project"""
        if obj.business_category:
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                obj.business_category.color,
                obj.project_term
            )
        return "Project"
    business_term_display.short_description = 'Type'

    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'prospect': '#FFA500',
            'quoted': '#17a2b8',
            'active': '#28a745',
            'installing': '#007bff',
            'complete': '#6c757d',
            'invoiced': '#fd7e14',
            'paid': '#28a745',
            'cancelled': '#dc3545'
        }
        
        # Default color for custom statuses
        color = colors.get(obj.status, '#007bff')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.status.replace('_', ' ').title()
        )
    status_badge.short_description = 'Status'

    def progress_bar(self, obj):
        """Display progress bar"""
        percent = float(obj.percent_complete)
        
        # Color based on progress
        if percent >= 100:
            color = '#28a745'  # Green
        elif percent >= 75:
            color = '#007bff'  # Blue
        elif percent >= 50:
            color = '#ffc107'  # Yellow
        else:
            color = '#dc3545'  # Red
        
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; line-height: 20px; color: white; font-size: 11px; font-weight: bold;">'
            '{}%'
            '</div></div>',
            percent, color, int(percent)
        )
    progress_bar.short_description = 'Progress'

    def financial_summary(self, obj):
        """Display financial summary"""
        if obj.contract_value:
            contract = float(obj.contract_value)
            margin = float(obj.profit_margin)
            return format_html(
                '<div style="font-size: 11px;">'
                '<strong>{}</strong><br>'
                '<span style="color: {};">{}% margin</span>'
                '</div>',
                f"${contract:,.0f}",
                '#28a745' if obj.is_profitable else '#dc3545',
                f"{margin:.1f}"
            )
        return "—"
    financial_summary.short_description = 'Financial'

    def overdue_indicator(self, obj):
        """Show if project is overdue"""
        if obj.is_overdue:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">⚠ OVERDUE</span>'
            )
        elif obj.days_until_due and obj.days_until_due <= 7:
            return format_html(
                '<span style="color: #ffc107; font-weight: bold;">⚡ Due Soon</span>'
            )
        return ""
    overdue_indicator.short_description = 'Status'

    def profit_margin_display(self, obj):
        """Display profit margin with color coding"""
        margin = float(obj.profit_margin)
        color = '#28a745' if margin > 0 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            f"{margin:.2f}%"
        )
    profit_margin_display.short_description = 'Profit Margin'

    def outstanding_balance_display(self, obj):
        """Display outstanding balance"""
        balance = float(obj.outstanding_balance)
        color = '#dc3545' if balance > 0 else '#28a745'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            f"${balance:,.2f}"
        )
    outstanding_balance_display.short_description = 'Outstanding Balance'

    def revenue_to_date_display(self, obj):
        """Display revenue earned to date"""
        revenue = obj.revenue_to_date
        return f"${revenue:,.2f}"
    revenue_to_date_display.short_description = 'Revenue to Date'

    def is_profitable_display(self, obj):
        """Display profitability indicator"""
        if obj.is_profitable:
            return format_html('<span style="color: #28a745;">✓ Profitable</span>')
        else:
            return format_html('<span style="color: #dc3545;">✗ Loss</span>')
    is_profitable_display.short_description = 'Profitability'

    def days_until_due_display(self, obj):
        """Display days until due"""
        days = obj.days_until_due
        if days is not None:
            if days < 0:
                return format_html('<span style="color: #dc3545;">{} days overdue</span>', abs(days))
            elif days <= 7:
                return format_html('<span style="color: #ffc107;">{} days left</span>', days)
            else:
                return f"{days} days left"
        return "—"
    days_until_due_display.short_description = 'Days Until Due'

    def project_duration_display(self, obj):
        """Display project duration"""
        duration = obj.project_duration
        if duration is not None:
            return f"{duration} days"
        return "In progress"
    project_duration_display.short_description = 'Duration'

    def task_completion_display(self, obj):
        """Display task completion percentage"""
        if obj.total_tasks > 0:
            percent = obj.task_completion_percentage
            return format_html(
                '{} ({}/{})',
                f"{percent:.1f}%", obj.completed_tasks, obj.total_tasks
            )
        return "No tasks"
    task_completion_display.short_description = 'Task Completion'

    def featured_image_preview(self, obj):
        """Display featured image preview"""
        if obj.featured_image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.featured_image.url
            )
        return "No image"
    featured_image_preview.short_description = 'Image Preview'

    def material_costs_summary(self, obj):
        """Display material costs breakdown"""
        try:
            costs = obj.calculate_material_costs()
            html = "<table style='font-size: 12px;'>"
            html += f"<tr><td><strong>Devices:</strong></td><td>${costs['device_cost']:,.2f}</td></tr>"
            html += f"<tr><td><strong>Hardware:</strong></td><td>${costs['hardware_cost']:,.2f}</td></tr>"
            html += f"<tr><td><strong>Software:</strong></td><td>${costs['software_cost']:,.2f}</td></tr>"
            html += f"<tr><td><strong>Licenses:</strong></td><td>${costs['license_cost']:,.2f}</td></tr>"
            html += f"<tr><td><strong>Travel:</strong></td><td>${costs['travel_cost']:,.2f}</td></tr>"
            html += f"<tr style='border-top: 1px solid #ccc;'><td><strong>Total:</strong></td><td><strong>${costs['total_cost']:,.2f}</strong></td></tr>"
            html += "</table>"
            return mark_safe(html)
        except:
            return "Calculation unavailable"
    material_costs_summary.short_description = 'Material Costs'

    def project_statistics(self, obj):
        """Display comprehensive project statistics"""
        try:
            html = "<table style='font-size: 12px;'>"
            html += f"<tr><td><strong>Business Type:</strong></td><td>{obj.business_category.name if obj.business_category else 'Not set'}</td></tr>"
            html += f"<tr><td><strong>Project Term:</strong></td><td>{obj.project_term}</td></tr>"
            loc = obj.service_locations.first()
            client_name = loc.client.company_name if loc else 'N/A'
            loc_name = loc.name if loc else 'N/A'
            html += f"<tr><td><strong>Client:</strong></td><td>{client_name}</td></tr>"
            html += f"<tr><td><strong>Location:</strong></td><td>{loc_name}</td></tr>"
            html += f"<tr><td><strong>Scope Items:</strong></td><td>{obj.scope_items.count()}</td></tr>"
            html += f"<tr><td><strong>Changes:</strong></td><td>{obj.changes.count()}</td></tr>"
            html += f"<tr><td><strong>Milestones:</strong></td><td>{obj.milestones.count()}</td></tr>"
            
            if obj.client_satisfaction_rating:
                stars = "★" * obj.client_satisfaction_rating + "☆" * (5 - obj.client_satisfaction_rating)
                html += f"<tr><td><strong>Client Rating:</strong></td><td>{stars} ({obj.client_satisfaction_rating}/5)</td></tr>"
            
            html += "</table>"
            return mark_safe(html)
        except:
            return "Statistics unavailable"
    project_statistics.short_description = 'Project Statistics'

    # Custom actions
    def mark_complete(self, request, queryset):
        """Mark selected projects as complete"""
        updated = 0
        for project in queryset:
            if project.status != 'complete':
                project.mark_complete()
                updated += 1
        self.message_user(request, f"{updated} projects marked as complete.")
    mark_complete.short_description = "Mark as complete"

    def calculate_material_costs(self, request, queryset):
        """Recalculate material costs for selected projects"""
        updated = 0
        for project in queryset:
            try:
                project.calculate_material_costs()
                updated += 1
            except:
                pass
        self.message_user(request, f"Material costs recalculated for {updated} projects.")
    calculate_material_costs.short_description = "Recalculate material costs"

    def update_progress(self, request, queryset):
        """Update progress based on task completion"""
        updated = 0
        for project in queryset:
            if project.total_tasks > 0:
                project.percent_complete = project.task_completion_percentage
                project.save()
                updated += 1
        self.message_user(request, f"Progress updated for {updated} projects.")
    update_progress.short_description = "Update progress from tasks"

    def generate_invoices(self, request, queryset):
        """Generate invoices for selected projects"""
        # This would integrate with your invoicing system
        count = queryset.filter(status='complete', invoiced_amount=0).count()
        self.message_user(request, f"{count} projects ready for invoicing.")
    generate_invoices.short_description = "Generate invoices"

# Scope of Work Admin
@admin.register(ScopeOfWork)
class ScopeOfWorkAdmin(admin.ModelAdmin):
    list_display = (
        'area',
        'system_type',
        'project',
        'phase',
        'progress_bar',
        'cost_variance_display',
        'priority'
    )
    
    list_filter = (
        'phase',
        'percent_complete',
        'priority'
    )
    
    search_fields = (
        'area',
        'system_type',
        'description',
        'project__name',
        'project__job_number'
    )
    
    def progress_bar(self, obj):
        """Display progress bar for scope item"""
        percent = float(obj.percent_complete)
        color = '#28a745' if percent >= 100 else '#007bff'
        
        return format_html(
            '<div style="width: 80px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 15px; border-radius: 3px; text-align: center; line-height: 15px; color: white; font-size: 10px;">'
            '{}%'
            '</div></div>',
            percent, color, int(percent)
        )
    progress_bar.short_description = 'Progress'
    
    def cost_variance_display(self, obj):
        """Display cost variance"""
        variance = obj.cost_variance
        if variance is not None:
            val = float(variance)
            color = '#dc3545' if val > 0 else '#28a745'
            return format_html(
                '<span style="color: {};">{}</span>',
                color,
                f"${val:,.2f}"
            )
        return "—"
    cost_variance_display.short_description = 'Cost Variance'

# Project Change Admin
@admin.register(ProjectChange)
class ProjectChangeAdmin(admin.ModelAdmin):
    list_display = (
        'project',
        'change_type',
        'cost_impact_display',
        'schedule_impact_days',
        'approval_status',
        'requested_by',
        'created_at'
    )
    
    list_filter = (
        'change_type',
        'is_approved',
        'created_at'
    )
    
    search_fields = (
        'project__name',
        'project__job_number',
        'description',
        'requested_by'
    )
    
    def cost_impact_display(self, obj):
        """Display cost impact with color coding"""
        impact = float(obj.cost_impact)
        if impact > 0:
            return format_html(
                '<span style="color: #dc3545;">{}</span>',
                f"+${impact:,.2f}"
            )
        elif impact < 0:
            return format_html(
                '<span style="color: #28a745;">{}</span>',
                f"${impact:,.2f}"
            )
        return "$0.00"
    cost_impact_display.short_description = 'Cost Impact'
    
    def approval_status(self, obj):
        """Display approval status"""
        if obj.is_approved:
            return format_html('<span style="color: #28a745;">✓ Approved</span>')
        else:
            return format_html('<span style="color: #ffc107;">⏳ Pending</span>')
    approval_status.short_description = 'Status'

# Project Milestone Admin
@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'project',
        'target_date',
        'actual_date',
        'status_indicator',
        'is_critical'
    )
    
    list_filter = (
        'is_critical',
        'is_complete',
        'target_date'
    )
    
    search_fields = (
        'name',
        'description',
        'project__name',
        'project__job_number'
    )
    
    def status_indicator(self, obj):
        """Display milestone status"""
        if obj.is_complete:
            return format_html('<span style="color: #28a745;">✓ Complete</span>')
        elif obj.target_date < timezone.now().date():
            return format_html('<span style="color: #dc3545;">⚠ Overdue</span>')
        else:
            return format_html('<span style="color: #007bff;">⏳ Pending</span>')
    status_indicator.short_description = 'Status'


class MaterialLifecycleInline(admin.TabularInline):
    model = MaterialLifecycle
    extra = 0
    readonly_fields = (
        'ordered_at', 'received_at', 'stored_at', 'prepared_at', 'fabricated_at',
        'assembled_at', 'inspected_at', 'tested_at', 'repaired_at',
        'refurbished_at', 'shipped_at', 'delivered_at', 'staged_at',
        'installed_at', 'billed_at', 'paid_at', 'warranted_at',
        'created_at', 'updated_at'
    )


@admin.register(ProjectMaterial)
class ProjectMaterialAdmin(admin.ModelAdmin):
    list_display = (
        'project', 'product', 'material_type', 'quantity', 'unit_cost',
        'status', 'delivered_date', 'installed_date'
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MaterialLifecycleInline]
