# todo/admin.py - Modern Admin Interface for Todo/Task Management

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
    TaskList, Task, Comment, TaskAttachment, TaskTemplate, TaskTemplateItem
)

# Custom Forms
class TaskAdminForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'note': forms.Textarea(attrs={'rows': 2}),
            'blockers': forms.Textarea(attrs={'rows': 2}),
        }

# Inline admins
class TaskInline(admin.TabularInline):
    """Inline admin for tasks in task list view"""
    model = Task
    extra = 0
    fields = (
        'title', 'assigned_to', 'priority', 'status', 
        'due_date', 'total_hours_display', 'completed'
    )
    readonly_fields = ('total_hours_display',)
    
    def total_hours_display(self, obj):
        if obj.pk:
            return f"{obj.total_hours:.1f}h"
        return "—"
    total_hours_display.short_description = 'Est. Hours'

class CommentInline(admin.TabularInline):
    """Inline admin for task comments"""
    model = Comment
    extra = 0
    fields = ('author', 'comment_type', 'body', 'is_private', 'requires_response')
    readonly_fields = ('date',)

class TaskAttachmentInline(admin.TabularInline):
    """Inline admin for task attachments"""
    model = TaskAttachment
    extra = 0
    fields = ('file', 'description', 'uploaded_by', 'uploaded_at')
    readonly_fields = ('uploaded_at',)

class TaskTemplateItemInline(admin.TabularInline):
    """Inline admin for task template items"""
    model = TaskTemplateItem
    extra = 0
    fields = (
        'order', 'title', 'allotted_time', 'team_size', 
        'difficulty', 'priority', 'position'
    )
    ordering = ['order']

