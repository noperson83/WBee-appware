from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Avg, Sum
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import date, timedelta
import csv

from .models import (
    Worker, JobPosition, TimeOffRequest, PerformanceReview,
    Clearance, Certification, WorkerClearance, WorkerCertification
)
from .forms import RegisterForm
from company.models import Company, Department, Office


@login_required
def index(request):
    """HR Dashboard view"""
    # Get basic statistics
    total_workers = Worker.objects.filter(is_active=True).count()
    pending_time_off = TimeOffRequest.objects.filter(approval_status='pending').count()
    expiring_clearances = WorkerClearance.objects.filter(
        is_active=True,
        expiration_date__lte=date.today() + timedelta(days=30),
        expiration_date__gte=date.today()
    ).count()
    
    # Recent hires (last 30 days)
    recent_hires = Worker.objects.filter(
        date_of_hire__gte=date.today() - timedelta(days=30)
    ).order_by('-date_of_hire')[:5]
    
    # Upcoming reviews
    upcoming_reviews = PerformanceReview.objects.filter(
        next_review_date__lte=date.today() + timedelta(days=30),
        next_review_date__gte=date.today()
    ).order_by('next_review_date')[:5]
    
    context = {
        'total_workers': total_workers,
        'pending_time_off': pending_time_off,
        'expiring_clearances': expiring_clearances,
        'recent_hires': recent_hires,
        'upcoming_reviews': upcoming_reviews,
    }
    
    return render(request, 'hr/dashboard.html', context)


