from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'hr'

urlpatterns = [
    # Dashboard
    path('', views.index, name='index'),
    
    # Worker URLs
    path('workers/', views.WorkerListView.as_view(), name='worker-list'),
    path('worker/<uuid:pk>/', views.WorkerDetailView.as_view(), name='worker-detail'),
    path('worker/create/', views.WorkerCreateView.as_view(), name='worker-create'),
    path('worker/<uuid:pk>/update/', views.WorkerUpdateView.as_view(), name='worker-update'),
    path('worker/<uuid:pk>/delete/', views.WorkerDeleteView.as_view(), name='worker-delete'),
    
    # Job Position URLs
    path('positions/', views.JobPositionListView.as_view(), name='position-list'),
    path('position/<int:pk>/', views.JobPositionDetailView.as_view(), name='position-detail'),
    path('position/create/', views.JobPositionCreateView.as_view(), name='position-create'),
    path('position/<int:pk>/update/', views.JobPositionUpdateView.as_view(), name='position-update'),
    
    # Time Off URLs
    path('time-off/', views.TimeOffRequestListView.as_view(), name='timeoff-list'),
    path('time-off/<int:pk>/', views.TimeOffRequestDetailView.as_view(), name='timeoff-detail'),
    path('time-off/create/', views.TimeOffRequestCreateView.as_view(), name='timeoff-create'),
    path('time-off/<int:pk>/update/', views.TimeOffRequestUpdateView.as_view(), name='timeoff-update'),
    path('time-off/<int:pk>/approve/', views.approve_time_off, name='timeoff-approve'),
    path('time-off/<int:pk>/deny/', views.deny_time_off, name='timeoff-deny'),
    
    # Performance Review URLs
    path('reviews/', views.PerformanceReviewListView.as_view(), name='review-list'),
    path('review/<int:pk>/', views.PerformanceReviewDetailView.as_view(), name='review-detail'),
    path('review/create/', views.PerformanceReviewCreateView.as_view(), name='review-create'),
    path('review/<int:pk>/update/', views.PerformanceReviewUpdateView.as_view(), name='review-update'),
    
    # Clearance & Certification URLs
    path('clearances/', views.ClearanceListView.as_view(), name='clearance-list'),
    path('certifications/', views.CertificationListView.as_view(), name='certification-list'),
    
    # Reports
    path('reports/', views.reports_dashboard, name='reports'),
    path('reports/payroll/', views.payroll_report, name='payroll-report'),
    path('reports/employee/', views.employee_report, name='employee-report'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
