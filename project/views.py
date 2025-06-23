# project/views.py - Modern Django Views for Project Management

import asyncio
import json
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import (
    Q, F, Count, Sum, Avg, Max, Min, 
    Prefetch, Case, When, Value, IntegerField
)
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView,
    DeleteView, TemplateView, FormView
)
from django.forms.models import model_to_dict

from rest_framework import generics, viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Project, ProjectTemplate, ScopeOfWork, ProjectMaterial,
    ProjectChange, ProjectMilestone
)
from .forms import (
    ProjectForm, ScopeOfWorkForm, DeviceForm,
    HardwareForm, SoftwareForm, LicenseForm, TravelForm,
    ProjectStatusForm,
)
from .serializers import ProjectSerializer, ScopeOfWorkSerializer

from .utils import generate_job_number, calculate_project_metrics
from .permissions import ProjectAccessMixin, ProjectPermissionMixin
from todo.models import TaskList

User = get_user_model()

# ============================================
# Base Mixins and Utilities
# ============================================


class AjaxResponseMixin:
    """Mixin to handle AJAX requests consistently"""
    
    def dispatch(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            self.is_ajax = True
        else:
            self.is_ajax = False
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.is_ajax:
            return JsonResponse({
                'success': True,
                'object_id': self.object.pk,
                'redirect_url': self.get_success_url()
            })
        return response
    
    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.is_ajax:
            return JsonResponse({
                'success': False,
                'errors': form.errors,
                'non_field_errors': form.non_field_errors()
            }, status=400)
        return response

class OptimizedQuerysetMixin:
    """Mixin to optimize querysets for performance"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if hasattr(self, 'select_related_fields'):
            queryset = queryset.select_related(*self.select_related_fields)
        
        if hasattr(self, 'prefetch_related_fields'):
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)
            
        if hasattr(self, 'annotations'):
            queryset = queryset.annotate(**self.annotations)
            
        return queryset

# ============================================
# Dashboard Views
# ============================================

class ProjectDashboardView(LoginRequiredMixin, TemplateView):
    """Modern project dashboard with real-time metrics"""
    template_name = 'project/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Cache key for user-specific dashboard data
        cache_key = f'dashboard_data_{user.id}_{user.role}'
        dashboard_data = cache.get(cache_key)
        
        if not dashboard_data:
            dashboard_data = self._build_dashboard_data(user)
            cache.set(cache_key, dashboard_data, 60 * 15)  # 15 minutes
        
        context.update(dashboard_data)
        
        # Real-time notifications (not cached)
        context['notifications'] = self._get_user_notifications(user)
        
        return context
    
    def _build_dashboard_data(self, user):
        """Build comprehensive dashboard data"""
        base_queryset = self._get_user_projects(user)
        
        # Project statistics
        project_stats = base_queryset.aggregate(
            total_projects=Count('id'),
            active_projects=Count('id', filter=Q(status='active')),
            completed_projects=Count('id', filter=Q(status='complete')),
            overdue_projects=Count('id', filter=Q(
                due_date__lt=timezone.now().date(),
                status__in=['active', 'installing']
            )),
            total_value=Sum('contract_value'),
            avg_completion=Avg('percent_complete')
        )
        
        # Recent projects
        recent_projects = base_queryset.select_related(
            'location', 'project_manager'
        ).prefetch_related(
            'team_members'
        ).order_by('-updated_at')[:10]
        
        # Upcoming milestones
        upcoming_milestones = ProjectMilestone.objects.filter(
            project__in=base_queryset,
            target_date__gte=date.today(),
            target_date__lte=date.today() + timedelta(days=30),
            is_complete=False
        ).select_related('project').order_by('target_date')[:10]
        
        # Team performance data
        team_performance = self._calculate_team_performance(base_queryset)
        
        # Financial summary
        financial_data = self._calculate_financial_summary(base_queryset)
        
        return {
            'project_stats': project_stats,
            'recent_projects': recent_projects,
            'upcoming_milestones': upcoming_milestones,
            'team_performance': team_performance,
            'financial_data': financial_data,
            'quick_actions': self._get_quick_actions(user)
        }
    
    def _get_user_projects(self, user):
        """Get projects accessible to the user"""
        if user.role == 'admin':
            return Project.objects.all()
        elif user.role == 'project_manager':
            return Project.objects.filter(
                Q(project_manager=user) | 
                Q(estimator=user) |
                Q(team_leads=user)
            ).distinct()
        elif user.role in ['supervisor', 'worker']:
            return Project.objects.filter(
                Q(supervisor=user) |
                Q(team_leads=user) |
                Q(team_members=user)
            ).distinct()
        elif user.role == 'client':
            if hasattr(user, 'client'):
                return Project.objects.filter(location__client=user.client)
        
        return Project.objects.none()
    
    def _get_user_notifications(self, user):
        """Get real-time notifications for user"""
        notifications = []
        
        # Overdue projects
        overdue_count = self._get_user_projects(user).filter(
            due_date__lt=date.today(),
            status__in=['active', 'installing']
        ).count()
        
        if overdue_count > 0:
            notifications.append({
                'type': 'warning',
                'message': f'You have {overdue_count} overdue project(s)',
                'url': reverse('project:overdue-projects')
            })
        
        # Pending approvals (for managers)
        if user.role in ['admin', 'project_manager']:
            pending_changes = ProjectChange.objects.filter(
                project__in=self._get_user_projects(user),
                is_approved=False
            ).count()
            
            if pending_changes > 0:
                notifications.append({
                    'type': 'info',
                    'message': f'{pending_changes} change request(s) need approval',
                    'url': reverse('project:change-list')
                })
        
        return notifications
    
    def _calculate_team_performance(self, projects):
        """Calculate team performance metrics"""
        return {
            'total_team_members': User.objects.filter(
                assigned_projects__in=projects
            ).distinct().count(),
            'active_team_leads': projects.values('team_leads').distinct().count(),
            'avg_project_duration': projects.filter(
                completed_date__isnull=False
            ).annotate(
                duration=F('completed_date') - F('start_date')
            ).aggregate(avg_duration=Avg('duration'))['avg_duration']
        }
    
    def _calculate_financial_summary(self, projects):
        """Calculate financial summary"""
        return projects.aggregate(
            total_estimated_cost=Sum('estimated_cost'),
            total_contract_value=Sum('contract_value'),
            total_invoiced=Sum('invoiced_amount'),
            total_paid=Sum('paid_amount'),
            avg_profit_margin=Avg(
                Case(
                    When(contract_value__gt=0, then=(
                        F('contract_value') - F('estimated_cost')
                    ) * 100 / F('contract_value')),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
        )
    
    def _get_quick_actions(self, user):
        """Get role-specific quick actions"""
        actions = [
            {'title': 'View All Projects', 'url': reverse('project:project-list'), 'icon': 'fa-list'},
        ]
        
        if user.role in ['admin', 'project_manager']:
            actions.extend([
                {'title': 'Create Project', 'url': reverse('project:project-create'), 'icon': 'fa-plus'},
                {'title': 'Financial Report', 'url': reverse('project:financial-report'), 'icon': 'fa-chart-line'},
                {'title': 'Team Performance', 'url': reverse('project:team-performance'), 'icon': 'fa-users'},
            ])
        
        return actions

# ============================================
# Project CRUD Views
# ============================================

class ProjectListView(LoginRequiredMixin, OptimizedQuerysetMixin, ListView):
    """Enhanced project list with filtering and search"""
    model = Project
    template_name = 'project/project_list.html'
    context_object_name = 'projects'
    paginate_by = 25
    
    select_related_fields = [
        'location',
        'project_manager',
        # Follow the relation through ``location`` to load the project's
        # business category in a single query.
        'location__business_category',
    ]
    prefetch_related_fields = [
        'team_members',
        Prefetch('scope_items', queryset=ScopeOfWork.objects.select_related('project')),
        Prefetch('milestones', queryset=ProjectMilestone.objects.filter(is_critical=True))
    ]
    annotations = {
        # Count tasks via related task lists to avoid FieldError when
        # referencing the non-existent "tasks" field directly on Project
        'task_count': Count('task_lists__tasks', distinct=True),
        'team_size': Count('team_members', distinct=True),
        'milestone_count': Count('milestones'),
    }
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Role-based filtering
        if user.role == 'admin':
            pass  # Admin sees all projects
        elif user.role == 'project_manager':
            queryset = queryset.filter(
                Q(project_manager=user) | 
                Q(estimator=user) |
                Q(team_leads=user)
            ).distinct()
        elif user.role in ['supervisor', 'worker']:
            queryset = queryset.filter(
                Q(supervisor=user) |
                Q(team_leads=user) |
                Q(team_members=user)
            ).distinct()
        elif user.role == 'client':
            if hasattr(user, 'client'):
                queryset = queryset.filter(location__client=user.client)
            else:
                queryset = queryset.none()
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(job_number__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(location__name__icontains=search_query) |
                Q(location__client__company_name__icontains=search_query)
            ).distinct()
        
        # Status filtering
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Priority filtering
        priority_filter = self.request.GET.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        # Date range filtering
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(start_date__lte=date_to)
        
        # Manager filtering
        manager_filter = self.request.GET.get('manager')
        if manager_filter:
            queryset = queryset.filter(project_manager_id=manager_filter)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filter options
        context.update({
            'status_choices': Project._meta.get_field('status').choices if hasattr(Project._meta.get_field('status'), 'choices') else [],
            'priority_choices': Project.PRIORITY_CHOICES,
            'managers': User.objects.filter(
                Q(roles__contains=['admin']) |
                Q(roles__contains=['project_manager'])
            ),
            'current_filters': {
                'search': self.request.GET.get('search', ''),
                'status': self.request.GET.get('status', ''),
                'priority': self.request.GET.get('priority', ''),
                'date_from': self.request.GET.get('date_from', ''),
                'date_to': self.request.GET.get('date_to', ''),
                'manager': self.request.GET.get('manager', ''),
            }
        })
        
        return context

class ProjectDetailView(ProjectAccessMixin, DetailView):
    """Comprehensive project detail view"""
    model = Project
    template_name = 'project/project_detail_full.html'
    context_object_name = 'project'
    slug_field = 'job_number'
    slug_url_kwarg = 'job_number'
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'location', 'location__client', 'project_manager',
            'estimator', 'supervisor'
        ).prefetch_related(
            'team_leads', 'team_members', 'scope_items',
            'material_items', 'changes', 'milestones'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        user = self.request.user
        
        # User permissions for this project
        context['user_permissions'] = self._get_user_permissions(project, user)
        
        # Financial summary
        context['financial_summary'] = {
            'estimated_cost': project.estimated_cost,
            'contract_value': project.contract_value,
            'profit_margin': project.profit_margin,
            'outstanding_balance': project.outstanding_balance,
            'revenue_to_date': project.revenue_to_date,
            'is_profitable': project.is_profitable,
        }
        
        # Progress tracking
        context['progress_data'] = {
            'percent_complete': project.percent_complete,
            'total_tasks': project.total_tasks,
            'completed_tasks': project.completed_tasks,
            'task_completion_percentage': project.task_completion_percentage,
            'days_until_due': project.days_until_due,
            'is_overdue': project.is_overdue,
        }

        # Scope of work and related task lists
        context['scope_list'] = project.scope_items.all()
        context['task_list'] = TaskList.objects.filter(project=project).select_related('scope')

        # Consolidated metrics using utility function
        context['metrics'] = calculate_project_metrics(project)
        
        # Material costs
        try:
            context['material_costs'] = project.calculate_material_costs()
        except:
            context['material_costs'] = {}
        
        # Recent activity
        context['recent_activity'] = self._get_recent_activity(project)
        
        # Upcoming milestones
        context['upcoming_milestones'] = project.milestones.filter(
            target_date__gte=date.today(),
            is_complete=False
        ).order_by('target_date')[:5]
        
        # Team information
        context['team_info'] = {
            'project_manager': project.project_manager,
            'estimator': project.estimator,
            'supervisor': project.supervisor,
            'team_leads': project.team_leads.all(),
            'team_members': project.team_members.all(),
            'team_size': project.team_members.count(),
        }
        
        return context
    
    def _get_user_permissions(self, project, user):
        """Get user-specific permissions for the project"""
        permissions = {
            'can_edit': False,
            'can_delete': False,
            'can_manage_team': False,
            'can_approve_changes': False,
            'can_view_financials': False,
            'can_add_materials': False,
        }
        
        if user.is_superuser or user.role == 'admin':
            return {key: True for key in permissions}
        
        if user.role == 'project_manager':
            permissions.update({
                'can_edit': project.project_manager == user or project.estimator == user,
                'can_delete': project.project_manager == user,
                'can_manage_team': project.project_manager == user,
                'can_approve_changes': True,
                'can_view_financials': True,
                'can_add_materials': True,
            })
        elif user.role == 'supervisor':
            permissions.update({
                'can_edit': project.supervisor == user or user in project.team_leads.all(),
                'can_add_materials': True,
            })
        elif user.role == 'worker':
            permissions.update({
                'can_edit': user in project.team_members.all(),
            })
        elif user.role == 'client':
            permissions.update({
                'can_view_financials': True,
            })
        
        return permissions
    
    def _get_recent_activity(self, project):
        """Get recent project activity"""
        activities = []
        
        # Recent changes
        recent_changes = project.changes.order_by('-created_at')[:5]
        for change in recent_changes:
            activities.append({
                'type': 'change',
                'title': f'{change.change_type.title()} Request',
                'description': change.description[:100] + '...' if len(change.description) > 100 else change.description,
                'date': change.created_at,
                'user': change.requested_by,
                'status': 'approved' if change.is_approved else 'pending'
            })
        
        # Recent milestone completions
        recent_milestones = project.milestones.filter(
            is_complete=True,
            actual_date__isnull=False
        ).order_by('-actual_date')[:3]
        
        for milestone in recent_milestones:
            activities.append({
                'type': 'milestone',
                'title': f'Milestone: {milestone.name}',
                'description': 'Completed',
                'date': milestone.actual_date,
                'status': 'completed'
            })
        
        return sorted(activities, key=lambda x: x['date'], reverse=True)[:10]

class ProjectCreateView(LoginRequiredMixin, AjaxResponseMixin, CreateView):
    """Create new project with business logic validation"""
    model = Project
    form_class = ProjectForm
    template_name = 'project/project_form.html'
    
    # ProjectForm does not accept a custom 'user' argument. Simply
    # return the default kwargs provided by the generic view.
    def get_form_kwargs(self):
        return super().get_form_kwargs()
    
    def form_valid(self, form):
        """Enhanced form processing with business logic"""
        form.instance.created_by = self.request.user
        
        # Auto-assign project manager if not set
        if not form.instance.project_manager:
            form.instance.project_manager = self.request.user
        
        # Generate job number if not provided
        if not form.instance.job_number:
            form.instance.job_number = generate_job_number(
                form.instance.location.business_category if form.instance.location else None
            )
        
        # Validate user's project limits
        if self.request.user.role == 'project_manager':
            active_projects = Project.objects.filter(
                project_manager=self.request.user,
                status__in=['prospect', 'quoted', 'active', 'installing']
            ).count()
            
            max_projects = getattr(self.request.user, 'max_concurrent_projects', 10)
            if active_projects >= max_projects:
                form.add_error(None, f"You have reached your maximum concurrent project limit ({max_projects})")
                return self.form_invalid(form)
        
        with transaction.atomic():
            response = super().form_valid(form)
            
            # Create default milestones if template is used
            if form.instance.template:
                self._create_default_milestones(form.instance)
            
            # Add creator to team
            if self.request.user not in form.instance.team_members.all():
                form.instance.team_members.add(self.request.user)
            
            # Log project creation
            messages.success(
                self.request, 
                f'Project "{form.instance.name}" created successfully.'
            )
        
        return response
    
    def _create_default_milestones(self, project):
        """Create default milestones from template"""
        if project.template and project.template.template_tasks:
            for task_data in project.template.template_tasks:
                if task_data.get('is_milestone'):
                    ProjectMilestone.objects.create(
                        project=project,
                        name=task_data.get('name', 'Milestone'),
                        description=task_data.get('description', ''),
                        target_date=project.start_date + timedelta(
                            days=task_data.get('days_offset', 0)
                        ) if project.start_date else None,
                        is_critical=task_data.get('is_critical', False)
                    )
    
    def get_success_url(self):
        return reverse('project:project-detail', kwargs={'job_number': self.object.job_number})

class ProjectUpdateView(ProjectAccessMixin, ProjectPermissionMixin, AjaxResponseMixin, UpdateView):
    """Update project with change tracking"""
    model = Project
    form_class = ProjectForm
    template_name = 'project/project_form.html'
    slug_field = 'job_number'
    slug_url_kwarg = 'job_number'
    permission_required = 'project.change_project'
    
    # Return default kwargs; ProjectForm has no custom arguments
    def get_form_kwargs(self):
        return super().get_form_kwargs()
    
    def form_valid(self, form):
        """Track changes and apply business logic"""
        old_instance = Project.objects.get(pk=self.object.pk)
        
        # Track significant changes
        significant_changes = []
        change_fields = ['status', 'due_date', 'contract_value', 'estimated_cost']
        
        for field in change_fields:
            old_value = getattr(old_instance, field)
            new_value = form.cleaned_data.get(field)
            
            if old_value != new_value:
                significant_changes.append({
                    'field': field,
                    'old_value': str(old_value),
                    'new_value': str(new_value)
                })
        
        with transaction.atomic():
            response = super().form_valid(form)
            
            # Create change records for significant changes
            if significant_changes:
                change_description = '; '.join([
                    f"{change['field']}: {change['old_value']} → {change['new_value']}"
                    for change in significant_changes
                ])
                
                ProjectChange.objects.create(
                    project=self.object,
                    change_type='modification',
                    description=f"Project updated: {change_description}",
                    requested_by=self.request.user.username,
                    is_approved=True,  # Auto-approve for authorized users
                    approved_by=self.request.user.username,
                    approved_date=timezone.now().date()
                )
            
            # Update project status logic
            self._handle_status_change(old_instance, self.object)
            
            messages.success(
                self.request,
                f'Project "{self.object.name}" updated successfully.'
            )
        
        return response
    
    def _handle_status_change(self, old_instance, new_instance):
        """Handle business logic for status changes"""
        if old_instance.status != new_instance.status:
            if new_instance.status == 'complete' and not new_instance.completed_date:
                new_instance.completed_date = date.today()
                new_instance.percent_complete = 100
                new_instance.save()
            elif new_instance.status != 'complete' and old_instance.status == 'complete':
                new_instance.completed_date = None
                new_instance.save()
    
    def get_success_url(self):
        return reverse('project:project-detail', kwargs={'job_number': self.object.job_number})

class ProjectDeleteView(ProjectAccessMixin, ProjectPermissionMixin, DeleteView):
    """Delete project with proper authorization"""
    model = Project
    template_name = 'project/project_confirm_delete.html'
    slug_field = 'job_number'
    slug_url_kwarg = 'job_number'
    success_url = reverse_lazy('project:project-list')
    permission_required = 'project.delete_project'
    
    def test_func(self):
        """Enhanced permission check for deletion"""
        base_test = super().test_func()
        if not base_test:
            return False
        
        project = self.get_object()
        user = self.request.user
        
        # Only project managers, estimators, or admins can delete
        if user.role == 'admin':
            return True
        elif user.role == 'project_manager':
            return project.project_manager == user or project.estimator == user
        
        return False
    
    def delete(self, request, *args, **kwargs):
        """Enhanced deletion with validation"""
        project = self.get_object()
        
        # Prevent deletion of active projects with high value
        if project.contract_value and project.contract_value > 50000:
            if project.status in ['active', 'installing']:
                messages.error(
                    request,
                    'Cannot delete high-value active projects. Please complete or cancel first.'
                )
                return redirect('project:project-detail', job_number=project.job_number)
        
        # Create deletion record
        ProjectChange.objects.create(
            project=project,
            change_type='deletion',
            description=f'Project deleted by {request.user.username}',
            requested_by=request.user.username,
            is_approved=True,
            approved_by=request.user.username,
            approved_date=timezone.now().date()
        )
        
        project_name = project.name
        response = super().delete(request, *args, **kwargs)
        
        messages.success(request, f'Project "{project_name}" deleted successfully.')
        return response

class ProjectDuplicateView(ProjectAccessMixin, ProjectPermissionMixin, CreateView):
    """Duplicate an existing project."""
    model = Project
    form_class = ProjectForm
    template_name = 'project/project_form.html'
    slug_field = 'job_number'
    slug_url_kwarg = 'job_number'
    permission_required = 'project.add_project'

    def get_initial(self):
        original = get_object_or_404(Project, job_number=self.kwargs['job_number'])
        initial = model_to_dict(
            original,
            exclude=[
                'id', 'pk', 'job_number', 'revision', 'created_at', 'updated_at'
            ],
        )
        initial['name'] = f"Copy of {original.name}"
        initial['job_number'] = generate_job_number(original.business_category)
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user

        if not form.instance.job_number:
            form.instance.job_number = generate_job_number(
                form.instance.location.business_category if form.instance.location else None
            )

        response = super().form_valid(form)

        original = get_object_or_404(Project, job_number=self.kwargs['job_number'])
        self.object.team_leads.set(original.team_leads.all())
        self.object.team_members.set(original.team_members.all())

        messages.success(
            self.request,
            f'Project "{self.object.name}" duplicated successfully.'
        )

        return response

    def get_success_url(self):
        return reverse('project:project-detail', kwargs={'job_number': self.object.job_number})


class ProjectStatusUpdateView(ProjectAccessMixin, View):
    """Update a project's status."""

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, job_number=kwargs["job_number"])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = ProjectStatusForm(instance=self.project)
        return render(request, "project/project_status_form.html", {"form": form, "project": self.project})

    def post(self, request, *args, **kwargs):
        form = ProjectStatusForm(request.POST, instance=self.project)
        if form.is_valid():
            old_status = self.project.status
            self.project = form.save(commit=False)
            if self.project.status == "complete" and not self.project.completed_date:
                self.project.completed_date = date.today()
                self.project.percent_complete = 100
            elif self.project.status != "complete" and old_status == "complete":
                self.project.completed_date = None
            self.project.save()
            messages.success(request, "Project status updated successfully.")
            return redirect("project:project-detail", job_number=self.project.job_number)
        return render(request, "project/project_status_form.html", {"form": form, "project": self.project})