class WorkerListView(LoginRequiredMixin, ListView):
    model = Worker
    template_name = 'hr/worker_list.html'
    context_object_name = 'workers'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Worker.objects.filter(is_active=True).select_related(
            'position', 'department', 'office', 'manager', 'company'
        ).prefetch_related('clearances', 'certifications')
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(employee_id__icontains=search_query)
            )
        
        # Department filter
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
            
        # Position filter
        position = self.request.GET.get('position')
        if position:
            queryset = queryset.filter(position_id=position)
        
        return queryset.order_by('first_name', 'last_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        context['positions'] = JobPosition.objects.all()
        context['search_query'] = self.request.GET.get('search', '')
        return context


class WorkerDetailView(LoginRequiredMixin, DetailView):
    model = Worker
    template_name = 'hr/worker_detail.html'
    context_object_name = 'worker'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        worker = self.object
        
        # Get worker's clearances and certifications
        context['worker_clearances'] = WorkerClearance.objects.filter(
            worker=worker, is_active=True
        ).select_related('clearance')
        
        context['worker_certifications'] = WorkerCertification.objects.filter(
            worker=worker, is_active=True
        ).select_related('certification')
        
        # Get time off requests
        context['time_off_requests'] = TimeOffRequest.objects.filter(
            worker=worker
        ).order_by('-start_date')[:10]
        
        # Get performance reviews
        context['performance_reviews'] = PerformanceReview.objects.filter(
            worker=worker
        ).order_by('-review_date')[:5]
        
        # Get direct reports if this worker is a manager
        context['direct_reports'] = Worker.objects.filter(
            manager=worker, is_active=True
        )
        
        return context


class WorkerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Worker
    form_class = RegisterForm
    template_name = 'hr/worker_form.html'
    permission_required = 'hr.add_worker'
    
    def form_valid(self, form):
        # Set the company for the new worker
        if hasattr(self.request.user, 'company'):
            form.instance.company = self.request.user.company
        messages.success(self.request, 'Worker created successfully!')
        return super().form_valid(form)


class WorkerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Worker
    template_name = 'hr/worker_form.html'
    permission_required = 'hr.change_worker'
    fields = [
        'first_name', 'last_name', 'middle_name', 'preferred_name',
        'phone_number', 'emergency_contact_name', 'emergency_contact_phone',
        'emergency_contact_relationship', 'date_of_birth', 'gender',
        'position', 'office', 'department', 'manager', 'employment_status',
        'date_of_hire', 'current_hourly_rate', 'current_annual_salary',
        'bio', 'skills', 'profile_picture', 'resume', 'roles', 'is_active'
    ]
    
    def form_valid(self, form):
        messages.success(self.request, 'Worker updated successfully!')
        return super().form_valid(form)


class WorkerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Worker
    template_name = 'hr/worker_confirm_delete.html'
    permission_required = 'hr.delete_worker'
    success_url = reverse_lazy('hr:worker-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Worker deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Job Position Views
class JobPositionListView(LoginRequiredMixin, ListView):
    model = JobPosition
    template_name = 'hr/position_list.html'
    context_object_name = 'positions'
    paginate_by = 20
    
    def get_queryset(self):
        return JobPosition.objects.filter(is_active=True).select_related(
            'department'
        ).prefetch_related('required_clearances', 'required_certifications')


class JobPositionDetailView(LoginRequiredMixin, DetailView):
    model = JobPosition
    template_name = 'hr/position_detail.html'
    context_object_name = 'position'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        position = self.object
        
        # Get workers in this position
        context['workers'] = Worker.objects.filter(
            position=position, is_active=True
        )
        
        return context


class JobPositionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = JobPosition
    template_name = 'hr/position_form.html'
    permission_required = 'hr.add_jobposition'
    fields = [
        'title', 'position_code', 'department', 'reports_to',
        'description', 'responsibilities', 'requirements',
        'compensation_type', 'min_hourly_rate', 'max_hourly_rate',
        'min_annual_salary', 'max_annual_salary', 'employment_type',
        'job_level', 'required_clearances', 'required_certifications',
        'is_billable'
    ]


class JobPositionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = JobPosition
    template_name = 'hr/position_form.html'
    permission_required = 'hr.change_jobposition'
    fields = [
        'title', 'position_code', 'department', 'reports_to',
        'description', 'responsibilities', 'requirements',
        'compensation_type', 'min_hourly_rate', 'max_hourly_rate',
        'min_annual_salary', 'max_annual_salary', 'employment_type',
        'job_level', 'required_clearances', 'required_certifications',
        'is_billable'
    ]


# Time Off Request Views
class TimeOffRequestListView(LoginRequiredMixin, ListView):
    model = TimeOffRequest
    template_name = 'hr/timeoff_list.html'
    context_object_name = 'time_off_requests'
    paginate_by = 25
    
    def get_queryset(self):
        # Managers can see all requests, employees see only their own
        if self.request.user.is_staff or hasattr(self.request.user, 'direct_reports'):
            queryset = TimeOffRequest.objects.all()
        else:
            queryset = TimeOffRequest.objects.filter(worker=self.request.user)
            
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(approval_status=status)
            
        return queryset.select_related('worker', 'approved_by').order_by('-start_date')


class TimeOffRequestDetailView(LoginRequiredMixin, DetailView):
    model = TimeOffRequest
    template_name = 'hr/timeoff_detail.html'
    context_object_name = 'time_off_request'


class TimeOffRequestCreateView(LoginRequiredMixin, CreateView):
    model = TimeOffRequest
    template_name = 'hr/timeoff_form.html'
    fields = ['start_date', 'end_date', 'time_off_type', 'is_paid', 'reason']
    
    def form_valid(self, form):
        form.instance.worker = self.request.user
        messages.success(self.request, 'Time off request submitted successfully!')
        return super().form_valid(form)


class TimeOffRequestUpdateView(LoginRequiredMixin, UpdateView):
    model = TimeOffRequest
    template_name = 'hr/timeoff_form.html'
    fields = ['start_date', 'end_date', 'time_off_type', 'is_paid', 'reason']
    
    def get_queryset(self):
        # Only allow editing of own requests or if user is manager
        if self.request.user.is_staff:
            return TimeOffRequest.objects.all()
        return TimeOffRequest.objects.filter(worker=self.request.user)


@login_required
@permission_required('hr.change_timeoffrequest')
def approve_time_off(request, pk):
    """Approve a time off request"""
    time_off = get_object_or_404(TimeOffRequest, pk=pk)
    time_off.approval_status = 'approved'
    time_off.approved_by = request.user
    time_off.approved_date = timezone.now()
    time_off.save()
    
    messages.success(request, f'Time off request for {time_off.worker.get_full_name()} approved.')
    return redirect('hr:timeoff-detail', pk=pk)


@login_required
@permission_required('hr.change_timeoffrequest')
def deny_time_off(request, pk):
    """Deny a time off request"""
    time_off = get_object_or_404(TimeOffRequest, pk=pk)
    time_off.approval_status = 'denied'
    time_off.approved_by = request.user
    time_off.approved_date = timezone.now()
    time_off.save()
    
    messages.success(request, f'Time off request for {time_off.worker.get_full_name()} denied.')
    return redirect('hr:timeoff-detail', pk=pk)


# Performance Review Views
class PerformanceReviewListView(LoginRequiredMixin, ListView):
    model = PerformanceReview
    template_name = 'hr/review_list.html'
    context_object_name = 'reviews'
    paginate_by = 25
    
    def get_queryset(self):
        return PerformanceReview.objects.select_related(
            'worker', 'reviewer'
        ).order_by('-review_date')


class PerformanceReviewDetailView(LoginRequiredMixin, DetailView):
    model = PerformanceReview
    template_name = 'hr/review_detail.html'
    context_object_name = 'review'


class PerformanceReviewCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = PerformanceReview
    template_name = 'hr/review_form.html'
    permission_required = 'hr.add_performancereview'
    fields = [
        'worker', 'review_period_start', 'review_period_end',
        'review_type', 'overall_rating', 'quality_of_work',
        'productivity', 'communication', 'teamwork', 'leadership',
        'accomplishments', 'areas_for_improvement', 'goals_for_next_period',
        'manager_comments', 'next_review_date'
    ]
    
    def form_valid(self, form):
        form.instance.reviewer = self.request.user
        return super().form_valid(form)


class PerformanceReviewUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = PerformanceReview
    template_name = 'hr/review_form.html'
    permission_required = 'hr.change_performancereview'
    fields = [
        'review_period_start', 'review_period_end', 'review_type',
        'overall_rating', 'quality_of_work', 'productivity',
        'communication', 'teamwork', 'leadership', 'accomplishments',
        'areas_for_improvement', 'goals_for_next_period',
        'manager_comments', 'employee_comments', 'next_review_date'
    ]


# Clearance and Certification Views
class ClearanceListView(LoginRequiredMixin, ListView):
    model = Clearance
    template_name = 'hr/clearance_list.html'
    context_object_name = 'clearances'
    
    def get_queryset(self):
        return Clearance.objects.filter(is_active=True).annotate(
            worker_count=Count('workers')
        )


class CertificationListView(LoginRequiredMixin, ListView):
    model = Certification
    template_name = 'hr/certification_list.html'
    context_object_name = 'certifications'
    
    def get_queryset(self):
        return Certification.objects.filter(is_active=True).annotate(
            worker_count=Count('workers')
        )


# Reports
@login_required
@permission_required('hr.view_worker')
def reports_dashboard(request):
    """HR Reports dashboard"""
    context = {
        'total_workers': Worker.objects.filter(is_active=True).count(),
        'departments': Department.objects.annotate(
            worker_count=Count('workers', filter=Q(workers__is_active=True))
        ),
        'positions': JobPosition.objects.annotate(
            worker_count=Count('workers', filter=Q(workers__is_active=True))
        ),
    }
    return render(request, 'hr/reports_dashboard.html', context)


@login_required
@permission_required('hr.view_worker')
def payroll_report(request):
    """Generate payroll report"""
    workers = Worker.objects.filter(is_active=True).select_related(
        'position', 'department'
    )
    
    # Calculate totals
    total_salary = workers.aggregate(
        total=Sum('current_annual_salary')
    )['total'] or 0
    
    total_hourly = workers.filter(
        current_hourly_rate__isnull=False
    ).aggregate(
        total=Sum('current_hourly_rate')
    )['total'] or 0
    
    context = {
        'workers': workers,
        'total_salary': total_salary,
        'total_hourly': total_hourly,
    }
    
    # Return CSV if requested
    if request.GET.get('format') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="payroll_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Employee ID', 'Name', 'Position', 'Department',
            'Annual Salary', 'Hourly Rate', 'Employment Status'
        ])
        
        for worker in workers:
            writer.writerow([
                worker.employee_id,
                worker.get_full_name(),
                worker.position.title if worker.position else '',
                worker.department.name if worker.department else '',
                worker.current_annual_salary or '',
                worker.current_hourly_rate or '',
                worker.get_employment_status_display()
            ])
        
        return response
    
    return render(request, 'hr/payroll_report.html', context)


@login_required
@permission_required('hr.view_worker')
def employee_report(request):
    """Generate employee report"""
    workers = Worker.objects.filter(is_active=True).select_related(
        'position', 'department', 'office'
    ).prefetch_related('clearances', 'certifications')
    
    context = {
        'workers': workers,
        'total_count': workers.count(),
    }
    
    return render(request, 'hr/employee_report.html', context)