# Task List Admin
@admin.register(TaskList)
class TaskListAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'list_type_badge',
        'group',
        'status_indicator',
        'progress_bar',
        'task_summary',
        'priority_display',
        'due_date_display',
        'owner'
    )
    
    list_filter = (
        'list_type',
        'status',
        'is_active',
        'is_template',
        'group',
        'priority',
        'created_at',
        'target_completion_date'
    )
    
    search_fields = (
        'name',
        'description',
        'owner__first_name',
        'owner__last_name',
        'created_by__first_name',
        'created_by__last_name'
    )
    
    prepopulated_fields = {'slug': ('name',)}
    
    readonly_fields = (
        'completion_stats',
        'time_analysis',
        'task_distribution',
        'list_statistics'
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'slug',
                'description',
                'list_type',
                'status'
            )
        }),
        ('Organization', {
            'fields': (
                ('group', 'owner'),
                ('project', 'scope'),
                ('priority', 'is_active')
            )
        }),
        ('Workflow Settings', {
            'fields': (
                'is_template',
                'auto_assign',
                'requires_approval',
                'send_notifications'
            ),
            'classes': ('collapse',)
        }),
        ('Timeline', {
            'fields': (
                ('start_date', 'target_completion_date'),
                'completed_date'
            )
        }),
        ('Statistics', {
            'fields': (
                'completion_stats',
                'time_analysis',
                'task_distribution'
            ),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': (
                'created_by',
                'list_statistics'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [TaskInline]
    
    actions = [
        'mark_active',
        'mark_completed', 
        'clone_as_template',
        'apply_template',
        'bulk_assign_owner'
    ]

    def list_type_badge(self, obj):
        """Display list type with color coding"""
        colors = {
            'project': '#007bff',
            'maintenance': '#fd7e14',
            'training': '#28a745',
            'daily': '#17a2b8',
            'backlog': '#6c757d',
            'template': '#6f42c1',
            'personal': '#e83e8c',
            'custom': '#ffc107'
        }
        color = colors.get(obj.list_type, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_list_type_display()
        )
    list_type_badge.short_description = 'Type'

    def status_indicator(self, obj):
        """Display status with appropriate styling"""
        colors = {
            'active': '#28a745',
            'on_hold': '#ffc107',
            'completed': '#17a2b8',
            'archived': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        
        status_html = format_html(
            '<span style="color: {};">● {}</span>',
            color,
            obj.get_status_display()
        )
        
        if obj.is_overdue:
            status_html += format_html('<br><span style="color: #dc3545; font-size: 10px;">⚠ OVERDUE</span>')
        
        return status_html
    status_indicator.short_description = 'Status'

    def progress_bar(self, obj):
        """Display progress bar"""
        percent = obj.completion_percentage
        
        if percent >= 100:
            color = '#28a745'  # Green
        elif percent >= 75:
            color = '#17a2b8'  # Blue
        elif percent >= 50:
            color = '#ffc107'  # Yellow
        elif percent >= 25:
            color = '#fd7e14'  # Orange
        else:
            color = '#dc3545'  # Red
        
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 18px; border-radius: 3px; text-align: center; line-height: 18px; color: white; font-size: 10px; font-weight: bold;">'
            '{}%'
            '</div></div>',
            percent, color, int(percent)
        )
    progress_bar.short_description = 'Progress'

    def task_summary(self, obj):
        """Display task count summary"""
        return format_html(
            '<strong>{} tasks</strong><br>'
            '<small>{} pending | {} done</small>',
            obj.task_count,
            obj.pending_task_count,
            obj.completed_task_count
        )
    task_summary.short_description = 'Tasks'

    def priority_display(self, obj):
        """Display priority with visual indicator"""
        if obj.priority <= 5:
            color = '#dc3545'  # High priority - red
            icon = '🔥'
        elif obj.priority <= 50:
            color = '#ffc107'  # Medium priority - yellow
            icon = '⚡'
        else:
            color = '#28a745'  # Low priority - green
            icon = '📋'
        
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.priority
        )
    priority_display.short_description = 'Priority'

    def due_date_display(self, obj):
        """Display due date with warning if approaching"""
        if not obj.target_completion_date:
            return "No deadline"
        
        if obj.is_overdue:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">⚠ {}</span>',
                obj.target_completion_date.strftime('%m/%d/%Y')
            )
        elif obj.days_until_due and obj.days_until_due <= 7:
            return format_html(
                '<span style="color: #ffc107; font-weight: bold;">⏰ {}</span>',
                obj.target_completion_date.strftime('%m/%d/%Y')
            )
        else:
            return obj.target_completion_date.strftime('%m/%d/%Y')
    due_date_display.short_description = 'Due Date'

    def completion_stats(self, obj):
        """Display completion statistics"""
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Total Tasks:</strong></td><td>{obj.task_count}</td></tr>"
        html += f"<tr><td><strong>Completed:</strong></td><td>{obj.completed_task_count}</td></tr>"
        html += f"<tr><td><strong>Pending:</strong></td><td>{obj.pending_task_count}</td></tr>"
        html += f"<tr><td><strong>Progress:</strong></td><td>{obj.completion_percentage:.1f}%</td></tr>"
        
        if obj.target_completion_date:
            html += f"<tr><td><strong>Due Date:</strong></td><td>{obj.target_completion_date.strftime('%m/%d/%Y')}</td></tr>"
            if obj.days_until_due is not None:
                if obj.days_until_due < 0:
                    html += f"<tr><td><strong>Status:</strong></td><td style='color: #dc3545;'>{abs(obj.days_until_due)} days overdue</td></tr>"
                else:
                    html += f"<tr><td><strong>Days Left:</strong></td><td>{obj.days_until_due}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    completion_stats.short_description = 'Completion Statistics'

    def time_analysis(self, obj):
        """Display time analysis"""
        total_hours = obj.total_estimated_hours
        
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Estimated Hours:</strong></td><td>{total_hours:.1f}h</td></tr>"
        
        if obj.task_count > 0:
            avg_hours = total_hours / obj.task_count
            html += f"<tr><td><strong>Avg per Task:</strong></td><td>{avg_hours:.1f}h</td></tr>"
        
        # Calculate estimated days (assuming 8 hour work days)
        if total_hours > 0:
            work_days = total_hours / Decimal('8')
            html += f"<tr><td><strong>Est. Work Days:</strong></td><td>{work_days:.1f} days</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    time_analysis.short_description = 'Time Analysis'

    def task_distribution(self, obj):
        """Display task distribution by status/priority"""
        tasks = obj.tasks.all()
        
        # Count by status
        status_counts = {}
        for task in tasks:
            status = task.get_status_display()
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by priority
        priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for task in tasks:
            priority_counts[task.priority] = priority_counts.get(task.priority, 0) + 1
        
        html = "<table style='font-size: 12px;'>"
        html += "<tr><td colspan='2'><strong>By Status:</strong></td></tr>"
        for status, count in status_counts.items():
            html += f"<tr><td>{status}:</td><td>{count}</td></tr>"
        
        html += "<tr><td colspan='2'><strong>By Priority:</strong></td></tr>"
        priority_names = {1: 'Critical', 2: 'High', 3: 'Normal', 4: 'Low', 5: 'Backlog'}
        for priority, count in priority_counts.items():
            if count > 0:
                html += f"<tr><td>{priority_names[priority]}:</td><td>{count}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    task_distribution.short_description = 'Task Distribution'

    def list_statistics(self, obj):
        """Display comprehensive list statistics"""
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Created:</strong></td><td>{obj.created_at.strftime('%m/%d/%Y %H:%M')}</td></tr>"
        html += f"<tr><td><strong>Created By:</strong></td><td>{obj.created_by.get_full_name() if obj.created_by else 'Unknown'}</td></tr>"
        html += f"<tr><td><strong>Last Updated:</strong></td><td>{obj.updated_at.strftime('%m/%d/%Y %H:%M')}</td></tr>"
        
        if obj.group:
            html += f"<tr><td><strong>Group:</strong></td><td>{obj.group.name}</td></tr>"
        
        if obj.project:
            html += f"<tr><td><strong>Project:</strong></td><td>{obj.project.name}</td></tr>"
        
        if obj.scope:
            html += f"<tr><td><strong>Scope:</strong></td><td>{obj.scope}</td></tr>"
        
        html += f"<tr><td><strong>Settings:</strong></td><td>"
        settings = []
        if obj.is_template:
            settings.append("Template")
        if obj.auto_assign:
            settings.append("Auto-assign")
        if obj.requires_approval:
            settings.append("Requires approval")
        if obj.send_notifications:
            settings.append("Notifications")
        html += ", ".join(settings) if settings else "None"
        html += "</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    list_statistics.short_description = 'List Statistics'

    # Custom actions
    def mark_active(self, request, queryset):
        """Mark task lists as active"""
        updated = queryset.update(status='active', is_active=True)
        self.message_user(request, f"{updated} task lists marked as active.")
    mark_active.short_description = "Mark as active"

    def mark_completed(self, request, queryset):
        """Mark task lists as completed"""
        updated = 0
        for task_list in queryset:
            if task_list.all_tasks_completed:
                task_list.status = 'completed'
                task_list.completed_date = timezone.now().date()
                task_list.save()
                updated += 1
        self.message_user(request, f"{updated} task lists marked as completed.")
    mark_completed.short_description = "Mark as completed"

    def clone_as_template(self, request, queryset):
        """Clone task lists as templates"""
        cloned = 0
        for task_list in queryset:
            try:
                task_list.clone_as_template()
                cloned += 1
            except:
                pass
        self.message_user(request, f"{cloned} task lists cloned as templates.")
    clone_as_template.short_description = "Clone as templates"

    def apply_template(self, request, queryset):
        """Apply templates to create new task lists"""
        count = queryset.filter(is_template=True).count()
        self.message_user(request, f"{count} templates selected for application.")
    apply_template.short_description = "Apply templates"

    def bulk_assign_owner(self, request, queryset):
        """Bulk assign owner (would open form in real implementation)"""
        count = queryset.count()
        self.message_user(request, f"{count} task lists selected for owner assignment.")
    bulk_assign_owner.short_description = "Bulk assign owner"

