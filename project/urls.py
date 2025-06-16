# project/urls.py - Modern URL Configuration for Project Management

from django.urls import path, include
from django.views.generic import RedirectView
from . import views

app_name = 'project'

urlpatterns = [
    # ============================================
    # Dashboard & Home
    # ============================================
    path('', views.ProjectDashboardView.as_view(), name='dashboard'),
    path('dashboard/', views.ProjectDashboardView.as_view(), name='dashboard-alt'),
    
    # ============================================
    # Project Management (Main)
    # ============================================
    
    # Project List Views
    path('projects/', views.ProjectListView.as_view(), name='project-list'),
    path('projects/active/', views.ActiveProjectListView.as_view(), name='active-projects'),
    path('projects/complete/', views.CompleteProjectListView.as_view(), name='complete-projects'),
    path('projects/overdue/', views.OverdueProjectListView.as_view(), name='overdue-projects'),
    
    # Project CRUD Operations
    path('projects/create/', views.ProjectCreateView.as_view(), name='project-create'),
    path('projects/<str:job_number>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path('projects/<str:job_number>/edit/', views.ProjectUpdateView.as_view(), name='project-edit'),
    path('projects/<str:job_number>/delete/', views.ProjectDeleteView.as_view(), name='project-delete'),
    path('projects/<str:job_number>/duplicate/', views.ProjectDuplicateView.as_view(), name='project-duplicate'),
    
    # Project Status Management
    path('projects/<str:job_number>/status/', views.ProjectStatusUpdateView.as_view(), name='project-status-update'),
    path('projects/<str:job_number>/complete/', views.ProjectMarkCompleteView.as_view(), name='project-mark-complete'),
    path('projects/<str:job_number>/reopen/', views.ProjectReopenView.as_view(), name='project-reopen'),
    
    # Project Progress & Tracking
    path('projects/<str:job_number>/progress/', views.ProjectProgressView.as_view(), name='project-progress'),
    path('projects/<str:job_number>/timeline/', views.ProjectTimelineView.as_view(), name='project-timeline'),
    path('projects/<str:job_number>/activity/', views.ProjectActivityView.as_view(), name='project-activity'),
    
    # ============================================
    # Financial Management
    # ============================================
    path('projects/<str:job_number>/finance/', views.ProjectFinancialView.as_view(), name='project-finance'),
    path('projects/<str:job_number>/costs/calculate/', views.CalculateMaterialCostsView.as_view(), name='calculate-costs'),
    path('projects/<str:job_number>/invoice/', views.ProjectInvoiceView.as_view(), name='project-invoice'),
    path('projects/<str:job_number>/payment/', views.ProjectPaymentView.as_view(), name='project-payment'),
    
    # ============================================
    # Scope of Work Management
    # ============================================
    path('projects/<str:job_number>/scope/', views.ScopeOfWorkListView.as_view(), name='scope-list'),
    path('projects/<str:job_number>/scope/create/', views.ScopeOfWorkCreateView.as_view(), name='scope-create'),
    path('scope/<int:pk>/', views.ScopeOfWorkDetailView.as_view(), name='scope-detail'),
    path('scope/<int:pk>/edit/', views.ScopeOfWorkUpdateView.as_view(), name='scope-edit'),
    path('scope/<int:pk>/delete/', views.ScopeOfWorkDeleteView.as_view(), name='scope-delete'),
    
    # ============================================
    # Project Materials & Resources
    # ============================================
    
    # Material Overview
    path('projects/<str:job_number>/materials/', views.ProjectMaterialsView.as_view(), name='project-materials'),
    
    # Device Management
    path('projects/<str:job_number>/devices/', views.ProjectDeviceListView.as_view(), name='device-list'),
    path('projects/<str:job_number>/devices/create/', views.ProjectDeviceCreateView.as_view(), name='device-create'),
    path('devices/<int:pk>/', views.ProjectDeviceDetailView.as_view(), name='device-detail'),
    path('devices/<int:pk>/edit/', views.ProjectDeviceUpdateView.as_view(), name='device-edit'),
    path('devices/<int:pk>/delete/', views.ProjectDeviceDeleteView.as_view(), name='device-delete'),
    
    
    # Hardware Management
    path('projects/<str:job_number>/hardware/', views.ProjectHardwareListView.as_view(), name='hardware-list'),
    path('projects/<str:job_number>/hardware/create/', views.ProjectHardwareCreateView.as_view(), name='hardware-create'),
    path('hardware/<int:pk>/', views.ProjectHardwareDetailView.as_view(), name='hardware-detail'),
    path('hardware/<int:pk>/edit/', views.ProjectHardwareUpdateView.as_view(), name='hardware-edit'),
    path('hardware/<int:pk>/delete/', views.ProjectHardwareDeleteView.as_view(), name='hardware-delete'),
    
    # Software Management
    path('projects/<str:job_number>/software/', views.ProjectSoftwareListView.as_view(), name='software-list'),
    path('projects/<str:job_number>/software/create/', views.ProjectSoftwareCreateView.as_view(), name='software-create'),
    path('software/<int:pk>/', views.ProjectSoftwareDetailView.as_view(), name='software-detail'),
    path('software/<int:pk>/edit/', views.ProjectSoftwareUpdateView.as_view(), name='software-edit'),
    path('software/<int:pk>/delete/', views.ProjectSoftwareDeleteView.as_view(), name='software-delete'),
    
    # License Management
    path('projects/<str:job_number>/licenses/', views.ProjectLicenseListView.as_view(), name='license-list'),
    path('projects/<str:job_number>/licenses/create/', views.ProjectLicenseCreateView.as_view(), name='license-create'),
    path('licenses/<int:pk>/', views.ProjectLicenseDetailView.as_view(), name='license-detail'),
    path('licenses/<int:pk>/edit/', views.ProjectLicenseUpdateView.as_view(), name='license-edit'),
    path('licenses/<int:pk>/delete/', views.ProjectLicenseDeleteView.as_view(), name='license-delete'),
    
    # Travel Management
    path('projects/<str:job_number>/travel/', views.ProjectTravelListView.as_view(), name='travel-list'),
    path('projects/<str:job_number>/travel/create/', views.ProjectTravelCreateView.as_view(), name='travel-create'),
    path('travel/<int:pk>/', views.ProjectTravelDetailView.as_view(), name='travel-detail'),
    path('travel/<int:pk>/edit/', views.ProjectTravelUpdateView.as_view(), name='travel-edit'),
    path('travel/<int:pk>/delete/', views.ProjectTravelDeleteView.as_view(), name='travel-delete'),
    
    # ============================================
    # Project Changes & Milestones
    # ============================================
    
    # Change Management
    path('projects/<str:job_number>/changes/', views.ProjectChangeListView.as_view(), name='change-list'),
    path('projects/<str:job_number>/changes/create/', views.ProjectChangeCreateView.as_view(), name='change-create'),
    path('changes/<int:pk>/', views.ProjectChangeDetailView.as_view(), name='change-detail'),
    path('changes/<int:pk>/edit/', views.ProjectChangeUpdateView.as_view(), name='change-edit'),
    path('changes/<int:pk>/delete/', views.ProjectChangeDeleteView.as_view(), name='change-delete'),
    path('changes/<int:pk>/approve/', views.ProjectChangeApproveView.as_view(), name='change-approve'),
    
    # Milestone Management
    path('projects/<str:job_number>/milestones/', views.ProjectMilestoneListView.as_view(), name='milestone-list'),
    path('projects/<str:job_number>/milestones/create/', views.ProjectMilestoneCreateView.as_view(), name='milestone-create'),
    path('milestones/<int:pk>/', views.ProjectMilestoneDetailView.as_view(), name='milestone-detail'),
    path('milestones/<int:pk>/edit/', views.ProjectMilestoneUpdateView.as_view(), name='milestone-edit'),
    path('milestones/<int:pk>/delete/', views.ProjectMilestoneDeleteView.as_view(), name='milestone-delete'),
    path('milestones/<int:pk>/complete/', views.ProjectMilestoneCompleteView.as_view(), name='milestone-complete'),
    
    # ============================================
    # Project Templates
    # ============================================
    path('templates/', views.ProjectTemplateListView.as_view(), name='template-list'),
    path('templates/create/', views.ProjectTemplateCreateView.as_view(), name='template-create'),
    path('templates/<int:pk>/', views.ProjectTemplateDetailView.as_view(), name='template-detail'),
    path('templates/<int:pk>/edit/', views.ProjectTemplateUpdateView.as_view(), name='template-edit'),
    path('templates/<int:pk>/delete/', views.ProjectTemplateDeleteView.as_view(), name='template-delete'),
    path('templates/<int:pk>/use/', views.ProjectFromTemplateView.as_view(), name='project-from-template'),
    
    # ============================================
    # Team & Assignment Management
    # ============================================
    path('projects/<str:job_number>/team/', views.ProjectTeamView.as_view(), name='project-team'),
    path('projects/<str:job_number>/team/assign/', views.ProjectTeamAssignView.as_view(), name='team-assign'),
    path('projects/<str:job_number>/team/remove/', views.ProjectTeamRemoveView.as_view(), name='team-remove'),
    path('assignments/', views.MyProjectAssignmentsView.as_view(), name='my-assignments'),
    
    # ============================================
    # Reports & Analytics
    # ============================================
    path('reports/', views.ProjectReportsView.as_view(), name='reports'),
    path('reports/financial/', views.FinancialReportView.as_view(), name='financial-report'),
    path('reports/progress/', views.ProgressReportView.as_view(), name='progress-report'),
    path('reports/team-performance/', views.TeamPerformanceReportView.as_view(), name='team-performance'),
    path('reports/utilization/', views.ResourceUtilizationReportView.as_view(), name='utilization-report'),
    
    # ============================================
    # Export & Import
    # ============================================
    path('export/', views.ProjectExportView.as_view(), name='project-export'),
    path('export/<str:job_number>/', views.ProjectExportSingleView.as_view(), name='project-export-single'),
    path('export/<str:job_number>/pdf/', views.ProjectPDFExportView.as_view(), name='project-pdf'),
    path('export/<str:job_number>/excel/', views.ProjectExcelExportView.as_view(), name='project-excel'),
    path('import/', views.ProjectImportView.as_view(), name='project-import'),
    
    # ============================================
    # API Endpoints (for AJAX/Frontend)
    # ============================================
    path('api/', include([
        # Search & Autocomplete
        path('search/', views.ProjectSearchAPIView.as_view(), name='api-search'),
        path('autocomplete/projects/', views.ProjectAutocompleteView.as_view(), name='api-project-autocomplete'),
        path('autocomplete/locations/', views.LocationAutocompleteView.as_view(), name='api-location-autocomplete'),
        
        # Quick Updates
        path('projects/<str:job_number>/quick-update/', views.ProjectQuickUpdateAPIView.as_view(), name='api-quick-update'),
        path('projects/<str:job_number>/progress-update/', views.ProjectProgressUpdateAPIView.as_view(), name='api-progress-update'),
        
        # Real-time Data
        path('projects/<str:job_number>/status/', views.ProjectStatusAPIView.as_view(), name='api-project-status'),
        path('dashboard/stats/', views.DashboardStatsAPIView.as_view(), name='api-dashboard-stats'),
        path('notifications/', views.ProjectNotificationsAPIView.as_view(), name='api-notifications'),
        
        # Bulk Operations
        path('projects/bulk-update/', views.ProjectBulkUpdateAPIView.as_view(), name='api-bulk-update'),
        path('projects/bulk-delete/', views.ProjectBulkDeleteAPIView.as_view(), name='api-bulk-delete'),
        
        # Material Cost Calculator
        path('projects/<str:job_number>/calculate-costs/', views.CalculateCostsAPIView.as_view(), name='api-calculate-costs'),
        
        # File Uploads
        path('projects/<str:job_number>/upload-image/', views.ProjectImageUploadAPIView.as_view(), name='api-upload-image'),
        path('projects/<str:job_number>/upload-document/', views.ProjectDocumentUploadAPIView.as_view(), name='api-upload-document'),

        # Serializer-based endpoints
        path('projects/', views.ProjectListAPIView.as_view(), name='api-project-list'),
        path('projects/<str:job_number>/', views.ProjectDetailAPIView.as_view(), name='api-project-detail'),
        path('scope/', views.ScopeOfWorkListAPIView.as_view(), name='api-scope-list'),
    ])),
    
    # ============================================
    # Utility & Management URLs
    # ============================================
    
    # Project Number Generation
    path('generate-job-number/', views.GenerateJobNumberView.as_view(), name='generate-job-number'),
    
    # Project Validation
    path('validate/', views.ProjectValidationView.as_view(), name='project-validation'),
    path('projects/<str:job_number>/validate/', views.ProjectValidationDetailView.as_view(), name='project-validation-detail'),
    
    # Quick Actions
    path('quick-actions/', views.QuickActionsView.as_view(), name='quick-actions'),
    path('recently-viewed/', views.RecentlyViewedProjectsView.as_view(), name='recently-viewed'),
    path('favorites/', views.FavoriteProjectsView.as_view(), name='favorite-projects'),
    path('projects/<str:job_number>/favorite/', views.ToggleFavoriteView.as_view(), name='toggle-favorite'),
    
    # Settings & Configuration
    path('settings/', views.ProjectSettingsView.as_view(), name='project-settings'),
    path('settings/defaults/', views.ProjectDefaultsView.as_view(), name='project-defaults'),
    path('settings/business-categories/', views.BusinessCategorySettingsView.as_view(), name='business-category-settings'),
    
    # ============================================
    # Calendar & Scheduling
    # ============================================
    path('calendar/', views.ProjectCalendarView.as_view(), name='project-calendar'),
    path('calendar/events/', views.ProjectCalendarEventsAPIView.as_view(), name='calendar-events'),
    path('schedule/', views.ProjectScheduleView.as_view(), name='project-schedule'),
    
    # ============================================
    # Legacy URL Redirects (for backward compatibility)
    # ============================================
    path('job/<str:job_number>/', RedirectView.as_view(pattern_name='project:project-detail'), name='legacy-job-detail'),
    path('estimate/<str:job_number>/', RedirectView.as_view(pattern_name='project:project-detail'), name='legacy-estimate'),
    path('quote/<str:job_number>/', RedirectView.as_view(pattern_name='project:project-detail'), name='legacy-quote'),
    
    # ============================================
    # Health Check & Status
    # ============================================
    path('health/', views.ProjectHealthCheckView.as_view(), name='health-check'),
    path('system-status/', views.SystemStatusView.as_view(), name='system-status'),
]

# ============================================
# URL Pattern Groups for Better Organization
# ============================================

# Core project management patterns
project_patterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('create/', views.ProjectCreateView.as_view(), name='create'),
    path('<str:job_number>/', views.ProjectDetailView.as_view(), name='detail'),
    path('<str:job_number>/edit/', views.ProjectUpdateView.as_view(), name='edit'),
    path('<str:job_number>/delete/', views.ProjectDeleteView.as_view(), name='delete'),
]

