# company/views.py - Modernized Views for Company Management

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .models import Company, Office, Department, CompanySettings, setup_default_company_data
from .forms import CompanyForm, OfficeForm, DepartmentForm
from client.models import Client, Address, Contact
from location.models import BusinessCategory


# Company Views
class CompanyListView(LoginRequiredMixin, ListView):
    """List all companies with search and filtering"""
    model = Company
    template_name = 'company/company_list.html'
    context_object_name = 'companies'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Company.objects.select_related('business_category', 'parent_company')
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(company_name__icontains=search_query) |
                Q(legal_name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(primary_contact_name__icontains=search_query)
            )
        
        # Filter by business type
        business_type = self.request.GET.get('business_type')
        if business_type:
            queryset = queryset.filter(business_type=business_type)
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(business_category_id=category)
        
        # Filter by active status
        active_filter = self.request.GET.get('active')
        if active_filter == 'true':
            queryset = queryset.filter(is_active=True)
        elif active_filter == 'false':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('company_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['business_types'] = Company.BUSINESS_TYPES
        context['business_categories'] = BusinessCategory.objects.filter(is_active=True)
        context['search_query'] = self.request.GET.get('search', '')
        context['current_filters'] = {
            'business_type': self.request.GET.get('business_type', ''),
            'category': self.request.GET.get('category', ''),
            'active': self.request.GET.get('active', ''),
        }
        return context


class CompanyDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single company"""
    model = Company
    template_name = 'company/company_detail.html'
    context_object_name = 'company'
    
    def get_queryset(self):
        return Company.objects.select_related(
            'business_category', 'parent_company'
        ).prefetch_related(
            'offices', 'departments', 'subsidiaries', 'addresses', 'contacts'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.object
        
        # Get related data
        context['offices'] = company.offices.filter(is_active=True).order_by('office_name')
        context['departments'] = company.departments.filter(is_active=True).order_by('name')
        context['subsidiaries'] = company.subsidiaries.filter(is_active=True)
        context['addresses'] = company.addresses.filter(is_active=True)
        context['contacts'] = company.contacts.filter(is_active=True)
        
        # Get primary address and contact
        context['primary_address'] = company.primary_address
        context['headquarters_address'] = company.headquarters_address
        
        # Get company statistics
        context['statistics'] = {
            'total_offices': company.total_locations,
            'total_departments': company.total_departments,
            'total_employees': company.total_employees,
            'revenue_growth': company.revenue_growth,
        }
        
        # Get recent clients (if you want to show them)
        try:
            context['recent_clients'] = Client.objects.filter(
                # Assuming there's a relationship to company
                is_active=True
            ).order_by('-created_at')[:5]
        except:
            context['recent_clients'] = []
        
        return context


class CompanyCreateView(LoginRequiredMixin, CreateView):
    """Create a new company"""
    model = Company
    template_name = 'company/company_form.html'
    form_class = CompanyForm
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Set up default company data
        setup_default_company_data(self.object)
        
        messages.success(
            self.request, 
            f'Company "{self.object.company_name}" created successfully with default departments and settings.'
        )
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create New Company'
        context['submit_text'] = 'Create Company'
        return context


class CompanyUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing company"""
    model = Company
    template_name = 'company/company_form.html'
    form_class = CompanyForm
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Company "{self.object.company_name}" updated successfully.'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Update {self.object.company_name}'
        context['submit_text'] = 'Update Company'
        return context


class CompanyDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a company (with confirmation)"""
    model = Company
    template_name = 'company/company_confirm_delete.html'
    success_url = reverse_lazy('company:list')
    
    def delete(self, request, *args, **kwargs):
        company_name = self.get_object().company_name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Company "{company_name}" deleted successfully.')
        return response


# Office Views
class OfficeListView(LoginRequiredMixin, ListView):
    """List offices for a company"""
    model = Office
    template_name = 'company/office_list.html'
    context_object_name = 'offices'
    paginate_by = 20
    
    def get_queryset(self):
        company_id = self.kwargs.get('company_id')
        if company_id:
            return Office.objects.filter(
                company_id=company_id, is_active=True
            ).select_related('company').order_by('office_name')
        return Office.objects.filter(is_active=True).select_related('company')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.kwargs.get('company_id')
        if company_id:
            context['company'] = get_object_or_404(Company, id=company_id)
        return context


class OfficeDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of an office"""
    model = Office
    template_name = 'company/office_detail.html'
    context_object_name = 'office'
    
    def get_queryset(self):
        return Office.objects.select_related('company').prefetch_related('addresses')


class OfficeCreateView(LoginRequiredMixin, CreateView):
    """Create a new office"""
    model = Office
    template_name = 'company/office_form.html'
    form_class = OfficeForm
    
    def get_initial(self):
        initial = super().get_initial()
        company_id = self.kwargs.get('company_id')
        if company_id:
            initial['company'] = company_id
        return initial
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Office "{self.object.office_name}" created successfully.'
        )
        return super().form_valid(form)