# Task Admin
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    form = TaskAdminForm
    
    list_display = (
        'title',
        'task_list_display',
        'assigned_to_display',
        'status_badge',
        'priority_indicator',
        'progress_display',
        'due_date_status',
        'time_summary',
        'dependency_status'
    )

    list_filter = (
        'status',
        'priority',
        'difficulty',
        'completed',
        'requires_approval',
        'task_list__list_type',
        'task_list__group',
        'assigned_to',
        'position',
        'created_date',
        'due_date'
    )

    search_fields = (
        'title',
        'description',
        'task_list__name',
        'assigned_to__first_name',
        'assigned_to__last_name',
        'created_by__first_name',
        'created_by__last_name'
    )

    date_hierarchy = 'due_date'

    readonly_fields = (
        'cost_analysis',
        'time_tracking',
        'dependency_analysis',
        'completion_details',
        'task_statistics'
    )

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title',
                'description',
                'task_list',
                ('status', 'priority', 'difficulty')
            )
        }),
        ('Assignment', {
            'fields': (
                ('assigned_to', 'position'),
                ('created_by', 'requires_approval')
            )
        }),
        ('Work Estimation', {
            'fields': (
                ('allotted_time', 'team_size'),
                ('actual_hours', 'completion_percentage'),
                'time_tracking'
            )
        }),
        ('Schedule', {
            'fields': (
                ('start_date', 'due_date'),
                ('completed', 'completed_date'),
                'dependency_analysis'
            )
        }),
        ('Dependencies', {
            'fields': (
                'depends_on',
            ),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': (
                'note',
                'blockers'
            ),
            'classes': ('collapse',)
        }),
        ('Approval Workflow', {
            'fields': (
                ('approved_by', 'approved_date')
            ),
            'classes': ('collapse',)
        }),
        ('Cost Analysis', {
            'fields': (
                'cost_analysis',
            ),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': (
                'completion_details',
                'task_statistics'
            ),
            'classes': ('collapse',)
        })
    )

    filter_horizontal = ('depends_on',)
    inlines = [CommentInline, TaskAttachmentInline]

    actions = [
        'mark_completed',
        'mark_in_progress',
        'assign_to_me',
        'bulk_set_priority',
        'clone_tasks'
    ]

    def task_list_display(self, obj):
        """Display task list with type"""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.task_list.name,
            obj.task_list.get_list_type_display()
        )
    task_list_display.short_description = 'Task List'

    def assigned_to_display(self, obj):
        """Display assigned person with avatar placeholder"""
        if obj.assigned_to:
            return format_html(
                '<div style="display: flex; align-items: center;">'
                '<div style="width: 24px; height: 24px; border-radius: 50%; background-color: #007bff; color: white; display: flex; align-items: center; justify-content: center; font-size: 10px; margin-right: 5px;">'
                '{}'
                '</div>'
                '{}'
                '</div>',
                obj.assigned_to.first_name[0] if obj.assigned_to.first_name else 'U',
                obj.assigned_to.get_short_name()
            )
        return format_html('<span style="color: #6c757d;">Unassigned</span>')
    assigned_to_display.short_description = 'Assigned To'

    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'todo': '#6c757d',
            'in_progress': '#007bff',
            'review': '#ffc107',
            'blocked': '#dc3545',
            'completed': '#28a745',
            'cancelled': '#fd7e14'
        }
        color = colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def priority_indicator(self, obj):
        """Display priority with visual indicator"""
        priority_map = {1: ('🔥', '#dc3545'), 2: ('⚡', '#fd7e14'), 3: ('📋', '#28a745'), 4: ('📝', '#17a2b8'), 5: ('📂', '#6c757d')}
        icon, color = priority_map.get(obj.priority, ('📋', '#28a745'))
        
        return format_html(
            '<span style="color: {}; font-size: 14px;" title="{}">{}</span>',
            color,
            obj.get_priority_display(),
            icon
        )
    priority_indicator.short_description = 'Priority'

    def progress_display(self, obj):
        """Display progress with completion percentage"""
        percent = obj.completion_percentage
        
        if obj.completed:
            color = '#28a745'
        elif percent >= 75:
            color = '#17a2b8'
        elif percent >= 50:
            color = '#ffc107'
        elif percent >= 25:
            color = '#fd7e14'
        else:
            color = '#dc3545'
        
        return format_html(
            '<div style="width: 60px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 14px; border-radius: 3px; text-align: center; line-height: 14px; color: white; font-size: 9px;">'
            '{}%'
            '</div></div>',
            percent, color, percent
        )
    progress_display.short_description = 'Progress'

    def due_date_status(self, obj):
        """Display due date with status indicator"""
        if not obj.due_date:
            return "No due date"
        
        if obj.is_overdue and not obj.completed:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">⚠ {}</span>',
                obj.due_date.strftime('%m/%d')
            )
        elif obj.days_until_due and obj.days_until_due <= 3 and not obj.completed:
            return format_html(
                '<span style="color: #ffc107; font-weight: bold;">⏰ {}</span>',
                obj.due_date.strftime('%m/%d')
            )
        else:
            return obj.due_date.strftime('%m/%d/%Y')
    due_date_status.short_description = 'Due Date'

    def time_summary(self, obj):
        """Display time summary"""
        est_hours = obj.total_hours
        actual_hours = obj.actual_hours
        
        if actual_hours:
            variance = actual_hours - est_hours
            variance_color = '#dc3545' if variance > 0 else '#28a745'
            return format_html(
                '<strong>{:.1f}h</strong> est.<br>'
                '<small style="color: {};">{:.1f}h actual</small>',
                est_hours,
                variance_color,
                actual_hours
            )
        else:
            return format_html('<strong>{:.1f}h</strong> est.', est_hours)
    time_summary.short_description = 'Time'

    def dependency_status(self, obj):
        """Display dependency status"""
        deps = obj.depends_on.all()
        if not deps.exists():
            return "No dependencies"
        
        completed_deps = deps.filter(completed=True).count()
        total_deps = deps.count()
        
        if completed_deps == total_deps:
            return format_html('<span style="color: #28a745;">✓ Ready</span>')
        elif completed_deps > 0:
            return format_html(
                '<span style="color: #ffc107;">⏳ {}/{}</span>',
                completed_deps, total_deps
            )
        else:
            return format_html('<span style="color: #dc3545;">🔒 Blocked</span>')
    dependency_status.short_description = 'Dependencies'

    def cost_analysis(self, obj):
        """Display cost analysis"""
        estimated_cost = obj.estimated_cost
        actual_cost = obj.actual_cost
        
        html = "<table style='font-size: 12px;'>"
        
        if obj.position:
            html += f"<tr><td><strong>Position:</strong></td><td>{obj.position.name}</td></tr>"
            
            if obj.position.hors and obj.position.hourly:
                html += f"<tr><td><strong>Hourly Rate:</strong></td><td>${obj.position.hourly:.2f}</td></tr>"
            elif not obj.position.hors and obj.position.salary:
                hourly_rate = obj.position.salary / Decimal('2080')
                html += f"<tr><td><strong>Hourly Rate:</strong></td><td>${hourly_rate:.2f}</td></tr>"
        
        html += f"<tr><td><strong>Est. Hours:</strong></td><td>{obj.total_hours:.1f}h</td></tr>"
        html += f"<tr><td><strong>Est. Cost:</strong></td><td>${estimated_cost:.2f}</td></tr>"
        
        if obj.actual_hours:
            html += f"<tr><td><strong>Actual Hours:</strong></td><td>{obj.actual_hours:.1f}h</td></tr>"
            html += f"<tr><td><strong>Actual Cost:</strong></td><td>${actual_cost:.2f}</td></tr>"
            
            if obj.cost_variance:
                variance = obj.cost_variance
                color = '#dc3545' if variance > 0 else '#28a745'
                html += f"<tr><td><strong>Variance:</strong></td><td style='color: {color};'>${variance:.2f}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    cost_analysis.short_description = 'Cost Analysis'

    def time_tracking(self, obj):
        """Display time tracking details"""
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Estimated:</strong></td><td>{obj.allotted_time:.2f}h × {obj.team_size} = {obj.total_hours:.2f}h</td></tr>"
        
        if obj.actual_hours:
            html += f"<tr><td><strong>Actual:</strong></td><td>{obj.actual_hours:.2f}h</td></tr>"
            
            if obj.time_variance:
                variance = obj.time_variance
                color = '#dc3545' if variance > 0 else '#28a745'
                html += f"<tr><td><strong>Time Variance:</strong></td><td style='color: {color};'>{variance:+.2f}h</td></tr>"
                
                # Calculate efficiency percentage
                if obj.total_hours > 0:
                    efficiency = (obj.total_hours / obj.actual_hours) * 100
                    html += f"<tr><td><strong>Efficiency:</strong></td><td>{efficiency:.1f}%</td></tr>"
        
        html += f"<tr><td><strong>Difficulty:</strong></td><td>{obj.get_difficulty_display()}</td></tr>"
        html += f"<tr><td><strong>Team Size:</strong></td><td>{obj.team_size} person{'s' if obj.team_size > 1 else ''}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    time_tracking.short_description = 'Time Tracking'

    def dependency_analysis(self, obj):
        """Display dependency analysis"""
        depends_on = obj.depends_on.all()
        blocks = obj.blocks.all()
        
        html = "<table style='font-size: 12px;'>"
        
        if depends_on.exists():
            html += "<tr><td><strong>Depends On:</strong></td><td>"
            dep_list = []
            for dep in depends_on:
                status = "✓" if dep.completed else "⏳"
                dep_list.append(f"{status} {dep.title}")
            html += "<br>".join(dep_list)
            html += "</td></tr>"
            
            html += f"<tr><td><strong>Can Start:</strong></td><td>{'✓ Yes' if obj.can_start else '✗ No'}</td></tr>"
        
        if blocks.exists():
            html += "<tr><td><strong>Blocks:</strong></td><td>"
            block_list = [task.title for task in blocks[:3]]
            if blocks.count() > 3:
                block_list.append(f"and {blocks.count() - 3} more")
            html += "<br>".join(block_list)
            html += "</td></tr>"
        
        if not depends_on.exists() and not blocks.exists():
            html += "<tr><td colspan='2'>No dependencies</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    dependency_analysis.short_description = 'Dependencies'

    def completion_details(self, obj):
        """Display completion details"""
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Progress:</strong></td><td>{obj.completion_percentage}%</td></tr>"
        html += f"<tr><td><strong>Completed:</strong></td><td>{'Yes' if obj.completed else 'No'}</td></tr>"
        
        if obj.completed_date:
            html += f"<tr><td><strong>Completed Date:</strong></td><td>{obj.completed_date.strftime('%m/%d/%Y %H:%M')}</td></tr>"
        
        if obj.requires_approval:
            if obj.approved_by and obj.approved_date:
                html += f"<tr><td><strong>Approved By:</strong></td><td>{obj.approved_by.get_full_name()}</td></tr>"
                html += f"<tr><td><strong>Approved Date:</strong></td><td>{obj.approved_date.strftime('%m/%d/%Y %H:%M')}</td></tr>"
            else:
                html += "<tr><td><strong>Approval:</strong></td><td style='color: #ffc107;'>Pending</td></tr>"
        
        if obj.blockers:
            html += f"<tr><td><strong>Blockers:</strong></td><td>{obj.blockers[:100]}{'...' if len(obj.blockers) > 100 else ''}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    completion_details.short_description = 'Completion Details'

    def task_statistics(self, obj):
        """Display comprehensive task statistics"""
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Created:</strong></td><td>{obj.created_date.strftime('%m/%d/%Y %H:%M')}</td></tr>"
        html += f"<tr><td><strong>Created By:</strong></td><td>{obj.created_by.get_full_name()}</td></tr>"
        html += f"<tr><td><strong>Last Updated:</strong></td><td>{obj.updated_at.strftime('%m/%d/%Y %H:%M')}</td></tr>"
        
        if obj.start_date:
            html += f"<tr><td><strong>Start Date:</strong></td><td>{obj.start_date.strftime('%m/%d/%Y')}</td></tr>"
        
        # Calculate age of task
        age = (timezone.now().date() - obj.created_date.date()).days
        html += f"<tr><td><strong>Age:</strong></td><td>{age} days</td></tr>"
        
        # Comments count
        comment_count = obj.comments.count()
        html += f"<tr><td><strong>Comments:</strong></td><td>{comment_count}</td></tr>"
        
        # Attachments count
        attachment_count = obj.attachments.count()
        html += f"<tr><td><strong>Attachments:</strong></td><td>{attachment_count}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    task_statistics.short_description = 'Task Statistics'

    # Custom actions
    def mark_completed(self, request, queryset):
        """Mark selected tasks as completed"""
        updated = 0
        for task in queryset.exclude(completed=True):
            task.mark_completed(completed_by=request.user)
            updated += 1
        self.message_user(request, f"{updated} tasks marked as completed.")
    mark_completed.short_description = "Mark as completed"

    def mark_in_progress(self, request, queryset):
        """Mark selected tasks as in progress"""
        updated = queryset.filter(status='todo').update(status='in_progress')
        self.message_user(request, f"{updated} tasks marked as in progress.")
    mark_in_progress.short_description = "Mark as in progress"

    def assign_to_me(self, request, queryset):
        """Assign selected tasks to current user"""
        updated = queryset.filter(assigned_to__isnull=True).update(assigned_to=request.user)
        self.message_user(request, f"{updated} tasks assigned to you.")
    assign_to_me.short_description = "Assign to me"

    def bulk_set_priority(self, request, queryset):
        """Bulk set priority (would open form in real implementation)"""
        count = queryset.count()
        self.message_user(request, f"{count} tasks selected for priority update.")
    bulk_set_priority.short_description = "Bulk set priority"

    def clone_tasks(self, request, queryset):
        """Clone selected tasks"""
        cloned = 0
        for task in queryset:
            try:
                task.clone_to_list(task.task_list, reset_dates=True)
                cloned += 1
            except:
                pass
        self.message_user(request, f"{cloned} tasks cloned.")
    clone_tasks.short_description = "Clone tasks"