# Material management patterns
material_patterns = [
    path('devices/', include([
        path('', views.ProjectDeviceListView.as_view(), name='device-list'),
        path('create/', views.ProjectDeviceCreateView.as_view(), name='device-create'),
        path('<int:pk>/', views.ProjectDeviceDetailView.as_view(), name='device-detail'),
        path('<int:pk>/edit/', views.ProjectDeviceUpdateView.as_view(), name='device-edit'),
        path('<int:pk>/delete/', views.ProjectDeviceDeleteView.as_view(), name='device-delete'),
    ])),
    # ... other material types
]

# ============================================
# Custom URL Configuration Class
# ============================================

class ProjectURLConfig:
    """
    Custom URL configuration class for project app
    Provides organized access to URL patterns and reverse lookups
    """
    
    @staticmethod
    def get_project_urls():
        """Get all project-related URLs"""
        return [name for name in globals() if name.endswith('_patterns')]
    
    @staticmethod
    def get_api_urls():
        """Get all API endpoint URLs"""
        return [url for url in urlpatterns if 'api/' in str(url.pattern)]
    
    @staticmethod
    def get_material_urls():
        """Get all material management URLs"""
        material_types = ['device', 'hardware', 'software', 'license', 'travel']
        return [url for url in urlpatterns if any(mat_type in str(url.pattern) for mat_type in material_types)]