class ProjectMarkCompleteView(ProjectAccessMixin, View):
    """Convenience view to mark a project as complete."""

    def post(self, request, job_number):
        project = get_object_or_404(Project, job_number=job_number)
        if not request.user.has_perm("project.change_project"):
            raise PermissionDenied
        old_status = project.status
        project.status = "complete"
        if not project.completed_date:
            project.completed_date = date.today()
        project.percent_complete = 100
        project.save()
        ProjectChange.objects.create(
            project=project,
            change_type="status",
            description=f"Status changed from {old_status} to complete",
            requested_by=request.user.username,
            is_approved=True,
            approved_by=request.user.username,
            approved_date=timezone.now().date(),
        )
        messages.success(request, f'Project "{project.name}" marked as complete.')
        return redirect("project:project-detail", job_number=project.job_number)


class ProjectReopenView(ProjectAccessMixin, View):
    """Reopen a completed project."""

    def post(self, request, job_number):
        project = get_object_or_404(Project, job_number=job_number)
        if not request.user.has_perm("project.change_project"):
            raise PermissionDenied
        old_status = project.status
        project.status = "active"
        project.completed_date = None
        project.save()
        ProjectChange.objects.create(
            project=project,
            change_type="status",
            description=f"Status changed from {old_status} to active",
            requested_by=request.user.username,
            is_approved=True,
            approved_by=request.user.username,
            approved_date=timezone.now().date(),
        )
        messages.success(request, f'Project "{project.name}" reopened.')
        return redirect("project:project-detail", job_number=project.job_number)