# Comment Admin
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'snippet_display',
        'task_link',
        'author',
        'comment_type_badge',
        'date',
        'privacy_indicator',
        'response_required'
    )
    
    list_filter = (
        'comment_type',
        'is_private',
        'requires_response',
        'date',
        'author'
    )
    
    search_fields = (
        'body',
        'task__title',
        'author__first_name',
        'author__last_name'
    )
    
    readonly_fields = ('attachment_preview',)
    
    fieldsets = (
        ('Comment Information', {
            'fields': (
                ('author', 'task'),
                'comment_type',
                'body'
            )
        }),
        ('Settings', {
            'fields': (
                'is_private',
                'requires_response'
            )
        }),
        ('Attachment', {
            'fields': (
                'attachment',
                'attachment_preview'
            ),
            'classes': ('collapse',)
        })
    )

    def snippet_display(self, obj):
        """Display comment snippet with author"""
        return obj.snippet(100)
    snippet_display.short_description = 'Comment'

    def task_link(self, obj):
        """Display task as clickable link"""
        url = reverse('admin:todo_task_change', args=[obj.task.id])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)
    task_link.short_description = 'Task'

    def comment_type_badge(self, obj):
        """Display comment type with color coding"""
        colors = {
            'note': '#6c757d',
            'update': '#007bff',
            'question': '#ffc107',
            'blocker': '#dc3545',
            'approval': '#28a745',
            'review': '#17a2b8'
        }
        color = colors.get(obj.comment_type, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            obj.get_comment_type_display()
        )
    comment_type_badge.short_description = 'Type'

    def privacy_indicator(self, obj):
        """Display privacy indicator"""
        if obj.is_private:
            return format_html('<span style="color: #dc3545;">🔒 Private</span>')
        return format_html('<span style="color: #28a745;">👁 Public</span>')
    privacy_indicator.short_description = 'Privacy'

    def response_required(self, obj):
        """Display if response is required"""
        if obj.requires_response:
            return format_html('<span style="color: #ffc107;">⚠ Response Required</span>')
        return "—"
    response_required.short_description = 'Response'

    def attachment_preview(self, obj):
        """Display attachment preview"""
        if obj.attachment:
            return format_html(
                '<a href="{}" target="_blank">📎 View Attachment</a>',
                obj.attachment.url
            )
        return "No attachment"
    attachment_preview.short_description = 'Attachment Preview'