# ============================================
# URL Validation & Testing
# ============================================

def validate_project_urls():
    """
    Validate that all required URL patterns exist
    Useful for testing and development
    """
    required_patterns = [
        'dashboard', 'project-list', 'project-create', 'project-detail',
        'project-edit', 'project-delete', 'scope-create', 'device-create',
        'api-search', 'reports', 'project-export'
    ]
    
    existing_patterns = [url.name for url in urlpatterns if url.name]
    missing_patterns = [pattern for pattern in required_patterns if pattern not in existing_patterns]
    
    if missing_patterns:
        print(f"Warning: Missing URL patterns: {missing_patterns}")
    else:
        print("All required URL patterns are present")
    
    return len(missing_patterns) == 0

# ============================================
# URL Documentation
# ============================================

"""
Project URL Structure Documentation:

1. Dashboard & Overview:
   - /projects/ - Main project dashboard
   - /projects/dashboard/ - Alternative dashboard route

2. Project Management:
   - /projects/projects/ - List all projects
   - /projects/projects/create/ - Create new project
   - /projects/projects/{job_number}/ - Project detail view
   - /projects/projects/{job_number}/edit/ - Edit project

3. Material Management:
   Each material type (devices, hardware, software, licenses, travel) follows the pattern:
   - /projects/projects/{job_number}/{material_type}/ - List items
   - /projects/projects/{job_number}/{material_type}/create/ - Add new item
   - /projects/{material_type}/{pk}/ - Item detail/edit/delete

4. Scope & Changes:
   - /projects/projects/{job_number}/scope/ - Scope of work management
   - /projects/projects/{job_number}/changes/ - Change requests

5. Reports & Analytics:
   - /projects/reports/ - Various project reports
   - /projects/export/ - Export functionality

6. API Endpoints:
   - /projects/api/ - All AJAX/API endpoints for frontend

7. Settings & Configuration:
   - /projects/settings/ - Project configuration
   - /projects/templates/ - Project templates

This structure provides:
- RESTful URL design
- Logical grouping of related functionality
- Consistent patterns across different object types
- API endpoints for modern frontend interactions
- Backward compatibility with legacy URLs
- Clear separation between user interface and API
"""