# ============================================
# Specialized Project Views
# ============================================

class ActiveProjectListView(ProjectListView):
    """List only active projects"""
    template_name = 'project/active_projects.html'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(status__in=['active', 'installing'])

class CompleteProjectListView(ProjectListView):
    """List only completed projects"""
    template_name = 'project/complete_projects.html'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(status='complete')

class OverdueProjectListView(ProjectListView):
    """List overdue projects"""
    template_name = 'project/overdue_projects.html'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(
            due_date__lt=date.today(),
            status__in=['active', 'installing', 'quoted']
        )

class ProjectProgressView(ProjectAccessMixin, DetailView):
    """Detailed project progress tracking"""
    model = Project
    template_name = 'project/project_progress.html'
    slug_field = 'job_number'
    slug_url_kwarg = 'job_number'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        
        # Progress breakdown by scope items
        scope_progress = project.scope_items.annotate(
            task_count=Count('task_lists__tasks', distinct=True),
            completed_tasks=Count(
                'task_lists__tasks',
                filter=Q(task_lists__tasks__completed=True),
                distinct=True,
            )
        ).values(
            'area', 'system_type', 'percent_complete', 
            'task_count', 'completed_tasks'
        )
        
        # Milestone progress
        milestones = project.milestones.order_by('target_date')
        milestone_data = []
        for milestone in milestones:
            milestone_data.append({
                'name': milestone.name,
                'target_date': milestone.target_date,
                'actual_date': milestone.actual_date,
                'is_complete': milestone.is_complete,
                'is_critical': milestone.is_critical,
                'days_variance': (milestone.actual_date - milestone.target_date).days if milestone.actual_date and milestone.target_date else None
            })
        
        # Team productivity
        team_productivity = self._calculate_team_productivity(project)
        
        # Time tracking
        time_tracking = self._calculate_time_tracking(project)
        
        context.update({
            'scope_progress': scope_progress,
            'milestone_data': milestone_data,
            'team_productivity': team_productivity,
            'time_tracking': time_tracking,
            'progress_chart_data': self._get_progress_chart_data(project)
        })
        
        return context
    
    def _calculate_team_productivity(self, project):
        """Calculate team productivity metrics"""
        team_members = project.team_members.all()
        productivity_data = []
        
        for member in team_members:
            member_tasks = getattr(member, 'assigned_tasks', None)
            if member_tasks:
                completed_tasks = member_tasks.filter(completed=True).count()
                total_tasks = member_tasks.count()
                completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                
                productivity_data.append({
                    'member': member,
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'completion_rate': completion_rate
                })
        
        return productivity_data
    
    def _calculate_time_tracking(self, project):
        """Calculate time tracking metrics"""
        start_date = project.start_date
        due_date = project.due_date
        today = date.today()
        
        if not start_date:
            return {}
        
        total_days = (due_date - start_date).days if due_date else None
        elapsed_days = (today - start_date).days
        remaining_days = (due_date - today).days if due_date else None
        
        return {
            'start_date': start_date,
            'due_date': due_date,
            'total_days': total_days,
            'elapsed_days': elapsed_days,
            'remaining_days': remaining_days,
            'time_progress_percentage': (elapsed_days / total_days * 100) if total_days else 0,
            'is_on_schedule': project.percent_complete >= (elapsed_days / total_days * 100) if total_days else True
        }
    
    def _get_progress_chart_data(self, project):
        """Get data for progress charts"""
        # This would typically integrate with your task management system
        # For now, return sample structure
        return {
            'weekly_progress': [],  # Weekly progress data points
            'scope_breakdown': [],  # Progress by scope area
            'milestone_timeline': []  # Milestone timeline data
        }

class ProjectTimelineView(ProjectAccessMixin, DetailView):
    """Project timeline and activity view"""
    model = Project
    template_name = 'project/project_timeline.html'
    slug_field = 'job_number'
    slug_url_kwarg = 'job_number'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        
        # Build comprehensive timeline
        timeline_events = []
        
        # Project creation
        timeline_events.append({
            'date': project.created_at.date(),
            'type': 'project_created',
            'title': 'Project Created',
            'description': f'Project created by {project.created_by.get_full_name() if project.created_by else "System"}',
            'user': project.created_by,
            'icon': 'fa-plus-circle',
            'color': 'primary'
        })
        
        # Changes
        for change in project.changes.order_by('created_at'):
            timeline_events.append({
                'date': change.created_at.date(),
                'type': 'change',
                'title': f'{change.change_type.title()} Request',
                'description': change.description,
                'user': change.requested_by,
                'icon': 'fa-edit',
                'color': 'warning' if not change.is_approved else 'success',
                'status': 'approved' if change.is_approved else 'pending'
            })
        
        # Milestones
        for milestone in project.milestones.order_by('target_date'):
            if milestone.is_complete:
                timeline_events.append({
                    'date': milestone.actual_date,
                    'type': 'milestone',
                    'title': f'Milestone: {milestone.name}',
                    'description': milestone.description,
                    'icon': 'fa-flag-checkered',
                    'color': 'success',
                    'is_critical': milestone.is_critical
                })
        
        # Sort by date
        timeline_events.sort(key=lambda x: x['date'])
        
        context['timeline_events'] = timeline_events
        return context