# Task Attachment Admin
@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        'task',
        'description',
        'file_link',
        'uploaded_by',
        'uploaded_at'
    )
    
    list_filter = (
        'uploaded_at',
        'uploaded_by'
    )
    
    search_fields = (
        'description',
        'task__title',
        'uploaded_by__first_name',
        'uploaded_by__last_name'
    )
    
    readonly_fields = ('uploaded_at', 'file_preview')

    def file_link(self, obj):
        """Display file as downloadable link"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">📎 {}</a>',
                obj.file.url,
                obj.file.name.split('/')[-1]
            )
        return "No file"
    file_link.short_description = 'File'

    def file_preview(self, obj):
        """Display file preview if it's an image"""
        if obj.file:
            file_url = obj.file.url
            if any(file_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                return format_html(
                    '<img src="{}" style="max-height: 200px; max-width: 300px;" />',
                    file_url
                )
            else:
                return format_html(
                    '<a href="{}" target="_blank">📄 View File</a>',
                    file_url
                )
        return "No file"
    file_preview.short_description = 'Preview'

# Task Template Admin
@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category_badge',
        'template_items_count',
        'total_estimated_hours',
        'created_by',
        'is_active'
    )
    
    list_filter = (
        'category',
        'is_active',
        'created_at'
    )
    
    search_fields = (
        'name',
        'description'
    )
    
    readonly_fields = ('template_statistics', 'usage_metrics')
    
    fieldsets = (
        ('Template Information', {
            'fields': (
                'name',
                'description',
                'category',
                'is_active'
            )
        }),
        ('Statistics', {
            'fields': (
                'template_statistics',
                'usage_metrics'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [TaskTemplateItemInline]
    
    actions = ['activate_templates', 'deactivate_templates', 'apply_to_lists']

    def category_badge(self, obj):
        """Display category with color coding"""
        colors = {
            'project': '#007bff',
            'maintenance': '#fd7e14',
            'onboarding': '#28a745',
            'training': '#17a2b8',
            'inspection': '#6f42c1',
            'custom': '#6c757d'
        }
        color = colors.get(obj.category, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_category_display()
        )
    category_badge.short_description = 'Category'

    def template_items_count(self, obj):
        """Count of template items"""
        count = obj.template_tasks.count()
        return format_html('<strong>{}</strong> tasks', count)
    template_items_count.short_description = 'Tasks'

    def total_estimated_hours(self, obj):
        """Total estimated hours for template"""
        total = obj.template_tasks.aggregate(
            total=Sum('allotted_time')
        )['total'] or Decimal('0')
        return f"{total:.1f}h"
    total_estimated_hours.short_description = 'Est. Hours'

    def template_statistics(self, obj):
        """Display template statistics"""
        items = obj.template_tasks.all()
        
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Total Tasks:</strong></td><td>{items.count()}</td></tr>"
        
        if items.exists():
            total_hours = items.aggregate(total=Sum('allotted_time'))['total']
            avg_hours = total_hours / items.count() if items.count() > 0 else 0
            html += f"<tr><td><strong>Total Hours:</strong></td><td>{total_hours:.1f}h</td></tr>"
            html += f"<tr><td><strong>Avg per Task:</strong></td><td>{avg_hours:.1f}h</td></tr>"
            
            # Difficulty distribution
            difficulty_counts = {}
            for item in items:
                diff = item.get_difficulty_display()
                difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
            
            html += "<tr><td><strong>Difficulty Mix:</strong></td><td>"
            diff_list = [f"{diff}: {count}" for diff, count in difficulty_counts.items()]
            html += "<br>".join(diff_list)
            html += "</td></tr>"
        
        html += f"<tr><td><strong>Created:</strong></td><td>{obj.created_at.strftime('%m/%d/%Y')}</td></tr>"
        html += f"<tr><td><strong>Created By:</strong></td><td>{obj.created_by.get_full_name()}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    template_statistics.short_description = 'Template Statistics'

    def usage_metrics(self, obj):
        """Display usage metrics (would be tracked in real implementation)"""
        html = "<table style='font-size: 12px;'>"
        html += "<tr><td><strong>Times Used:</strong></td><td>—</td></tr>"
        html += "<tr><td><strong>Success Rate:</strong></td><td>—</td></tr>"
        html += "<tr><td><strong>Avg Completion Time:</strong></td><td>—</td></tr>"
        html += "<tr><td colspan='2'><small>Usage tracking not yet implemented</small></td></tr>"
        html += "</table>"
        return mark_safe(html)
    usage_metrics.short_description = 'Usage Metrics'

    def activate_templates(self, request, queryset):
        """Activate selected templates"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} templates activated.")
    activate_templates.short_description = "Activate templates"

    def deactivate_templates(self, request, queryset):
        """Deactivate selected templates"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} templates deactivated.")
    deactivate_templates.short_description = "Deactivate templates"

    def apply_to_lists(self, request, queryset):
        """Apply templates to create task lists"""
        count = queryset.filter(is_active=True).count()
        self.message_user(request, f"{count} active templates selected for application.")
    apply_to_lists.short_description = "Apply to task lists"

# Task Template Item Admin
@admin.register(TaskTemplateItem)
class TaskTemplateItemAdmin(admin.ModelAdmin):
    list_display = (
        'template',
        'order',
        'title',
        'time_and_team',
        'difficulty_badge',
        'priority_indicator',
        'position'
    )
    
    list_filter = (
        'template__category',
        'difficulty',
        'priority',
        'position'
    )
    
    search_fields = (
        'title',
        'description',
        'template__name'
    )
    
    ordering = ['template', 'order']

    def time_and_team(self, obj):
        """Display time and team size"""
        total_hours = obj.allotted_time * obj.team_size
        return format_html(
            '{:.1f}h<br><small>{} × {} person{}</small>',
            total_hours,
            obj.allotted_time,
            obj.team_size,
            's' if obj.team_size > 1 else ''
        )
    time_and_team.short_description = 'Time & Team'

    def difficulty_badge(self, obj):
        """Display difficulty with color coding"""
        colors = {
            'easy': '#28a745',
            'medium': '#ffc107',
            'hard': '#fd7e14',
            'expert': '#dc3545'
        }
        color = colors.get(obj.difficulty, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            obj.get_difficulty_display()
        )
    difficulty_badge.short_description = 'Difficulty'

    def priority_indicator(self, obj):
        """Display priority with visual indicator"""
        priority_map = {1: ('🔥', '#dc3545'), 2: ('⚡', '#fd7e14'), 3: ('📋', '#28a745'), 4: ('📝', '#17a2b8'), 5: ('📂', '#6c757d')}
        icon, color = priority_map.get(obj.priority, ('📋', '#28a745'))
        
        return format_html(
            '<span style="color: {}; font-size: 14px;">{}</span>',
            color, icon
        )
    priority_indicator.short_description = 'Priority'

# Custom admin site configuration
admin.site.site_header = "Task Management Administration"
admin.site.site_title = "Task Admin"
admin.site.index_title = "Welcome to Task Management"