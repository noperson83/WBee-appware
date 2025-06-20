# asset/views.py - Complete views for asset management
"""
Complete Django 5 views for universal asset management.
Includes all major functionality with proper error handling and permissions.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, 
    TemplateView, View, FormView
)
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse, Http404, HttpResponseRedirect
from django.db.models import Q, Count, Sum, Avg, F, Max
from django.core.paginator import Paginator
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError
import json
import csv
import io
import qrcode
from datetime import date, timedelta
from decimal import Decimal

# Import your models
from .models import (
    Asset, AssetCategory, AssetMaintenanceRecord, 
    AssetAssignment, AssetDepreciation
)
from .forms import (
    AssetForm, AssetBulkUpdateForm, AssetAssignmentForm,
    AssetMaintenanceForm, AssetSearchForm, AssetCategoryForm,
    AssetImportForm
)
from hr.models import Worker
from project.models import Project
from company.models import Office, Department


# ============================================================================
# DASHBOARD AND OVERVIEW VIEWS
# ============================================================================

class AssetDashboardView(LoginRequiredMixin, TemplateView):
    """Main asset management dashboard with analytics and overview."""
    template_name = 'asset/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's company assets
        user_company = getattr(self.request.user, 'company', None)
        if user_company:
            assets = Asset.objects.filter(company=user_company, is_active=True)
        else:
            assets = Asset.objects.filter(is_active=True)
        
        # Asset counts by category
        category_stats = assets.values('category__name').annotate(
            count=Count('id'),
            total_value=Sum('current_value')
        ).order_by('-count')
        
        # Asset status breakdown
        status_stats = assets.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Maintenance overview
        maintenance_due = assets.filter(
            next_maintenance_date__lte=date.today()
        ).count()
        
        maintenance_overdue = assets.filter(
            next_maintenance_date__lt=date.today()
        ).count()
        
        # Financial overview
        total_value = assets.aggregate(
            purchase_total=Sum('purchase_price'),
            current_total=Sum('current_value')
        )
        
        # Recent activity
        recent_assignments = AssetAssignment.objects.filter(
            asset__company=user_company if user_company else None,
            is_active=True
        ).select_related('asset', 'assigned_to_worker', 'assigned_to_project')[:5]
        
        recent_maintenance = AssetMaintenanceRecord.objects.filter(
            asset__company=user_company if user_company else None
        ).select_related('asset').order_by('-performed_date')[:5]
        
        context.update({
            'total_assets': assets.count(),
            'category_stats': category_stats,
            'status_stats': status_stats,
            'maintenance_due': maintenance_due,
            'maintenance_overdue': maintenance_overdue,
            'total_value': total_value,
            'recent_assignments': recent_assignments,
            'recent_maintenance': recent_maintenance,
            'available_assets': assets.filter(status='available').count(),
            'in_use_assets': assets.filter(status='in_use').count(),
        })
        
        return context


class AssetAnalyticsView(LoginRequiredMixin, TemplateView):
    """Advanced analytics and reporting for assets."""
    template_name = 'asset/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_company = getattr(self.request.user, 'company', None)
        assets = Asset.objects.filter(
            company=user_company if user_company else None,
            is_active=True
        )
        
        # Utilization analytics
        utilization_data = self.get_utilization_analytics(assets)
        
        # Depreciation analytics
        depreciation_data = self.get_depreciation_analytics(assets)
        
        # Maintenance analytics
        maintenance_data = self.get_maintenance_analytics(assets)
        
        # Cost analytics
        cost_data = self.get_cost_analytics(assets)
        
        context.update({
            'utilization_data': utilization_data,
            'depreciation_data': depreciation_data,
            'maintenance_data': maintenance_data,
            'cost_data': cost_data,
        })
        
        return context
    
    def get_utilization_analytics(self, assets):
        """Calculate asset utilization rates."""
        total_assets = assets.count()
        in_use = assets.filter(status='in_use').count()
        utilization_rate = (in_use / total_assets * 100) if total_assets > 0 else 0
        
        return {
            'utilization_rate': round(utilization_rate, 1),
            'in_use_count': in_use,
            'available_count': assets.filter(status='available').count(),
            'maintenance_count': assets.filter(status='maintenance').count(),
        }
    
    def get_depreciation_analytics(self, assets):
        """Calculate depreciation analytics."""
        with_purchase_price = assets.exclude(purchase_price__isnull=True)
        
        total_purchase = with_purchase_price.aggregate(Sum('purchase_price'))['purchase_price__sum'] or 0
        total_current = with_purchase_price.aggregate(Sum('current_value'))['current_value__sum'] or 0
        total_depreciation = total_purchase - total_current
        
        return {
            'total_purchase_value': total_purchase,
            'total_current_value': total_current,
            'total_depreciation': total_depreciation,
            'depreciation_rate': round((total_depreciation / total_purchase * 100) if total_purchase > 0 else 0, 1),
            'avg_asset_age': round(sum([asset.age_in_years for asset in assets]) / assets.count() if assets.count() > 0 else 0, 1),
        }
    
    def get_maintenance_analytics(self, assets):
        """Calculate maintenance analytics."""
        return {
            'overdue_maintenance': assets.filter(
                next_maintenance_date__lt=date.today()
            ).count(),
            'upcoming_maintenance': assets.filter(
                next_maintenance_date__range=[
                    date.today(),
                    date.today() + timedelta(days=30)
                ]
            ).count(),
            'avg_maintenance_cost': AssetMaintenanceRecord.objects.aggregate(
                avg_cost=Avg(F('labor_cost') + F('parts_cost') + F('external_cost'))
            )['avg_cost'] or 0,
            'total_maintenance_records': AssetMaintenanceRecord.objects.count(),
        }
    
    def get_cost_analytics(self, assets):
        """Calculate cost analytics."""
        return {
            'total_purchase_value': assets.aggregate(
                total=Sum('purchase_price')
            )['total'] or 0,
            'total_current_value': assets.aggregate(
                total=Sum('current_value')
            )['total'] or 0,
            'avg_asset_value': assets.aggregate(
                avg=Avg('current_value')
            )['avg'] or 0,
            'highest_value_asset': assets.order_by('-current_value').first(),
        }


class AssetReportsView(LoginRequiredMixin, TemplateView):
    """Asset reports and export functionality."""
    template_name = 'asset/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_company = getattr(self.request.user, 'company', None)
        assets = Asset.objects.filter(
            company=user_company if user_company else None,
            is_active=True
        )
        
        # Report options
        context.update({
            'total_assets': assets.count(),
            'categories': AssetCategory.objects.filter(is_active=True),
            'report_types': [
                ('inventory', 'Asset Inventory Report'),
                ('maintenance', 'Maintenance Report'),
                ('depreciation', 'Depreciation Report'),
                ('utilization', 'Utilization Report'),
                ('assignments', 'Assignment Report'),
            ]
        })
        
        return context


# ============================================================================
# ASSET CRUD VIEWS
# ============================================================================

class AssetListView(LoginRequiredMixin, ListView):
    """List all assets with filtering and search capabilities."""
    model = Asset
    template_name = 'asset/asset_list.html'
    context_object_name = 'assets'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Asset.objects.select_related(
            'category', 'assigned_worker', 'current_project', 
            'company', 'assigned_office', 'assigned_department'
        ).filter(is_active=True)
        
        # Filter by user's company if applicable
        user_company = getattr(self.request.user, 'company', None)
        if user_company:
            queryset = queryset.filter(company=user_company)
        
        # Apply filters from GET parameters
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        assigned_to = self.request.GET.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_worker_id=assigned_to)
        
        project = self.request.GET.get('project')
        if project:
            queryset = queryset.filter(current_project_id=project)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(asset_number__icontains=search) |
                Q(manufacturer__icontains=search) |
                Q(model__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Sorting
        sort_by = self.request.GET.get('sort', 'asset_number')
        if sort_by in ['asset_number', 'name', 'category__name', 'status', 'purchase_date']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        context.update({
            'categories': AssetCategory.objects.filter(is_active=True),
            'workers': Worker.objects.filter(is_active=True),
            'projects': Project.objects.filter(status='active'),
            'search_form': AssetSearchForm(self.request.GET),
            'current_filters': {
                'category': self.request.GET.get('category', ''),
                'status': self.request.GET.get('status', ''),
                'search': self.request.GET.get('search', ''),
                'assigned_to': self.request.GET.get('assigned_to', ''),
                'project': self.request.GET.get('project', ''),
            }
        })
        
        return context


class AssetDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single asset."""
    model = Asset
    template_name = 'asset/asset_detail.html'
    context_object_name = 'asset'
    
    def get_queryset(self):
        return Asset.objects.select_related(
            'category', 'assigned_worker', 'current_project',
            'company', 'assigned_office', 'assigned_department'
        ).prefetch_related(
            'maintenance_records', 'assignments', 'depreciation_records'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.get_object()
        
        # Recent maintenance records
        maintenance_records = asset.maintenance_records.order_by('-performed_date')[:10]
        
        # Assignment history
        assignment_history = asset.assignments.order_by('-start_date')[:10]
        
        # Depreciation info
        current_depreciation = asset.depreciated_value
        depreciation_rate = asset.depreciation_rate
        
        context.update({
            'maintenance_records': maintenance_records,
            'assignment_history': assignment_history,
            'current_depreciation': current_depreciation,
            'depreciation_rate': depreciation_rate,
            'is_maintenance_due': asset.is_maintenance_due,
            'days_until_maintenance': asset.days_until_maintenance,
            'is_warranty_active': asset.is_warranty_active,
            'can_assign': asset.status in ['available', 'maintenance'],
            'can_maintenance': True,
        })
        
        return context


class AssetCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create a new asset."""
    model = Asset
    form_class = AssetForm
    template_name = 'asset/asset_form.html'
    permission_required = 'asset.add_asset'
    
    def form_valid(self, form):
        # Set the company to the user's company
        if hasattr(self.request.user, 'company'):
            form.instance.company = self.request.user.company
        
        # Generate asset number if not provided
        if not form.instance.asset_number:
            form.instance.asset_number = self.generate_asset_number(form.instance.category)
        
        messages.success(self.request, f'Asset {form.instance.name} created successfully.')
        return super().form_valid(form)
    
    def generate_asset_number(self, category):
        """Generate a unique asset number based on category."""
        prefix = category.name[:3].upper() if category else 'AST'
        
        # Find the next number
        last_asset = Asset.objects.filter(
            asset_number__startswith=prefix
        ).order_by('-asset_number').first()
        
        if last_asset:
            try:
                last_num = int(last_asset.asset_number[3:])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        
        return f"{prefix}{next_num:04d}"


class AssetUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update an existing asset."""
    model = Asset
    form_class = AssetForm
    template_name = 'asset/asset_form.html'
    permission_required = 'asset.change_asset'
    
    def form_valid(self, form):
        messages.success(self.request, f'Asset {form.instance.name} updated successfully.')
        return super().form_valid(form)


class AssetDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete an asset (soft delete by setting is_active=False)."""
    model = Asset
    template_name = 'asset/asset_confirm_delete.html'
    permission_required = 'asset.delete_asset'
    success_url = reverse_lazy('asset:list')
    
    def delete(self, request, *args, **kwargs):
        # Soft delete - set is_active to False instead of deleting
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        
        messages.success(request, f'Asset {self.object.name} has been deactivated.')
        return redirect(self.success_url)


class AssetDuplicateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Duplicate an existing asset."""
    model = Asset
    form_class = AssetForm
    template_name = 'asset/asset_duplicate.html'
    permission_required = 'asset.add_asset'
    
    def get_initial(self):
        original_asset = get_object_or_404(Asset, pk=self.kwargs['pk'])
        initial = {
            'name': f"Copy of {original_asset.name}",
            'category': original_asset.category,
            'manufacturer': original_asset.manufacturer,
            'model': original_asset.model,
            'description': original_asset.description,
            'purchase_price': original_asset.purchase_price,
            'depreciation_method': original_asset.depreciation_method,
            'expected_life_years': original_asset.expected_life_years,
            'warranty_expiration': original_asset.warranty_expiration,
            'maintenance_interval_days': original_asset.maintenance_interval_days,
        }
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['original_asset'] = get_object_or_404(Asset, pk=self.kwargs['pk'])
        return context


# ============================================================================
# ASSET ACTION VIEWS
# ============================================================================

class AssetAssignView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Assign an asset to a worker or project."""
    form_class = AssetAssignmentForm
    template_name = 'asset/asset_assign.html'
    permission_required = 'asset.change_asset'
    
    def get_asset(self):
        return get_object_or_404(Asset, pk=self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asset'] = self.get_asset()
        return context
    
    def form_valid(self, form):
        asset = self.get_asset()
        
        with transaction.atomic():
            # Create assignment record
            assignment = AssetAssignment.objects.create(
                asset=asset,
                assigned_to_worker=form.cleaned_data.get('assigned_to_worker'),
                assigned_to_project=form.cleaned_data.get('assigned_to_project'),
                assigned_to_office=form.cleaned_data.get('assigned_to_office'),
                purpose=form.cleaned_data.get('purpose'),
                notes=form.cleaned_data.get('notes'),
                checked_out_by=str(self.request.user),
            )
            
            # Update asset status and assignment
            asset.assigned_worker = form.cleaned_data.get('assigned_to_worker')
            asset.current_project = form.cleaned_data.get('assigned_to_project')
            asset.assigned_office = form.cleaned_data.get('assigned_to_office')
            asset.status = 'in_use'
            asset.save()
        
        messages.success(
            self.request, 
            f'Asset {asset.name} has been assigned successfully.'
        )
        
        return redirect('asset:detail', pk=asset.pk)


class AssetUnassignView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Unassign an asset."""
    permission_required = 'asset.change_asset'
    
    def post(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk)
        
        with transaction.atomic():
            # Complete current assignment
            current_assignment = asset.assignments.filter(is_active=True).first()
            if current_assignment:
                current_assignment.end_date = date.today()
                current_assignment.is_active = False
                current_assignment.checked_in_by = str(request.user)
                current_assignment.save()
            
            # Update asset
            asset.assigned_worker = None
            asset.current_project = None
            asset.assigned_office = None
            asset.status = 'available'
            asset.save()
        
        messages.success(request, f'Asset {asset.name} has been unassigned.')
        return redirect('asset:detail', pk=pk)


class AssetTransferView(AssetAssignView):
    """Transfer asset to different assignment."""
    template_name = 'asset/asset_transfer.html'
    
    def form_valid(self, form):
        asset = self.get_asset()
        
        with transaction.atomic():
            # End current assignment
            current_assignment = asset.assignments.filter(is_active=True).first()
            if current_assignment:
                current_assignment.end_date = date.today()
                current_assignment.is_active = False
                current_assignment.save()
            
            # Create new assignment
            result = super().form_valid(form)
        
        messages.success(self.request, f'Asset {asset.name} has been transferred.')
        return result


class AssetCheckoutView(AssetAssignView):
    """Checkout asset for temporary use."""
    template_name = 'asset/asset_checkout.html'


class AssetCheckinView(AssetUnassignView):
    """Checkin asset from temporary use."""
    pass


class AssetStatusUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Update asset status."""
    permission_required = 'asset.change_asset'
    
    def post(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(Asset.STATUS_CHOICES):
            asset.status = new_status
            asset.save()
            messages.success(request, f'Asset status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid status.')
        
        return redirect('asset:detail', pk=pk)


# ============================================================================
# MAINTENANCE VIEWS
# ============================================================================

class AssetMaintenanceView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Record maintenance for an asset."""
    form_class = AssetMaintenanceForm
    template_name = 'asset/asset_maintenance.html'
    permission_required = 'asset.change_asset'
    
    def get_asset(self):
        return get_object_or_404(Asset, pk=self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.get_asset()
        context.update({
            'asset': asset,
            'maintenance_history': asset.maintenance_records.order_by('-performed_date')[:10]
        })
        return context
    
    def form_valid(self, form):
        asset = self.get_asset()
        
        # Create maintenance record
        maintenance = AssetMaintenanceRecord.objects.create(
            asset=asset,
            maintenance_type=form.cleaned_data['maintenance_type'],
            description=form.cleaned_data['description'],
            performed_by=form.cleaned_data.get('performed_by') or str(self.request.user),
            performed_date=form.cleaned_data['performed_date'],
            labor_cost=form.cleaned_data.get('labor_cost', 0),
            parts_cost=form.cleaned_data.get('parts_cost', 0),
            external_cost=form.cleaned_data.get('external_cost', 0),
            issue_resolved=form.cleaned_data.get('issue_resolved', True),
        )
        
        # Update asset maintenance info
        asset.mark_maintenance_complete(form.cleaned_data['description'])
        
        messages.success(
            self.request,
            f'Maintenance recorded for {asset.name}. Next maintenance scheduled for {asset.next_maintenance_date}.'
        )
        
        return redirect('asset:detail', pk=asset.pk)


class AssetMaintenanceScheduleView(LoginRequiredMixin, TemplateView):
    """View and schedule asset maintenance."""
    template_name = 'asset/maintenance_schedule.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = get_object_or_404(Asset, pk=self.kwargs['pk'])
        
        context.update({
            'asset': asset,
            'maintenance_due': asset.is_maintenance_due,
            'days_until_maintenance': asset.days_until_maintenance,
            'next_maintenance_date': asset.next_maintenance_date,
        })
        return context


class AssetMaintenanceHistoryView(LoginRequiredMixin, ListView):
    """View maintenance history for an asset."""
    model = AssetMaintenanceRecord
    template_name = 'asset/maintenance_history.html'
    context_object_name = 'maintenance_records'
    paginate_by = 20
    
    def get_queryset(self):
        asset = get_object_or_404(Asset, pk=self.kwargs['pk'])
        return asset.maintenance_records.order_by('-performed_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asset'] = get_object_or_404(Asset, pk=self.kwargs['pk'])
        return context


# ============================================================================
# CATEGORY MANAGEMENT VIEWS
# ============================================================================

class AssetCategoryListView(LoginRequiredMixin, ListView):
    """List all asset categories."""
    model = AssetCategory
    template_name = 'asset/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return AssetCategory.objects.filter(is_active=True).annotate(
            asset_count=Count('assets')
        )


class AssetCategoryDetailView(LoginRequiredMixin, DetailView):
    """Detail view for asset category."""
    model = AssetCategory
    template_name = 'asset/category_detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        
        context.update({
            'assets': category.assets.filter(is_active=True)[:20],
            'total_assets': category.assets.filter(is_active=True).count(),
            'total_value': category.assets.filter(is_active=True).aggregate(
                Sum('current_value')
            )['current_value__sum'] or 0,
        })
        return context


class AssetCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create new asset category."""
    model = AssetCategory
    form_class = AssetCategoryForm
    template_name = 'asset/category_form.html'
    permission_required = 'asset.add_assetcategory'
    success_url = reverse_lazy('asset:categories:list')


class AssetCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update asset category."""
    model = AssetCategory
    form_class = AssetCategoryForm
    template_name = 'asset/category_form.html'
    permission_required = 'asset.change_assetcategory'
    success_url = reverse_lazy('asset:categories:list')


class AssetCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete asset category."""
    model = AssetCategory
    template_name = 'asset/category_confirm_delete.html'
    permission_required = 'asset.delete_assetcategory'
    success_url = reverse_lazy('asset:categories:list')


class AssetCategoryAssetsView(LoginRequiredMixin, ListView):
    """List assets in a category."""
    model = Asset
    template_name = 'asset/category_assets.html'
    context_object_name = 'assets'
    paginate_by = 25
    
    def get_queryset(self):
        category = get_object_or_404(AssetCategory, pk=self.kwargs['pk'])
        return category.assets.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(AssetCategory, pk=self.kwargs['pk'])
        return context


# ============================================================================
# MAINTENANCE MANAGEMENT VIEWS
# ============================================================================

class MaintenanceListView(LoginRequiredMixin, ListView):
    """List all maintenance records."""
    model = AssetMaintenanceRecord
    template_name = 'asset/maintenance_list.html'
    context_object_name = 'maintenance_records'
    paginate_by = 25
    
    def get_queryset(self):
        return AssetMaintenanceRecord.objects.select_related('asset').order_by('-performed_date')


class MaintenanceDetailView(LoginRequiredMixin, DetailView):
    """Detail view for maintenance record."""
    model = AssetMaintenanceRecord
    template_name = 'asset/maintenance_detail.html'
    context_object_name = 'maintenance_record'


class MaintenanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create maintenance record."""
    model = AssetMaintenanceRecord
    form_class = AssetMaintenanceForm
    template_name = 'asset/maintenance_form.html'
    permission_required = 'asset.add_assetmaintenancerecord'


class MaintenanceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update maintenance record."""
    model = AssetMaintenanceRecord
    form_class = AssetMaintenanceForm
    template_name = 'asset/maintenance_form.html'
    permission_required = 'asset.change_assetmaintenancerecord'


class MaintenanceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete maintenance record."""
    model = AssetMaintenanceRecord
    template_name = 'asset/maintenance_confirm_delete.html'
    permission_required = 'asset.delete_assetmaintenancerecord'
    success_url = reverse_lazy('asset:maintenance:list')


class MaintenanceScheduleView(LoginRequiredMixin, TemplateView):
    """Maintenance schedule overview."""
    template_name = 'asset/maintenance_schedule_overview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = date.today()
        next_30_days = today + timedelta(days=30)
        
        context.update({
            'overdue_maintenance': Asset.objects.filter(
                next_maintenance_date__lt=today,
                is_active=True
            ),
            'due_today': Asset.objects.filter(
                next_maintenance_date=today,
                is_active=True
            ),
            'upcoming_maintenance': Asset.objects.filter(
                next_maintenance_date__range=[today + timedelta(days=1), next_30_days],
                is_active=True
            ),
        })
        return context


class MaintenanceOverdueView(LoginRequiredMixin, ListView):
    """List overdue maintenance assets."""
    model = Asset
    template_name = 'asset/maintenance_overdue.html'
    context_object_name = 'assets'
    
    def get_queryset(self):
        return Asset.objects.filter(
            next_maintenance_date__lt=date.today(),
            is_active=True
        ).select_related('category', 'assigned_worker')


class MaintenanceUpcomingView(LoginRequiredMixin, ListView):
    """List upcoming maintenance assets."""
    model = Asset
    template_name = 'asset/maintenance_upcoming.html'
    context_object_name = 'assets'
    
    def get_queryset(self):
        today = date.today()
        next_30_days = today + timedelta(days=30)
        
        return Asset.objects.filter(
            next_maintenance_date__range=[today, next_30_days],
            is_active=True
        ).select_related('category', 'assigned_worker')


# ============================================================================
# ASSIGNMENT MANAGEMENT VIEWS
# ============================================================================

class AssetAssignmentListView(LoginRequiredMixin, ListView):
    """List all asset assignments."""
    model = AssetAssignment
    template_name = 'asset/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 25
    
    def get_queryset(self):
        return AssetAssignment.objects.select_related(
            'asset', 'assigned_to_worker', 'assigned_to_project'
        ).order_by('-start_date')


class AssetAssignmentDetailView(LoginRequiredMixin, DetailView):
    """Detail view for asset assignment."""
    model = AssetAssignment
    template_name = 'asset/assignment_detail.html'
    context_object_name = 'assignment'


class AssetAssignmentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create asset assignment."""
    model = AssetAssignment
    form_class = AssetAssignmentForm
    template_name = 'asset/assignment_form.html'
    permission_required = 'asset.add_assetassignment'


class AssetAssignmentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update asset assignment."""
    model = AssetAssignment
    form_class = AssetAssignmentForm
    template_name = 'asset/assignment_form.html'
    permission_required = 'asset.change_assetassignment'


class AssetAssignmentCompleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Complete asset assignment."""
    permission_required = 'asset.change_assetassignment'
    
    def post(self, request, pk):
        assignment = get_object_or_404(AssetAssignment, pk=pk)
        
        assignment.end_date = date.today()
        assignment.is_active = False
        assignment.checked_in_by = str(request.user)
        assignment.save()
        
        # Update asset status
        assignment.asset.status = 'available'
        assignment.asset.assigned_worker = None
        assignment.asset.current_project = None
        assignment.asset.save()
        
        messages.success(request, f'Assignment for {assignment.asset.name} has been completed.')
        return redirect('asset:assignments:detail', pk=pk)


class ActiveAssignmentsView(AssetAssignmentListView):
    """List active assignments."""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class WorkerAssignmentsView(AssetAssignmentListView):
    """List assignments for a specific worker."""
    
    def get_queryset(self):
        worker_id = self.kwargs['worker_id']
        return super().get_queryset().filter(assigned_to_worker_id=worker_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['worker'] = get_object_or_404(Worker, pk=self.kwargs['worker_id'])
        return context


class ProjectAssignmentsView(AssetAssignmentListView):
    """List assignments for a specific project."""
    
    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return super().get_queryset().filter(assigned_to_project_id=project_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['project_id'])
        return context


# ============================================================================
# BULK OPERATIONS
# ============================================================================

class AssetBulkUpdateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Bulk update multiple assets."""
    form_class = AssetBulkUpdateForm
    template_name = 'asset/asset_bulk_update.html'
    permission_required = 'asset.change_asset'
    
    def form_valid(self, form):
        asset_ids = self.request.POST.getlist('asset_ids')
        
        if not asset_ids:
            messages.error(self.request, 'No assets selected for update.')
            return redirect('asset:list')
        
        assets = Asset.objects.filter(id__in=asset_ids)
        update_fields = {}
        
        # Build update dictionary based on form data
        if form.cleaned_data.get('status'):
            update_fields['status'] = form.cleaned_data['status']
        
        if form.cleaned_data.get('assigned_office'):
            update_fields['assigned_office'] = form.cleaned_data['assigned_office']
        
        if form.cleaned_data.get('assigned_department'):
            update_fields['assigned_department'] = form.cleaned_data['assigned_department']
        
        # Perform bulk update
        updated_count = assets.update(**update_fields)
        
        messages.success(
            self.request,
            f'Successfully updated {updated_count} assets.'
        )
        
        return redirect('asset:list')


class AssetBulkAssignView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Bulk assign multiple assets."""
    form_class = AssetAssignmentForm
    template_name = 'asset/asset_bulk_assign.html'
    permission_required = 'asset.change_asset'
    
    def form_valid(self, form):
        asset_ids = self.request.POST.getlist('asset_ids')
        
        if not asset_ids:
            messages.error(self.request, 'No assets selected for assignment.')
            return redirect('asset:list')
        
        assets = Asset.objects.filter(id__in=asset_ids, status='available')
        
        with transaction.atomic():
            for asset in assets:
                # Create assignment
                AssetAssignment.objects.create(
                    asset=asset,
                    assigned_to_worker=form.cleaned_data.get('assigned_to_worker'),
                    assigned_to_project=form.cleaned_data.get('assigned_to_project'),
                    assigned_to_office=form.cleaned_data.get('assigned_to_office'),
                    purpose=form.cleaned_data.get('purpose'),
                    notes=form.cleaned_data.get('notes'),
                    checked_out_by=str(self.request.user),
                )
                
                # Update asset
                asset.assigned_worker = form.cleaned_data.get('assigned_to_worker')
                asset.current_project = form.cleaned_data.get('assigned_to_project')
                asset.assigned_office = form.cleaned_data.get('assigned_to_office')
                asset.status = 'in_use'
                asset.save()
        
        messages.success(self.request, f'Successfully assigned {assets.count()} assets.')
        return redirect('asset:list')


class AssetBulkStatusView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Bulk update asset status."""
    permission_required = 'asset.change_asset'
    
    def post(self, request):
        asset_ids = request.POST.getlist('asset_ids')
        new_status = request.POST.get('status')
        
        if not asset_ids or not new_status:
            messages.error(request, 'No assets selected or status not provided.')
            return redirect('asset:list')
        
        assets = Asset.objects.filter(id__in=asset_ids)
        updated_count = assets.update(status=new_status)
        
        messages.success(request, f'Updated status for {updated_count} assets.')
        return redirect('asset:list')


# ============================================================================
# IMPORT/EXPORT VIEWS
# ============================================================================

class AssetImportView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Import assets from CSV."""
    form_class = AssetImportForm
    template_name = 'asset/asset_import.html'
    permission_required = 'asset.add_asset'
    
    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']
        
        try:
            # Read CSV file
            file_data = csv_file.read().decode('utf-8')
            csv_data = csv.DictReader(io.StringIO(file_data))
            
            created_count = 0
            error_count = 0
            
            for row in csv_data:
                try:
                    # Create asset from CSV row
                    asset = Asset.objects.create(
                        name=row.get('name', ''),
                        asset_number=row.get('asset_number', ''),
                        manufacturer=row.get('manufacturer', ''),
                        model=row.get('model', ''),
                        description=row.get('description', ''),
                        purchase_price=Decimal(row.get('purchase_price', '0') or '0'),
                        purchase_date=row.get('purchase_date') or None,
                        # Add more fields as needed
                    )
                    created_count += 1
                except Exception as e:
                    error_count += 1
            
            messages.success(
                self.request,
                f'Successfully imported {created_count} assets. {error_count} errors.'
            )
            
        except Exception as e:
            messages.error(self.request, f'Error processing file: {str(e)}')
        
        return redirect('asset:list')


class AssetExportView(LoginRequiredMixin, View):
    """Export assets to CSV."""
    
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="assets.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Asset Number', 'Name', 'Category', 'Manufacturer', 'Model',
            'Status', 'Purchase Price', 'Current Value', 'Purchase Date',
            'Assigned To', 'Project', 'Description'
        ])
        
        user_company = getattr(request.user, 'company', None)
        assets = Asset.objects.filter(
            company=user_company if user_company else None,
            is_active=True
        ).select_related('category', 'assigned_worker', 'current_project')
        
        for asset in assets:
            writer.writerow([
                asset.asset_number,
                asset.name,
                asset.category.name if asset.category else '',
                asset.manufacturer,
                asset.model,
                asset.status,
                asset.purchase_price,
                asset.current_value,
                asset.purchase_date,
                str(asset.assigned_worker) if asset.assigned_worker else '',
                str(asset.current_project) if asset.current_project else '',
                asset.description,
            ])
        
        return response


# ============================================================================
# API VIEWS FOR AJAX/MOBILE
# ============================================================================

class AssetSearchAPIView(LoginRequiredMixin, View):
    """API endpoint for asset search."""
    
    def get(self, request):
        query = request.GET.get('q', '')
        
        if len(query) < 2:
            return JsonResponse({'results': []})
        
        assets = Asset.objects.filter(
            Q(name__icontains=query) |
            Q(asset_number__icontains=query) |
            Q(manufacturer__icontains=query) |
            Q(model__icontains=query),
            is_active=True
        ).select_related('category', 'assigned_worker')[:20]
        
        results = [{
            'id': str(asset.id),
            'asset_number': asset.asset_number,
            'name': asset.name,
            'category': asset.category.name if asset.category else '',
            'status': asset.status,
            'assigned_to': str(asset.assigned_worker) if asset.assigned_worker else None,
            'url': reverse('asset:detail', args=[asset.id])
        } for asset in assets]
        
        return JsonResponse({'results': results})


class AssetFilterAPIView(LoginRequiredMixin, View):
    """API endpoint for filtered asset data."""
    
    def get(self, request):
        filters = {}
        
        category = request.GET.get('category')
        if category:
            filters['category_id'] = category
        
        status = request.GET.get('status')
        if status:
            filters['status'] = status
        
        assets = Asset.objects.filter(is_active=True, **filters)
        
        data = {
            'count': assets.count(),
            'assets': [{
                'id': str(asset.id),
                'name': asset.name,
                'status': asset.status,
                'url': reverse('asset:detail', args=[asset.id])
            } for asset in assets[:50]]
        }
        
        return JsonResponse(data)


class AssetAutocompleteAPIView(LoginRequiredMixin, View):
    """API endpoint for asset autocomplete."""
    
    def get(self, request):
        query = request.GET.get('q', '')
        
        if len(query) < 1:
            return JsonResponse({'results': []})
        
        assets = Asset.objects.filter(
            Q(name__icontains=query) | Q(asset_number__icontains=query),
            is_active=True
        )[:10]
        
        results = [{
            'id': str(asset.id),
            'text': f"{asset.asset_number} - {asset.name}"
        } for asset in assets]
        
        return JsonResponse({'results': results})


class AssetQuickStatusAPIView(LoginRequiredMixin, View):
    """API endpoint for quick status updates."""
    
    def post(self, request, asset_id):
        try:
            asset = Asset.objects.get(id=asset_id)
            data = json.loads(request.body)
            
            new_status = data.get('status')
            if new_status and new_status in dict(Asset.STATUS_CHOICES):
                asset.status = new_status
                asset.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Status updated to {new_status}',
                    'new_status': new_status
                })
            
            return JsonResponse({
                'success': False,
                'message': 'Invalid status provided'
            })
            
        except Asset.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Asset not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })


class AssetQuickAssignAPIView(LoginRequiredMixin, View):
    """API endpoint for quick assignments."""
    
    def post(self, request, asset_id):
        try:
            asset = Asset.objects.get(id=asset_id)
            data = json.loads(request.body)
            
            worker_id = data.get('worker_id')
            if worker_id:
                worker = Worker.objects.get(id=worker_id)
                
                with transaction.atomic():
                    # Create assignment
                    AssetAssignment.objects.create(
                        asset=asset,
                        assigned_to_worker=worker,
                        purpose='Quick Assignment',
                        checked_out_by=str(request.user),
                    )
                    
                    # Update asset
                    asset.assigned_worker = worker
                    asset.status = 'in_use'
                    asset.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Asset assigned to {worker.get_full_name()}',
                    'assigned_to': worker.get_full_name()
                })
            
            return JsonResponse({
                'success': False,
                'message': 'No worker specified'
            })
            
        except (Asset.DoesNotExist, Worker.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': 'Asset or worker not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })


class AssetCategoriesAPIView(LoginRequiredMixin, View):
    """API endpoint for categories by business category."""
    
    def get(self, request, business_category_id):
        categories = AssetCategory.objects.filter(
            business_category_id=business_category_id,
            is_active=True
        )
        
        data = [{
            'id': cat.id,
            'name': cat.name
        } for cat in categories]
        
        return JsonResponse({'categories': data})


class MaintenanceDueAPIView(LoginRequiredMixin, View):
    """API endpoint for maintenance due data."""
    
    def get(self, request):
        today = date.today()
        
        overdue = Asset.objects.filter(
            next_maintenance_date__lt=today,
            is_active=True
        ).count()
        
        due_today = Asset.objects.filter(
            next_maintenance_date=today,
            is_active=True
        ).count()
        
        upcoming = Asset.objects.filter(
            next_maintenance_date__range=[
                today + timedelta(days=1),
                today + timedelta(days=7)
            ],
            is_active=True
        ).count()
        
        return JsonResponse({
            'overdue': overdue,
            'due_today': due_today,
            'upcoming_week': upcoming
        })


# ============================================================================
# QR CODE AND MOBILE VIEWS
# ============================================================================

class AssetQRCodeView(LoginRequiredMixin, View):
    """Generate QR code for asset."""
    
    def get(self, request, asset_id):
        asset = get_object_or_404(Asset, id=asset_id)
        
        # Create QR code with asset URL
        qr_data = request.build_absolute_uri(
            reverse('asset:mobile-detail', args=[asset.id])
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        response = HttpResponse(content_type="image/png")
        img.save(response, "PNG")
        return response


class AssetScanView(LoginRequiredMixin, TemplateView):
    """QR code scanner interface."""
    template_name = 'asset/asset_scan.html'


class AssetMobileView(LoginRequiredMixin, DetailView):
    """Mobile-optimized asset detail view."""
    model = Asset
    template_name = 'asset/asset_mobile.html'
    context_object_name = 'asset'


# ============================================================================
# LEGACY SUPPORT VIEWS (For backward compatibility)
# ============================================================================

class LadderListView(AssetListView):
    """Legacy ladder list view - filters assets by ladder category."""
    template_name = 'asset/legacy/ladder_list.html'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(category__name__icontains='ladder')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['legacy_type'] = 'Ladders'
        return context


class VehicleListView(AssetListView):
    """Legacy vehicle list view - filters assets by vehicle category."""
    template_name = 'asset/legacy/vehicle_list.html'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(category__name__icontains='vehicle')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['legacy_type'] = 'Vehicles'
        return context


class PowerToolListView(AssetListView):
    """Legacy power tool list view - filters assets by power tool category."""
    template_name = 'asset/legacy/power_tool_list.html'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(category__name__icontains='power tool')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['legacy_type'] = 'Power Tools'
        return context


class TesterListView(AssetListView):
    """Legacy tester list view - filters assets by tester category."""
    template_name = 'asset/legacy/tester_list.html'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(category__name__icontains='tester')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['legacy_type'] = 'Testing Equipment'
        return context


class ToolListView(AssetListView):
    """Legacy tool list view - filters assets by tool category."""
    template_name = 'asset/legacy/tool_list.html'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(category__name__icontains='tool')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['legacy_type'] = 'Hand Tools'
        return context


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

@login_required
def asset_dashboard_data(request):
    """Return dashboard data as JSON for AJAX updates."""
    user_company = getattr(request.user, 'company', None)
    
    if user_company:
        assets = Asset.objects.filter(company=user_company, is_active=True)
    else:
        assets = Asset.objects.filter(is_active=True)
    
    data = {
        'total_assets': assets.count(),
        'available_assets': assets.filter(status='available').count(),
        'in_use_assets': assets.filter(status='in_use').count(),
        'maintenance_due': assets.filter(
            next_maintenance_date__lte=date.today()
        ).count(),
        'overdue_maintenance': assets.filter(
            next_maintenance_date__lt=date.today()
        ).count(),
        'total_value': float(assets.aggregate(
            Sum('current_value')
        )['current_value__sum'] or 0),
    }
    
    return JsonResponse(data)


# ============================================================================
# ADDITIONAL PLACEHOLDER VIEWS
# ============================================================================

class AssetImportTemplateView(LoginRequiredMixin, View):
    """Download CSV template for asset import."""
    
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="asset_import_template.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'name', 'asset_number', 'manufacturer', 'model', 'description',
            'purchase_price', 'purchase_date', 'category_name', 'status'
        ])
        
        # Add example row
        writer.writerow([
            'Example Asset', 'EX001', 'Example Manufacturer', 'Model X',
            'Example description', '1000.00', '2024-01-01', 'Equipment', 'available'
        ])
        
        return response


class AssetMobileActionView(LoginRequiredMixin, View):
    """Mobile quick actions for assets."""
    
    def post(self, request, asset_id):
        asset = get_object_or_404(Asset, id=asset_id)
        action = request.POST.get('action')
        
        if action == 'checkout':
            asset.status = 'in_use'
            asset.assigned_worker = request.user
            asset.save()
            
            AssetAssignment.objects.create(
                asset=asset,
                assigned_to_worker=request.user,
                purpose='Mobile Checkout',
                checked_out_by=str(request.user),
            )
            
            messages.success(request, f'{asset.name} checked out successfully.')
            
        elif action == 'checkin':
            asset.status = 'available'
            asset.assigned_worker = None
            asset.save()
            
            # Complete assignment
            assignment = asset.assignments.filter(is_active=True).first()
            if assignment:
                assignment.end_date = date.today()
                assignment.is_active = False
                assignment.checked_in_by = str(request.user)
                assignment.save()
            
            messages.success(request, f'{asset.name} checked in successfully.')
            
        elif action == 'maintenance':
            asset.status = 'maintenance'
            asset.save()
            
            messages.success(request, f'{asset.name} marked for maintenance.')
        
        return redirect('asset:mobile-detail', asset_id=asset_id)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

def asset_not_found(request, exception=None):
    """Custom 404 handler for asset views."""
    return render(request, 'asset/asset_not_found.html', status=404)


def asset_permission_denied(request, exception=None):
    """Custom 403 handler for asset views."""
    return render(request, 'asset/asset_permission_denied.html', status=403)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_user_assets(user):
    """Get assets for a specific user's company."""
    if hasattr(user, 'company') and user.company:
        return Asset.objects.filter(company=user.company, is_active=True)
    return Asset.objects.filter(is_active=True)


def can_user_manage_asset(user, asset):
    """Check if user can manage a specific asset."""
    if user.is_superuser:
        return True
    
    if hasattr(user, 'company') and asset.company == user.company:
        return True
    
    return False


def generate_asset_report(assets, report_type='inventory'):
    """Generate various types of asset reports."""
    if report_type == 'inventory':
        return {
            'total_assets': assets.count(),
            'by_category': assets.values('category__name').annotate(Count('id')),
            'by_status': assets.values('status').annotate(Count('id')),
            'total_value': assets.aggregate(Sum('current_value'))['current_value__sum'] or 0,
        }
    
    elif report_type == 'maintenance':
        today = date.today()
        return {
            'overdue': assets.filter(next_maintenance_date__lt=today).count(),
            'due_today': assets.filter(next_maintenance_date=today).count(),
            'upcoming': assets.filter(
                next_maintenance_date__range=[today, today + timedelta(days=30)]
            ).count(),
        }
    
    elif report_type == 'utilization':
        total = assets.count()
        in_use = assets.filter(status='in_use').count()
        return {
            'total_assets': total,
            'in_use': in_use,
            'available': assets.filter(status='available').count(),
            'utilization_rate': (in_use / total * 100) if total > 0 else 0,
        }
    
    return {}


def bulk_assign_assets(asset_ids, assignment_data, user):
    """Bulk assign multiple assets."""
    assets = Asset.objects.filter(id__in=asset_ids, status='available')
    
    with transaction.atomic():
        for asset in assets:
            # Create assignment
            AssetAssignment.objects.create(
                asset=asset,
                assigned_to_worker=assignment_data.get('worker'),
                assigned_to_project=assignment_data.get('project'),
                assigned_to_office=assignment_data.get('office'),
                purpose=assignment_data.get('purpose', 'Bulk Assignment'),
                notes=assignment_data.get('notes', ''),
                checked_out_by=str(user),
            )
            
            # Update asset
            asset.assigned_worker = assignment_data.get('worker')
            asset.current_project = assignment_data.get('project')
            asset.assigned_office = assignment_data.get('office')
            asset.status = 'in_use'
            asset.save()
    
    return assets.count()


def process_asset_import(csv_file, user):
    """Process CSV file for asset import."""
    results = {
        'created': 0,
        'updated': 0,
        'errors': [],
    }
    
    try:
        file_data = csv_file.read().decode('utf-8')
        csv_data = csv.DictReader(io.StringIO(file_data))
        
        for row_num, row in enumerate(csv_data, start=2):
            try:
                asset_number = row.get('asset_number', '').strip()
                
                # Check if asset exists
                if asset_number:
                    asset, created = Asset.objects.get_or_create(
                        asset_number=asset_number,
                        defaults={
                            'name': row.get('name', '').strip(),
                            'manufacturer': row.get('manufacturer', '').strip(),
                            'model': row.get('model', '').strip(),
                            'description': row.get('description', '').strip(),
                            'purchase_price': Decimal(row.get('purchase_price', '0') or '0'),
                            'purchase_date': row.get('purchase_date') or None,
                            'status': row.get('status', 'available').strip(),
                        }
                    )
                    
                    if created:
                        results['created'] += 1
                    else:
                        # Update existing asset
                        for field in ['name', 'manufacturer', 'model', 'description']:
                            if row.get(field):
                                setattr(asset, field, row[field].strip())
                        asset.save()
                        results['updated'] += 1
                
                else:
                    results['errors'].append(f'Row {row_num}: Asset number is required')
                    
            except Exception as e:
                results['errors'].append(f'Row {row_num}: {str(e)}')
    
    except Exception as e:
        results['errors'].append(f'File processing error: {str(e)}')
    
    return results


# ============================================================================
# MIXINS FOR COMMON FUNCTIONALITY
# ============================================================================

class AssetCompanyFilterMixin:
    """Mixin to filter assets by user's company."""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_company = getattr(self.request.user, 'company', None)
        
        if user_company:
            return queryset.filter(company=user_company)
        
        return queryset


class AssetPermissionMixin(PermissionRequiredMixin):
    """Mixin for asset-specific permissions."""
    
    def has_permission(self):
        if not super().has_permission():
            return False
        
        # Additional asset-specific permission checks
        if hasattr(self, 'get_object'):
            try:
                asset = self.get_object()
                return can_user_manage_asset(self.request.user, asset)
            except:
                pass
        
        return True


class AssetAjaxResponseMixin:
    """Mixin for AJAX responses in asset views."""
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Operation completed successfully',
                'redirect_url': self.get_success_url()
            })
        
        return response
    
    def form_invalid(self, form):
        response = super().form_invalid(form)
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors,
                'message': 'Please correct the errors below'
            })
        
        return response