class ProjectActivityView(ProjectAccessMixin, DetailView):
    """Full activity log for a project"""
    model = Project
    template_name = 'project/project_activity.html'
    slug_field = 'job_number'
    slug_url_kwarg = 'job_number'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activities'] = self._get_activity(self.object)
        return context

    def _get_activity(self, project):
        activities = []

        # All changes
        for change in project.changes.order_by('-created_at'):
            activities.append({
                'type': 'change',
                'title': f'{change.change_type.title()} Request',
                'description': change.description,
                'date': change.created_at,
                'user': change.requested_by,
                'status': 'approved' if change.is_approved else 'pending',
            })

        # Completed milestones
        for milestone in project.milestones.filter(
            is_complete=True,
            actual_date__isnull=False
        ).order_by('-actual_date'):
            activities.append({
                'type': 'milestone',
                'title': f'Milestone: {milestone.name}',
                'description': 'Completed',
                'date': milestone.actual_date,
                'status': 'completed',
            })

        return sorted(activities, key=lambda x: x['date'], reverse=True)

class ProjectFinancialView(ProjectAccessMixin, DetailView):
    """Project financial details and analysis"""
    model = Project
    template_name = 'project/project_financial.html'
    slug_field = 'job_number'
    slug_url_kwarg = 'job_number'
    
    def test_func(self):
        """Enhanced permission check for financial data"""
        base_test = super().test_func()
        if not base_test:
            return False
        
        user = self.request.user
        if user.role in ['admin', 'project_manager']:
            return True
        elif user.role == 'client':
            # Clients can view basic financial info
            return True
        
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        user = self.request.user
        
        # Basic financial data
        financial_data = {
            'estimated_cost': project.estimated_cost,
            'contract_value': project.contract_value,
            'markup_percentage': project.markup_percentage,
            'burden_percentage': project.burden_percentage,
            'invoiced_amount': project.invoiced_amount,
            'paid_amount': project.paid_amount,
            'outstanding_balance': project.outstanding_balance,
            'profit_margin': project.profit_margin,
            'revenue_to_date': project.revenue_to_date,
            'is_profitable': project.is_profitable
        }
        
        # Material costs breakdown
        try:
            material_costs = project.calculate_material_costs()
        except:
            material_costs = {}
        
        # Show detailed costs only to authorized users
        if user.role in ['admin', 'project_manager']:
            context.update({
                'financial_data': financial_data,
                'material_costs': material_costs,
                'cost_breakdown': self._get_detailed_cost_breakdown(project),
                'profit_analysis': self._get_profit_analysis(project)
            })
        else:
            # Limited view for clients
            context.update({
                'financial_data': {
                    'contract_value': financial_data['contract_value'],
                    'invoiced_amount': financial_data['invoiced_amount'],
                    'paid_amount': financial_data['paid_amount'],
                    'outstanding_balance': financial_data['outstanding_balance']
                },
                'is_client_view': True
            })
        
        return context
    
    def _get_detailed_cost_breakdown(self, project):
        """Get detailed cost breakdown"""
        breakdown = {
            'labor_cost': 0,
            'material_cost': 0,
            'equipment_cost': 0,
            'travel_cost': 0,
            'overhead_cost': 0
        }
        
        # Calculate from project items
        material_costs = project.calculate_material_costs()
        breakdown['material_cost'] = material_costs.get('total_cost', 0)
        breakdown['travel_cost'] = material_costs.get('travel_cost', 0)
        
        # Estimate labor costs (this would integrate with time tracking)
        if project.estimated_cost and breakdown['material_cost']:
            breakdown['labor_cost'] = project.estimated_cost - breakdown['material_cost'] - breakdown['travel_cost']
        
        return breakdown
    
    def _get_profit_analysis(self, project):
        """Analyze project profitability"""
        analysis = {
            'gross_profit': 0,
            'net_profit': 0,
            'roi_percentage': 0,
            'break_even_point': 0
        }
        
        if project.contract_value and project.estimated_cost:
            analysis['gross_profit'] = project.contract_value - project.estimated_cost
            analysis['net_profit'] = analysis['gross_profit'] * 0.85  # Approximate after overhead
            analysis['roi_percentage'] = (analysis['gross_profit'] / project.estimated_cost) * 100
            analysis['break_even_point'] = project.estimated_cost / project.contract_value * 100
        
        return analysis

# ============================================
# Financial Utility Views
# ============================================

class CalculateMaterialCostsView(ProjectAccessMixin, View):
    """Return material cost calculations for a project as JSON."""

    def get(self, request, job_number):
        project = get_object_or_404(Project, job_number=job_number)
        costs = project.calculate_material_costs()
        return JsonResponse({'success': True, 'costs': costs})


class ProjectInvoiceView(ProjectAccessMixin, View):
    """Placeholder view for project invoices."""

    def get(self, request, job_number):
        project = get_object_or_404(Project, job_number=job_number)
        return HttpResponse(f"Invoice page for {project.job_number}")


class ProjectPaymentView(ProjectAccessMixin, View):
    """Placeholder view for project payments."""

    def get(self, request, job_number):
        project = get_object_or_404(Project, job_number=job_number)
        return HttpResponse(f"Payment page for {project.job_number}")

# ============================================
# Scope of Work Views
# ============================================

class ScopeOfWorkListView(ProjectAccessMixin, ListView):
    """List scope items for a project"""
    model = ScopeOfWork
    template_name = 'project/scope_list.html'
    context_object_name = 'scope_items'

    def get_queryset(self):
        self.project = get_object_or_404(Project, job_number=self.kwargs['job_number'])
        return self.project.scope_items.all().order_by('priority', 'area')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context

class ScopeOfWorkCreateView(ProjectAccessMixin, CreateView):
    """Create new scope of work item"""
    model = ScopeOfWork
    form_class = ScopeOfWorkForm
    template_name = 'project/scope_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, job_number=kwargs['job_number'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'project': self.project}
        return kwargs
    
    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.material_type = 'device'
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context
    
    def get_success_url(self):
        return reverse('project:scope-list', kwargs={'job_number': self.project.job_number})

class ScopeOfWorkUpdateView(ProjectAccessMixin, UpdateView):
    """Update scope of work item"""
    model = ScopeOfWork
    form_class = ScopeOfWorkForm
    template_name = 'project/scope_form.html'
    
    def get_success_url(self):
        return reverse('project:scope-list', kwargs={'job_number': self.object.project.job_number})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        return context

class ScopeOfWorkDetailView(ProjectAccessMixin, DetailView):
    """Detailed view of scope item"""
    model = ScopeOfWork
    template_name = 'project/scope_detail.html'
    context_object_name = 'scope_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        return context

class ScopeOfWorkDeleteView(ProjectAccessMixin, DeleteView):
    """Delete scope of work item"""
    model = ScopeOfWork
    template_name = 'project/scope_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        return context
    
    def get_success_url(self):
        return reverse('project:scope-list', kwargs={'job_number': self.object.project.job_number})

# ============================================
# Material Management Views
# ============================================

class ProjectMaterialsView(ProjectAccessMixin, DetailView):
    """Overview of all project materials"""
    model = Project
    template_name = 'project/project_materials.html'
    slug_field = 'job_number'
    slug_url_kwarg = 'job_number'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        
        # Get all material types
        context.update({
            'devices': project.device_items,
            'hardware_items': project.hardware_items,
            'software_items': project.software_items,
            'license_items': project.license_items,
            'travel_items': project.travel_items,
            'material_summary': self._get_material_summary(project)
        })
        
        return context
    
    def _get_material_summary(self, project):
        """Get summary of all materials"""
        try:
            costs = project.calculate_material_costs()
            return {
                'total_items': (
                    project.device_items.count() +
                    project.hardware_items.count() +
                    project.software_items.count() +
                    project.license_items.count() +
                    project.travel_items.count()
                ),
                'total_cost': costs.get('total_cost', 0),
                'cost_breakdown': costs
            }
        except:
            return {'total_items': 0, 'total_cost': 0, 'cost_breakdown': {}}

# Device Management Views
class ProjectDeviceListView(ProjectAccessMixin, ListView):
    """List project devices"""
    model = ProjectMaterial
    template_name = 'project/device_list.html'
    context_object_name = 'devices'
    
    def get_queryset(self):
        self.project = get_object_or_404(Project, job_number=self.kwargs['job_number'])
        return self.project.device_items.select_related('product', 'task')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context

class ProjectDeviceCreateView(ProjectAccessMixin, CreateView):
    """Add device to project"""
    model = ProjectMaterial
    form_class = DeviceForm
    template_name = 'project/device_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, job_number=kwargs['job_number'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proj'] = self.project.job_number
        return kwargs
    
    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.material_type = 'device'
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('project:device-list', kwargs={'job_number': self.project.job_number})

class ProjectDeviceDetailView(DetailView):
    """Device detail view"""
    model = ProjectMaterial
    template_name = 'project/device_detail.html'
    context_object_name = 'device_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['material_type'] = 'Device'
        context['list_url_name'] = 'project:device-list'
        context['edit_url_name'] = 'project:device-edit'
        context['delete_url_name'] = 'project:device-delete'
        return context

class ProjectDeviceUpdateView(UpdateView):
    """Update project device"""
    model = ProjectMaterial
    form_class = DeviceForm
    template_name = 'project/device_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proj'] = self.object.project.job_number
        return kwargs
    
    def get_success_url(self):
        return reverse('project:device-list', kwargs={'job_number': self.object.project.job_number})

class ProjectDeviceDeleteView(DeleteView):
    """Delete project device"""
    model = ProjectMaterial
    template_name = 'project/device_confirm_delete.html'

    def get_success_url(self):
        return reverse('project:device-list', kwargs={'job_number': self.object.project.job_number})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['material_type'] = 'Device'
        context['list_url_name'] = 'project:device-list'
        return context