class OfficeUpdateView(LoginRequiredMixin, UpdateView):
    """Update an office"""
    model = Office
    template_name = 'company/office_form.html'
    form_class = OfficeForm
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Office "{self.object.office_name}" updated successfully.'
        )
        return super().form_valid(form)


# Department Views
class DepartmentListView(LoginRequiredMixin, ListView):
    """List departments for a company"""
    model = Department
    template_name = 'company/department_list.html'
    context_object_name = 'departments'
    
    def get_queryset(self):
        company_id = self.kwargs.get('company_id')
        if company_id:
            return Department.objects.filter(
                company_id=company_id, is_active=True
            ).select_related('company', 'parent_department', 'primary_office')
        return Department.objects.filter(is_active=True).select_related('company')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.kwargs.get('company_id')
        if company_id:
            context['company'] = get_object_or_404(Company, id=company_id)
        return context


class DepartmentDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a department"""
    model = Department
    template_name = 'company/department_detail.html'
    context_object_name = 'department'
    
    def get_queryset(self):
        return Department.objects.select_related(
            'company', 'parent_department', 'primary_office'
        ).prefetch_related('sub_departments')


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    """Create a new department"""
    model = Department
    template_name = 'company/department_form.html'
    form_class = DepartmentForm
    
    def get_initial(self):
        initial = super().get_initial()
        company_id = self.kwargs.get('company_id')
        if company_id:
            initial['company'] = company_id
        return initial
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Department "{self.object.name}" created successfully.'
        )
        return super().form_valid(form)


# Dashboard and Summary Views
@login_required
def company_dashboard(request, pk):
    """Company dashboard with key metrics and quick access"""
    company = get_object_or_404(Company, pk=pk)
    
    # Gather dashboard data
    context = {
        'company': company,
        'total_offices': company.total_locations,
        'total_departments': company.total_departments,
        'total_employees': company.total_employees,
        'revenue_growth': company.revenue_growth,
        'recent_offices': company.offices.filter(is_active=True).order_by('-created_at')[:5],
        'recent_departments': company.departments.filter(is_active=True).order_by('-created_at')[:5],
        'primary_address': company.primary_address,
        'headquarters_address': company.headquarters_address,
    }
    
    # Add financial summary if revenue data exists
    if company.current_year_revenue or company.previous_year_revenue:
        context['financial_summary'] = {
            'current_year': company.current_year_revenue,
            'previous_year': company.previous_year_revenue,
            'growth_rate': company.revenue_growth,
        }
    
    return render(request, 'company/company_dashboard.html', context)


@login_required
def company_overview(request):
    """Overview of all companies"""
    companies = Company.objects.filter(is_active=True).annotate(
        office_count=Count('offices', filter=Q(offices__is_active=True)),
        department_count=Count('departments', filter=Q(departments__is_active=True))
    ).order_by('company_name')
    
    # Pagination
    paginator = Paginator(companies, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'companies': page_obj,
        'total_companies': companies.count(),
        'total_offices': sum(c.office_count for c in companies),
        'total_departments': sum(c.department_count for c in companies),
    }
    
    return render(request, 'company/company_overview.html', context)


# AJAX and API Views
@login_required
def company_search_api(request):
    """AJAX endpoint for company search"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'companies': []})
    
    companies = Company.objects.filter(
        Q(company_name__icontains=query) | Q(legal_name__icontains=query),
        is_active=True
    ).values('id', 'company_name', 'legal_name')[:10]
    
    return JsonResponse({'companies': list(companies)})


@login_required
def office_search_api(request):
    """AJAX endpoint for office search within a company"""
    company_id = request.GET.get('company_id')
    query = request.GET.get('q', '')
    
    if not company_id or len(query) < 2:
        return JsonResponse({'offices': []})
    
    offices = Office.objects.filter(
        company_id=company_id,
        office_name__icontains=query,
        is_active=True
    ).values('id', 'office_name', 'office_type')[:10]
    
    return JsonResponse({'offices': list(offices)})


@login_required 
def department_search_api(request):
    """AJAX endpoint for department search within a company"""
    company_id = request.GET.get('company_id')
    query = request.GET.get('q', '')
    
    if not company_id or len(query) < 2:
        return JsonResponse({'departments': []})
    
    departments = Department.objects.filter(
        company_id=company_id,
        name__icontains=query,
        is_active=True
    ).values('id', 'name', 'department_code')[:10]
    
    return JsonResponse({'departments': list(departments)})


# Utility Views
@login_required
def setup_company_defaults(request, pk):
    """Manually trigger setup of default company data"""
    company = get_object_or_404(Company, pk=pk)
    setup_default_company_data(company)
    
    messages.success(
        request, 
        f'Default departments and settings created for {company.company_name}'
    )
    return redirect('company:detail', pk=company.pk)


# Legacy view function (for backward compatibility)
@login_required
def company(request):
    """
    Legacy view function for home page of site.
    Redirects to modern company list view.
    """
    return redirect('company:list')


@login_required  
def CompanyDeView(request, id):
    """
    Legacy detailed view function.
    Redirects to modern detail view.
    """
    return redirect('company:detail', pk=id)