# Additional material views for hardware, software, licenses, and travel

class ProjectHardwareListView(ProjectAccessMixin, ListView):
    """List project hardware"""
    model = ProjectMaterial
    template_name = 'project/device_list.html'
    context_object_name = 'hardware_items'

    def get_queryset(self):
        self.project = get_object_or_404(Project, job_number=self.kwargs['job_number'])
        return self.project.hardware_items.select_related('product', 'task')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['materials'] = self.object_list
        context['material_type'] = 'Hardware'
        context['create_url'] = reverse('project:hardware-create', kwargs={'job_number': self.project.job_number})
        context['edit_url_name'] = 'project:hardware-edit'
        context['delete_url_name'] = 'project:hardware-delete'
        return context

class ProjectHardwareCreateView(ProjectAccessMixin, CreateView):
    """Add hardware to project"""
    model = ProjectMaterial
    form_class = HardwareForm
    template_name = 'project/device_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, job_number=kwargs['job_number'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proj'] = self.project.job_number
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['material_type'] = 'Travel'
        context['list_url_name'] = 'project:travel-list'
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['material_type'] = 'License'
        context['list_url_name'] = 'project:license-list'
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['material_type'] = 'Software'
        context['list_url_name'] = 'project:software-list'
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['material_type'] = 'Hardware'
        context['list_url_name'] = 'project:hardware-list'
        return context

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.material_type = 'hardware'
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project:hardware-list', kwargs={'job_number': self.project.job_number})

class ProjectHardwareDetailView(DetailView):
    """Hardware detail view"""
    model = ProjectMaterial
    template_name = 'project/device_detail.html'
    context_object_name = 'hardware_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['material_type'] = 'Hardware'
        context['list_url_name'] = 'project:hardware-list'
        context['edit_url_name'] = 'project:hardware-edit'
        context['delete_url_name'] = 'project:hardware-delete'
        return context

class ProjectHardwareUpdateView(UpdateView):
    """Update project hardware"""
    model = ProjectMaterial
    form_class = HardwareForm
    template_name = 'project/device_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proj'] = self.object.project.job_number
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        context['material_type'] = 'Travel'
        context['list_url_name'] = 'project:travel-list'
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        context['material_type'] = 'License'
        context['list_url_name'] = 'project:license-list'
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        context['material_type'] = 'Software'
        context['list_url_name'] = 'project:software-list'
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        context['material_type'] = 'Hardware'
        context['list_url_name'] = 'project:hardware-list'
        return context

    def get_success_url(self):
        return reverse('project:hardware-list', kwargs={'job_number': self.object.project.job_number})

class ProjectHardwareDeleteView(DeleteView):
    """Delete project hardware"""
    model = ProjectMaterial
    template_name = 'project/device_confirm_delete.html'

    def get_success_url(self):
        return reverse('project:hardware-list', kwargs={'job_number': self.object.project.job_number})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['material_type'] = 'Hardware'
        context['list_url_name'] = 'project:hardware-list'
        return context


class ProjectSoftwareListView(ProjectAccessMixin, ListView):
    """List project software"""
    model = ProjectMaterial
    template_name = 'project/device_list.html'
    context_object_name = 'software_items'

    def get_queryset(self):
        self.project = get_object_or_404(Project, job_number=self.kwargs['job_number'])
        return self.project.software_items.select_related('product', 'task')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['materials'] = self.object_list
        context['material_type'] = 'Software'
        context['create_url'] = reverse('project:software-create', kwargs={'job_number': self.project.job_number})
        context['edit_url_name'] = 'project:software-edit'
        context['delete_url_name'] = 'project:software-delete'
        return context

class ProjectSoftwareCreateView(ProjectAccessMixin, CreateView):
    """Add software to project"""
    model = ProjectMaterial
    form_class = SoftwareForm
    template_name = 'project/device_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, job_number=kwargs['job_number'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proj'] = self.project.job_number
        return kwargs

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.material_type = 'software'
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project:software-list', kwargs={'job_number': self.project.job_number})

class ProjectSoftwareDetailView(DetailView):
    """Software detail view"""
    model = ProjectMaterial
    template_name = 'project/device_detail.html'
    context_object_name = 'software_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['material_type'] = 'Software'
        context['list_url_name'] = 'project:software-list'
        context['edit_url_name'] = 'project:software-edit'
        context['delete_url_name'] = 'project:software-delete'
        return context

class ProjectSoftwareUpdateView(UpdateView):
    """Update project software"""
    model = ProjectMaterial
    form_class = SoftwareForm
    template_name = 'project/device_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proj'] = self.object.project.job_number
        return kwargs

    def get_success_url(self):
        return reverse('project:software-list', kwargs={'job_number': self.object.project.job_number})

class ProjectSoftwareDeleteView(DeleteView):
    """Delete project software"""
    model = ProjectMaterial
    template_name = 'project/device_confirm_delete.html'

    def get_success_url(self):
        return reverse('project:software-list', kwargs={'job_number': self.object.project.job_number})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['material_type'] = 'Software'
        context['list_url_name'] = 'project:software-list'
        return context


class ProjectLicenseListView(ProjectAccessMixin, ListView):
    """List project licenses"""
    model = ProjectMaterial
    template_name = 'project/device_list.html'
    context_object_name = 'license_items'

    def get_queryset(self):
        self.project = get_object_or_404(Project, job_number=self.kwargs['job_number'])
        return self.project.license_items.select_related('product', 'task')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['materials'] = self.object_list
        context['material_type'] = 'License'
        context['create_url'] = reverse('project:license-create', kwargs={'job_number': self.project.job_number})
        context['edit_url_name'] = 'project:license-edit'
        context['delete_url_name'] = 'project:license-delete'
        return context

class ProjectLicenseCreateView(ProjectAccessMixin, CreateView):
    """Add license to project"""
    model = ProjectMaterial
    form_class = LicenseForm
    template_name = 'project/device_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, job_number=kwargs['job_number'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proj'] = self.project.job_number
        return kwargs

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.material_type = 'license'
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project:license-list', kwargs={'job_number': self.project.job_number})

class ProjectLicenseDetailView(DetailView):
    """License detail view"""
    model = ProjectMaterial
    template_name = 'project/device_detail.html'
    context_object_name = 'license_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['material_type'] = 'License'
        context['list_url_name'] = 'project:license-list'
        context['edit_url_name'] = 'project:license-edit'
        context['delete_url_name'] = 'project:license-delete'
        return context

class ProjectLicenseUpdateView(UpdateView):
    """Update project license"""
    model = ProjectMaterial
    form_class = LicenseForm
    template_name = 'project/device_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proj'] = self.object.project.job_number
        return kwargs

    def get_success_url(self):
        return reverse('project:license-list', kwargs={'job_number': self.object.project.job_number})

class ProjectLicenseDeleteView(DeleteView):
    """Delete project license"""
    model = ProjectMaterial
    template_name = 'project/device_confirm_delete.html'

    def get_success_url(self):
        return reverse('project:license-list', kwargs={'job_number': self.object.project.job_number})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['material_type'] = 'License'
        context['list_url_name'] = 'project:license-list'
        return context


class ProjectTravelListView(ProjectAccessMixin, ListView):
    """List project travel items"""
    model = ProjectMaterial
    template_name = 'project/device_list.html'
    context_object_name = 'travel_items'

    def get_queryset(self):
        self.project = get_object_or_404(Project, job_number=self.kwargs['job_number'])
        return self.project.travel_items.select_related('product', 'task')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['materials'] = self.object_list
        context['material_type'] = 'Travel'
        context['create_url'] = reverse('project:travel-create', kwargs={'job_number': self.project.job_number})
        context['edit_url_name'] = 'project:travel-edit'
        context['delete_url_name'] = 'project:travel-delete'
        return context

class ProjectTravelCreateView(ProjectAccessMixin, CreateView):
    """Add travel item to project"""
    model = ProjectMaterial
    form_class = TravelForm
    template_name = 'project/device_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, job_number=kwargs['job_number'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proj'] = self.project.job_number
        return kwargs

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.material_type = 'travel'
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project:travel-list', kwargs={'job_number': self.project.job_number})

class ProjectTravelDetailView(DetailView):
    """Travel item detail view"""
    model = ProjectMaterial
    template_name = 'project/device_detail.html'
    context_object_name = 'travel_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['material_type'] = 'Travel'
        context['list_url_name'] = 'project:travel-list'
        context['edit_url_name'] = 'project:travel-edit'
        context['delete_url_name'] = 'project:travel-delete'
        return context

class ProjectTravelUpdateView(UpdateView):
    """Update travel item"""
    model = ProjectMaterial
    form_class = TravelForm
    template_name = 'project/device_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proj'] = self.object.project.job_number
        return kwargs

    def get_success_url(self):
        return reverse('project:travel-list', kwargs={'job_number': self.object.project.job_number})

class ProjectTravelDeleteView(DeleteView):
    """Delete travel item"""
    model = ProjectMaterial
    template_name = 'project/device_confirm_delete.html'

    def get_success_url(self):
        return reverse('project:travel-list', kwargs={'job_number': self.object.project.job_number})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['material_type'] = 'Travel'
        context['list_url_name'] = 'project:travel-list'
        return context

# ============================================
# Project Changes and Milestones
# ============================================

class ProjectChangeListView(ProjectAccessMixin, ListView):
    """List project changes"""
    model = ProjectChange
    template_name = 'project/change_list.html'
    context_object_name = 'changes'
    
    def get_queryset(self):
        self.project = get_object_or_404(Project, job_number=self.kwargs['job_number'])
        return self.project.changes.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context

class ProjectChangeCreateView(ProjectAccessMixin, CreateView):
    """Create project change request"""
    model = ProjectChange
    fields = ['change_type', 'description', 'cost_impact', 'schedule_impact_days']
    template_name = 'project/change_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, job_number=kwargs['job_number'])
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.requested_by = self.request.user.username
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('project:change-list', kwargs={'job_number': self.project.job_number})

class ProjectChangeApproveView(ProjectAccessMixin, View):
    """Approve/reject change request"""
    
    def post(self, request, pk):
        change = get_object_or_404(ProjectChange, pk=pk)
        
        # Check approval permissions
        if not request.user.role in ['admin', 'project_manager']:
            raise PermissionDenied("You don't have permission to approve changes")
        
        action = request.POST.get('action')
        if action == 'approve':
            change.is_approved = True
            change.approved_by = request.user.username
            change.approved_date = timezone.now().date()
            change.save()
            
            # Apply change impacts
            if change.cost_impact:
                change.project.estimated_cost = (change.project.estimated_cost or 0) + change.cost_impact
                change.project.save()
            
            messages.success(request, 'Change request approved successfully')
        elif action == 'reject':
            change.delete()
            messages.info(request, 'Change request rejected and removed')
        
        return redirect('project:change-list', job_number=change.project.job_number)

class ProjectMilestoneListView(ProjectAccessMixin, ListView):
    """List project milestones"""
    model = ProjectMilestone
    template_name = 'project/milestone_list.html'
    context_object_name = 'milestones'
    
    def get_queryset(self):
        self.project = get_object_or_404(Project, job_number=self.kwargs['job_number'])
        return self.project.milestones.order_by('target_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context

class ProjectMilestoneCreateView(ProjectAccessMixin, CreateView):
    """Create project milestone"""
    model = ProjectMilestone
    fields = ['name', 'description', 'target_date', 'is_critical']
    template_name = 'project/milestone_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, job_number=kwargs['job_number'])
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.project = self.project
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('project:milestone-list', kwargs={'job_number': self.project.job_number})

class ProjectMilestoneCompleteView(ProjectAccessMixin, View):
    """Mark milestone as complete"""
    
    def post(self, request, pk):
        milestone = get_object_or_404(ProjectMilestone, pk=pk)
        
        milestone.is_complete = True
        milestone.actual_date = timezone.now().date()
        milestone.save()
        
        messages.success(request, f'Milestone "{milestone.name}" marked as complete')
        return redirect('project:milestone-list', job_number=milestone.project.job_number)

# ============================================
# Team Management Views
# ============================================

class ProjectTeamView(ProjectAccessMixin, DetailView):
    """Project team management"""
    model = Project
    template_name = 'project/project_team.html'
    slug_field = 'job_number'
    slug_url_kwarg = 'job_number'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        
        # Available team members (not already on project)
        available_members = User.objects.filter(
            Q(roles__contains=['worker']) |
            Q(roles__contains=['supervisor'])
        ).exclude(
            id__in=project.team_members.values_list('id', flat=True)
        )
        
        # Available team leads
        available_leads = User.objects.filter(
            Q(roles__contains=['supervisor']) |
            Q(roles__contains=['project_manager'])
        ).exclude(
            id__in=project.team_leads.values_list('id', flat=True)
        )
        
        context.update({
            'available_members': available_members,
            'available_leads': available_leads,
            'can_manage_team': self._can_manage_team(project, self.request.user)
        })
        
        return context
    
    def _can_manage_team(self, project, user):
        """Check if user can manage team"""
        return (user.role in ['admin', 'project_manager'] and 
                (project.project_manager == user or user.role == 'admin'))

class ProjectTeamAssignView(ProjectAccessMixin, View):
    """Assign team members to project"""
    
    def post(self, request, job_number):
        project = get_object_or_404(Project, job_number=job_number)
        
        # Check permissions
        if not self._can_manage_team(project, request.user):
            raise PermissionDenied("You don't have permission to manage this team")
        
        member_ids = request.POST.getlist('members')
        lead_ids = request.POST.getlist('leads')
        
        with transaction.atomic():
            # Add team members
            for member_id in member_ids:
                try:
                    user = User.objects.get(id=member_id)
                    project.team_members.add(user)
                except User.DoesNotExist:
                    pass
            
            # Add team leads
            for lead_id in lead_ids:
                try:
                    user = User.objects.get(id=lead_id)
                    project.team_leads.add(user)
                except User.DoesNotExist:
                    pass
        
        messages.success(request, 'Team members assigned successfully')
        return redirect('project:project-team', job_number=job_number)
    
    def _can_manage_team(self, project, user):
        """Check if user can manage team"""
        return (user.role in ['admin', 'project_manager'] and 
                (project.project_manager == user or user.role == 'admin'))

class MyProjectAssignmentsView(LoginRequiredMixin, ListView):
    """User's project assignments"""
    model = Project
    template_name = 'project/my_assignments.html'
    context_object_name = 'projects'
    
    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(
            Q(team_members=user) |
            Q(team_leads=user) |
            Q(project_manager=user) |
            Q(supervisor=user)
        ).distinct().select_related(
            'location', 'project_manager'
        ).order_by('-updated_at')

# ============================================
# API Views for AJAX/Frontend
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_search_api(request):
    """API endpoint for project search"""
    query = request.GET.get('q', '')
    limit = int(request.GET.get('limit', 10))
    
    if not query:
        return Response([])
    
    projects = Project.objects.filter(
        Q(job_number__icontains=query) |
        Q(name__icontains=query) |
        Q(location__name__icontains=query)
    )[:limit]
    
    results = []
    for project in projects:
        results.append({
            'id': project.id,
            'job_number': project.job_number,
            'name': project.name,
            'location': project.location.name if project.location else '',
            'status': project.status,
            'url': reverse('project:project-detail', kwargs={'job_number': project.job_number})
        })
    
    return Response(results)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats_api(request):
    """API endpoint for dashboard statistics"""
    user = request.user
    cache_key = f'dashboard_stats_{user.id}'
    
    stats = cache.get(cache_key)
    if not stats:
        projects = Project.objects.all()  # Apply user filtering as needed
        
        stats = {
            'total_projects': projects.count(),
            'active_projects': projects.filter(status='active').count(),
            'completed_projects': projects.filter(status='complete').count(),
            'overdue_projects': projects.filter(
                due_date__lt=date.today(),
                status__in=['active', 'installing']
            ).count(),
        }
        
        cache.set(cache_key, stats, 60 * 5)  # 5 minutes
    
    return Response(stats)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def project_quick_update_api(request, job_number):
    """API endpoint for quick project updates"""
    project = get_object_or_404(Project, job_number=job_number)
    
    # Check permissions
    if not request.user.role in ['admin', 'project_manager'] and project.project_manager != request.user:
        return Response({'error': 'Permission denied'}, status=403)
    
    # Update allowed fields
    allowed_fields = ['status', 'percent_complete', 'priority']
    updated_fields = []
    
    for field in allowed_fields:
        if field in request.data:
            setattr(project, field, request.data[field])
            updated_fields.append(field)
    
    if updated_fields:
        project.save()
        return Response({
            'success': True,
            'updated_fields': updated_fields,
            'message': 'Project updated successfully'
        })
    
    return Response({'error': 'No valid fields to update'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_costs_api(request, job_number):
    """API endpoint to calculate project costs"""
    project = get_object_or_404(Project, job_number=job_number)
    
    try:
        costs = project.calculate_material_costs()
        return Response({
            'success': True,
            'costs': costs
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


class CalculateCostsAPIView(ProjectAccessMixin, APIView):
    """API view for calculating material costs."""

    permission_classes = [IsAuthenticated]

    def post(self, request, job_number=None):
        project = get_object_or_404(Project, job_number=job_number)
        try:
            costs = project.calculate_material_costs()
            return Response({'success': True, 'costs': costs})
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=500)

# ============================================
# DRF API Views utilizing serializers
# ============================================

class ProjectListAPIView(ProjectPermissionMixin, generics.ListAPIView):
    """List projects using the DRF serializer"""
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_required = 'project.view_project'


class ProjectDetailAPIView(ProjectAccessMixin, ProjectPermissionMixin, generics.RetrieveAPIView):
    """Retrieve a single project using the serializer"""
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'job_number'
    permission_required = 'project.view_project'


class ScopeOfWorkListAPIView(ProjectPermissionMixin, generics.ListAPIView):
    """List scope of work items"""
    queryset = ScopeOfWork.objects.all()
    serializer_class = ScopeOfWorkSerializer
    permission_required = 'project.view_scopeofwork'

# ============================================
# Report and Analytics Views
# ============================================

class ProjectReportsView(LoginRequiredMixin, TemplateView):
    """Project reports dashboard"""
    template_name = 'project/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Available reports
        context['available_reports'] = [
            {
                'name': 'Financial Report',
                'description': 'Project financial performance and profitability',
                'url': reverse('project:financial-report'),
                'icon': 'fa-chart-line'
            },
            {
                'name': 'Progress Report',
                'description': 'Project progress and completion status',
                'url': reverse('project:progress-report'),
                'icon': 'fa-tasks'
            },
            {
                'name': 'Team Performance',
                'description': 'Team productivity and assignments',
                'url': reverse('project:team-performance'),
                'icon': 'fa-users'
            },
            {
                'name': 'Resource Utilization',
                'description': 'Resource allocation and utilization',
                'url': reverse('project:utilization-report'),
                'icon': 'fa-chart-pie'
            }
        ]
        
        return context

class FinancialReportView(LoginRequiredMixin, TemplateView):
    """Financial performance report"""
    template_name = 'project/reports/financial_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Date range filtering
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        queryset = Project.objects.all()
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(start_date__lte=date_to)
        
        # Financial aggregations
        financial_summary = queryset.aggregate(
            total_contract_value=Sum('contract_value'),
            total_estimated_cost=Sum('estimated_cost'),
            total_invoiced=Sum('invoiced_amount'),
            total_paid=Sum('paid_amount'),
            avg_profit_margin=Avg(
                Case(
                    When(contract_value__gt=0, then=(
                        F('contract_value') - F('estimated_cost')
                    ) * 100 / F('contract_value')),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ),
            project_count=Count('id')
        )
        
        # Profitability by status
        status_profitability = queryset.values('status').annotate(
            count=Count('id'),
            total_value=Sum('contract_value'),
            total_cost=Sum('estimated_cost'),
            avg_margin=Avg(
                Case(
                    When(contract_value__gt=0, then=(
                        F('contract_value') - F('estimated_cost')
                    ) * 100 / F('contract_value')),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
        ).order_by('-total_value')
        
        # Monthly financial trends
        monthly_trends = self._calculate_monthly_trends(queryset)
        
        # Top performing projects
        top_projects = queryset.filter(
            contract_value__isnull=False,
            estimated_cost__isnull=False
        ).annotate(
            profit=F('contract_value') - F('estimated_cost'),
            margin=Case(
                When(contract_value__gt=0, then=(
                    F('contract_value') - F('estimated_cost')
                ) * 100 / F('contract_value')),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('-profit')[:10]
        
        context.update({
            'financial_summary': financial_summary,
            'status_profitability': status_profitability,
            'monthly_trends': monthly_trends,
            'top_projects': top_projects,
            'date_from': date_from,
            'date_to': date_to
        })
        
        return context
    
    def _calculate_monthly_trends(self, queryset):
        """Calculate monthly financial trends"""
        from django.db.models.functions import TruncMonth
        
        return queryset.annotate(
            month=TruncMonth('start_date')
        ).values('month').annotate(
            project_count=Count('id'),
            total_value=Sum('contract_value'),
            total_cost=Sum('estimated_cost')
        ).order_by('month')

class ProgressReportView(LoginRequiredMixin, TemplateView):
    """Project progress report"""
    template_name = 'project/reports/progress_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        projects = Project.objects.select_related('project_manager').annotate(
            task_count=Count('task_lists__tasks', distinct=True),
            completed_tasks=Count(
                'task_lists__tasks',
                filter=Q(task_lists__tasks__completed=True),
                distinct=True,
            ),
            milestone_count=Count('milestones'),
            completed_milestones=Count('milestones', filter=Q(milestones__is_complete=True))
        )
        
        # Progress statistics
        progress_stats = {
            'total_projects': projects.count(),
            'on_track': projects.filter(percent_complete__gte=50).count(),
            'behind_schedule': projects.filter(
                due_date__lt=date.today() + timedelta(days=30),
                percent_complete__lt=75
            ).count(),
            'avg_completion': projects.aggregate(avg=Avg('percent_complete'))['avg'] or 0
        }
        
        # Projects by completion range
        completion_ranges = [
            ('0-25%', projects.filter(percent_complete__lt=25).count()),
            ('25-50%', projects.filter(percent_complete__gte=25, percent_complete__lt=50).count()),
            ('50-75%', projects.filter(percent_complete__gte=50, percent_complete__lt=75).count()),
            ('75-100%', projects.filter(percent_complete__gte=75).count()),
        ]
        
        # Manager performance
        manager_performance = projects.values(
            'project_manager__username', 'project_manager__first_name', 'project_manager__last_name'
        ).annotate(
            project_count=Count('id'),
            avg_completion=Avg('percent_complete'),
            on_time_projects=Count('id', filter=Q(
                completed_date__lte=F('due_date')
            ))
        ).order_by('-avg_completion')
        
        context.update({
            'progress_stats': progress_stats,
            'completion_ranges': completion_ranges,
            'manager_performance': manager_performance,
            'recent_completions': projects.filter(
                status='complete',
                completed_date__gte=date.today() - timedelta(days=30)
            ).order_by('-completed_date')[:10]
        })
        
        return context

class TeamPerformanceReportView(LoginRequiredMixin, TemplateView):
    """Team performance and productivity report"""
    template_name = 'project/reports/team_performance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Team member statistics
        team_stats = User.objects.filter(
            Q(roles__contains=['worker']) |
            Q(roles__contains=['supervisor']) |
            Q(roles__contains=['project_manager'])
        ).annotate(
            active_projects=Count('assigned_projects', filter=Q(
                assigned_projects__status__in=['active', 'installing']
            )),
            total_projects=Count('assigned_projects'),
            managed_projects=Count('managed_projects'),
            avg_project_completion=Avg('assigned_projects__percent_complete')
        ).order_by('-active_projects')
        
        # Department/role performance
        role_performance = User.objects.values('role').annotate(
            member_count=Count('id'),
            active_projects=Count('assigned_projects', filter=Q(
                assigned_projects__status__in=['active', 'installing']
            )),
            avg_completion=Avg('assigned_projects__percent_complete')
        ).order_by('-member_count')
        
        # Workload distribution
        workload_data = self._calculate_workload_distribution()
        
        context.update({
            'team_stats': team_stats,
            'role_performance': role_performance,
            'workload_data': workload_data
        })
        
        return context
    
    def _calculate_workload_distribution(self):
        """Calculate team workload distribution"""
        # This would integrate with your task/time tracking system
        return {
            'overloaded_members': [],  # Members with >40 hours/week
            'underutilized_members': [],  # Members with <20 hours/week
            'optimal_load_members': [],  # Members with 20-40 hours/week
        }

class ResourceUtilizationReportView(LoginRequiredMixin, TemplateView):
    """Resource utilization report"""
    template_name = 'project/reports/utilization_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Equipment/resource utilization would be calculated here
        # This depends on your asset management integration
        
        context.update({
            'equipment_utilization': [],
            'material_usage': [],
            'resource_conflicts': []
        })
        
        return context

# ============================================
# Export and Import Views
# ============================================

class ProjectExportView(LoginRequiredMixin, View):
    """Export projects to various formats"""
    
    def get(self, request):
        format_type = request.GET.get('format', 'csv')
        project_ids = request.GET.getlist('projects')
        
        if project_ids:
            projects = Project.objects.filter(id__in=project_ids)
        else:
            projects = Project.objects.all()
        
        if format_type == 'csv':
            return self._export_csv(projects)
        elif format_type == 'excel':
            return self._export_excel(projects)
        elif format_type == 'pdf':
            return self._export_pdf(projects)
        
        return JsonResponse({'error': 'Invalid format'}, status=400)
    
    def _export_csv(self, projects):
        """Export to CSV format"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="projects.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Job Number', 'Name', 'Status', 'Manager', 'Start Date', 
            'Due Date', 'Contract Value', 'Estimated Cost', 'Progress'
        ])
        
        for project in projects:
            writer.writerow([
                project.job_number,
                project.name,
                project.status,
                project.project_manager.get_full_name() if project.project_manager else '',
                project.start_date,
                project.due_date,
                project.contract_value,
                project.estimated_cost,
                f"{project.percent_complete}%"
            ])
        
        return response
    
    def _export_excel(self, projects):
        """Export to Excel format"""
        # Implementation would use openpyxl or similar
        pass
    
    def _export_pdf(self, projects):
        """Export to PDF format"""
        # Implementation would use reportlab or similar
        pass

class ProjectPDFExportView(ProjectAccessMixin, DetailView):
    """Export single project to PDF"""
    model = Project
    slug_field = 'job_number'
    slug_url_kwarg = 'job_number'
    
    def get(self, request, *args, **kwargs):
        project = self.get_object()
        
        # Use the render utility for PDF generation
        from .render import Render
        
        params = {
            'project': project,
            'today': date.today(),
            'user': request.user
        }
        
        return Render.render('project/pdf/project_detail.html', params)

# ============================================
# Utility and Management Views
# ============================================

class GenerateJobNumberView(LoginRequiredMixin, View):
    """Generate new job number"""
    
    def get(self, request):
        business_category_id = request.GET.get('business_category')
        business_category = None
        
        if business_category_id:
            from location.models import BusinessCategory
            business_category = BusinessCategory.objects.filter(id=business_category_id).first()
        
        job_number = generate_job_number(business_category)
        
        return JsonResponse({'job_number': job_number})

class ProjectValidationView(LoginRequiredMixin, View):
    """Validate project data"""
    
    def post(self, request):
        job_number = request.POST.get('job_number')
        
        # Check if job number already exists
        exists = Project.objects.filter(job_number=job_number).exists()
        
        return JsonResponse({
            'valid': not exists,
            'message': 'Job number already exists' if exists else 'Job number is available'
        })

class QuickActionsView(LoginRequiredMixin, TemplateView):
    """Quick actions dashboard"""
    template_name = 'project/quick_actions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Role-specific quick actions
        actions = []
        
        if user.role in ['admin', 'project_manager']:
            actions.extend([
                {'title': 'Create New Project', 'url': reverse('project:project-create'), 'icon': 'fa-plus', 'color': 'primary'},
                {'title': 'Pending Approvals', 'url': reverse('project:change-list'), 'icon': 'fa-check', 'color': 'warning'},
                {'title': 'Financial Report', 'url': reverse('project:financial-report'), 'icon': 'fa-chart-line', 'color': 'success'},
            ])
        
        actions.extend([
            {'title': 'My Assignments', 'url': reverse('project:my-assignments'), 'icon': 'fa-tasks', 'color': 'info'},
            {'title': 'Recent Projects', 'url': reverse('project:project-list'), 'icon': 'fa-list', 'color': 'secondary'},
        ])
        
        context['quick_actions'] = actions
        return context

class RecentlyViewedProjectsView(LoginRequiredMixin, ListView):
    """Recently viewed projects"""
    model = Project
    template_name = 'project/recently_viewed.html'
    context_object_name = 'projects'
    
    def get_queryset(self):
        # This would integrate with a session-based tracking system
        # For now, return recent projects for the user
        return Project.objects.filter(
            Q(project_manager=self.request.user) |
            Q(team_members=self.request.user)
        ).distinct().order_by('-updated_at')[:10]

class ProjectSettingsView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Project module settings"""
    template_name = 'project/settings.html'
    permission_required = 'project.change_project'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Available settings
        context['settings_sections'] = [
            {
                'title': 'Default Values',
                'description': 'Set default values for new projects',
                'url': reverse('project:project-defaults'),
                'icon': 'fa-cog'
            },
            {
                'title': 'Business Categories',
                'description': 'Manage business category specific settings',
                'url': reverse('project:business-category-settings'),
                'icon': 'fa-building'
            }
        ]
        
        return context

# ============================================
# Calendar and Scheduling Views
# ============================================

class ProjectCalendarView(LoginRequiredMixin, TemplateView):
    """Project calendar view"""
    template_name = 'project/calendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calendar will be populated via AJAX
        context['calendar_sources'] = [
            {
                'title': 'Project Deadlines',
                'url': reverse('project:calendar-events') + '?type=deadlines',
                'color': '#dc3545'
            },
            {
                'title': 'Milestones',
                'url': reverse('project:calendar-events') + '?type=milestones',
                'color': '#007bff'
            },
            {
                'title': 'Start Dates',
                'url': reverse('project:calendar-events') + '?type=starts',
                'color': '#28a745'
            }
        ]
        
        return context

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_calendar_events_api(request):
    """API endpoint for calendar events"""
    event_type = request.GET.get('type', 'all')
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    events = []
    
    # Get user's projects
    user_projects = Project.objects.filter(
        Q(project_manager=request.user) |
        Q(team_members=request.user)
    ).distinct()
    
    if event_type in ['deadlines', 'all']:
        # Project deadlines
        for project in user_projects.filter(due_date__isnull=False):
            events.append({
                'title': f'{project.name} - Due',
                'start': project.due_date.isoformat(),
                'url': reverse('project:project-detail', kwargs={'job_number': project.job_number}),
                'color': '#dc3545',
                'textColor': 'white'
            })
    
    if event_type in ['milestones', 'all']:
        # Project milestones
        milestones = ProjectMilestone.objects.filter(
            project__in=user_projects,
            target_date__isnull=False
        )
        
        for milestone in milestones:
            events.append({
                'title': f'{milestone.project.name} - {milestone.name}',
                'start': milestone.target_date.isoformat(),
                'url': reverse('project:project-detail', kwargs={'job_number': milestone.project.job_number}),
                'color': '#007bff' if not milestone.is_complete else '#28a745',
                'textColor': 'white'
            })
    
    if event_type in ['starts', 'all']:
        # Project start dates
        for project in user_projects.filter(start_date__isnull=False):
            events.append({
                'title': f'{project.name} - Start',
                'start': project.start_date.isoformat(),
                'url': reverse('project:project-detail', kwargs={'job_number': project.job_number}),
                'color': '#28a745',
                'textColor': 'white'
            })
    
    return Response(events)

# ============================================
# Health Check and Status Views
# ============================================

class ProjectHealthCheckView(View):
    """System health check for project module"""
    
    def get(self, request):
        checks = {
            'database': self._check_database(),
            'cache': self._check_cache(),
            'permissions': self._check_permissions(),
            'business_logic': self._check_business_logic()
        }
        
        overall_status = all(check['status'] for check in checks.values())
        
        return JsonResponse({
            'status': 'healthy' if overall_status else 'unhealthy',
            'checks': checks,
            'timestamp': timezone.now().isoformat()
        })
    
    def _check_database(self):
        """Check database connectivity and basic queries"""
        try:
            Project.objects.count()
            return {'status': True, 'message': 'Database accessible'}
        except Exception as e:
            return {'status': False, 'message': f'Database error: {str(e)}'}
    
    def _check_cache(self):
        """Check cache functionality"""
        try:
            cache.set('health_check', 'ok', 60)
            value = cache.get('health_check')
            return {'status': value == 'ok', 'message': 'Cache functional' if value == 'ok' else 'Cache not working'}
        except Exception as e:
            return {'status': False, 'message': f'Cache error: {str(e)}'}
    
    def _check_permissions(self):
        """Check permission system"""
        try:
            # Basic permission check
            from django.contrib.auth.models import Permission
            Permission.objects.filter(content_type__app_label='project').exists()
            return {'status': True, 'message': 'Permissions configured'}
        except Exception as e:
            return {'status': False, 'message': f'Permission error: {str(e)}'}
    
    def _check_business_logic(self):
        """Check business logic functions"""
        try:
            # Test job number generation
            test_number = generate_job_number()
            return {'status': bool(test_number), 'message': 'Business logic functional'}
        except Exception as e:
            return {'status': False, 'message': f'Business logic error: {str(e)}'}

class SystemStatusView(LoginRequiredMixin, TemplateView):
    """System status dashboard"""
    template_name = 'project/system_status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # System statistics
        context['system_stats'] = {
            'total_projects': Project.objects.count(),
            'active_projects': Project.objects.filter(status='active').count(),
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'database_size': self._get_database_size(),
            'cache_usage': self._get_cache_usage()
        }
        
        # Recent activity
        context['recent_activity'] = self._get_recent_system_activity()
        
        return context
    
    def _get_database_size(self):
        """Get database size estimate"""
        # This would depend on your database backend
        return "N/A"
    
    def _get_cache_usage(self):
        """Get cache usage statistics"""
        # This would depend on your cache backend
        return "N/A"
    
    def _get_recent_system_activity(self):
        """Get recent system activity"""
        activities = []
        
        # Recent project creations
        recent_projects = Project.objects.order_by('-created_at')[:5]
        for project in recent_projects:
            activities.append({
                'type': 'project_created',
                'message': f'Project "{project.name}" created',
                'timestamp': project.created_at,
                'user': project.created_by
            })
        
        return sorted(activities, key=lambda x: x['timestamp'], reverse=True)

# ============================================
# Placeholder Views for Unimplemented Features
# ============================================

class PlaceholderView(LoginRequiredMixin, TemplateView):
    """Generic placeholder view until functionality is implemented."""
    template_name = 'project/placeholder.html'


class NotImplementedAPIView(APIView):
    """Simple API view returning a 501 response."""

    def get(self, request, *args, **kwargs):
        return Response({'detail': 'Not implemented'}, status=501)

    post = put = patch = delete = get


class ProjectChangeDetailView(PlaceholderView):
    pass


class ProjectChangeUpdateView(PlaceholderView):
    pass


class ProjectChangeDeleteView(PlaceholderView):
    pass


class ProjectMilestoneDetailView(PlaceholderView):
    pass


class ProjectMilestoneUpdateView(PlaceholderView):
    pass


class ProjectMilestoneDeleteView(PlaceholderView):
    pass


class ProjectTemplateListView(PlaceholderView):
    pass


class ProjectTemplateCreateView(PlaceholderView):
    pass


class ProjectTemplateDetailView(PlaceholderView):
    pass


class ProjectTemplateUpdateView(PlaceholderView):
    pass


class ProjectTemplateDeleteView(PlaceholderView):
    pass


class ProjectFromTemplateView(PlaceholderView):
    pass


class ProjectTeamRemoveView(PlaceholderView):
    pass


class FavoriteProjectsView(PlaceholderView):
    pass


class ToggleFavoriteView(PlaceholderView):
    pass


class ProjectDefaultsView(PlaceholderView):
    pass


class BusinessCategorySettingsView(PlaceholderView):
    pass


class ProjectExportSingleView(PlaceholderView):
    pass


class ProjectExcelExportView(PlaceholderView):
    pass


class ProjectImportView(PlaceholderView):
    pass


class ProjectScheduleView(PlaceholderView):
    pass


class ProjectValidationDetailView(PlaceholderView):
    pass


class ProjectAutocompleteView(NotImplementedAPIView):
    pass


class LocationAutocompleteView(NotImplementedAPIView):
    pass


class ProjectSearchAPIView(NotImplementedAPIView):
    pass


class ProjectQuickUpdateAPIView(NotImplementedAPIView):
    pass


class ProjectProgressUpdateAPIView(NotImplementedAPIView):
    pass


class ProjectStatusAPIView(NotImplementedAPIView):
    pass


class DashboardStatsAPIView(NotImplementedAPIView):
    pass


class ProjectNotificationsAPIView(NotImplementedAPIView):
    pass


class ProjectBulkUpdateAPIView(NotImplementedAPIView):
    pass


class ProjectBulkDeleteAPIView(NotImplementedAPIView):
    pass


class ProjectImageUploadAPIView(NotImplementedAPIView):
    pass


class ProjectDocumentUploadAPIView(NotImplementedAPIView):
    pass


class ProjectCalendarEventsAPIView(NotImplementedAPIView):
    pass

# ============================================
# Error Handling Views
# ============================================

def project_404_handler(request, exception):
    """Custom 404 handler for project views"""
    return render(request, 'project/errors/404.html', {
        'message': 'The requested project could not be found.',
        'suggestion': 'Please check the project number and try again.'
    }, status=404)

def project_403_handler(request, exception):
    """Custom 403 handler for project views"""
    return render(request, 'project/errors/403.html', {
        'message': 'You do not have permission to access this project.',
        'suggestion': 'Please contact your project manager for access.'
    }, status=403)

def project_500_handler(request):
    """Custom 500 handler for project views"""
    return render(request, 'project/errors/500.html', {
        'message': 'An internal server error occurred.',
        'suggestion': 'Please try again later or contact support.'
    }, status=500)
