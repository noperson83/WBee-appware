from django.urls import path, include

from . import views

app_name = "project"

# API endpoints
api_patterns = [
    path("search/", views.project_search_api, name="api-search"),
    path("dashboard-stats/", views.dashboard_stats_api, name="api-dashboard-stats"),
    path(
        "projects/<str:job_number>/quick-update/",
        views.project_quick_update_api,
        name="api-quick-update",
    ),
    path(
        "projects/<str:job_number>/calculate-costs/",
        views.calculate_costs_api,
        name="api-calculate-costs",
    ),
    path("calendar/events/", views.project_calendar_events_api, name="api-calendar-events"),
]

urlpatterns = [
    # Dashboard
    path("", views.ProjectDashboardView.as_view(), name="dashboard"),

    # Project CRUD
    path("projects/", views.ProjectListView.as_view(), name="project-list"),
    path("projects/active/", views.ActiveProjectListView.as_view(), name="project-active"),
    path("projects/complete/", views.CompleteProjectListView.as_view(), name="project-complete"),
    path("projects/overdue/", views.OverdueProjectListView.as_view(), name="project-overdue"),
    path("projects/create/", views.ProjectCreateView.as_view(), name="project-create"),
    path("projects/<str:job_number>/", views.ProjectDetailView.as_view(), name="project-detail"),
    path("projects/<str:job_number>/edit/", views.ProjectUpdateView.as_view(), name="project-edit"),
    path("projects/<str:job_number>/delete/", views.ProjectDeleteView.as_view(), name="project-delete"),

    # Additional project views
    path("projects/<str:job_number>/progress/", views.ProjectProgressView.as_view(), name="project-progress"),
    path("projects/<str:job_number>/timeline/", views.ProjectTimelineView.as_view(), name="project-timeline"),
    path("projects/<str:job_number>/financial/", views.ProjectFinancialView.as_view(), name="project-financial"),
    path("projects/<str:job_number>/materials/", views.ProjectMaterialsView.as_view(), name="project-materials"),

    # Scope of work
    path("projects/<str:job_number>/scope/", views.ScopeOfWorkListView.as_view(), name="scope-list"),
    path("projects/<str:job_number>/scope/create/", views.ScopeOfWorkCreateView.as_view(), name="scope-create"),
    path("scope/<int:pk>/", views.ScopeOfWorkDetailView.as_view(), name="scope-detail"),
    path("scope/<int:pk>/edit/", views.ScopeOfWorkUpdateView.as_view(), name="scope-edit"),
    path("scope/<int:pk>/delete/", views.ScopeOfWorkDeleteView.as_view(), name="scope-delete"),

    # Devices
    path("projects/<str:job_number>/devices/", views.ProjectDeviceListView.as_view(), name="device-list"),
    path("projects/<str:job_number>/devices/create/", views.ProjectDeviceCreateView.as_view(), name="device-create"),
    path("devices/<int:pk>/", views.ProjectDeviceDetailView.as_view(), name="device-detail"),
    path("devices/<int:pk>/edit/", views.ProjectDeviceUpdateView.as_view(), name="device-edit"),
    path("devices/<int:pk>/delete/", views.ProjectDeviceDeleteView.as_view(), name="device-delete"),

    # Project changes
    path("projects/<str:job_number>/changes/", views.ProjectChangeListView.as_view(), name="change-list"),
    path("projects/<str:job_number>/changes/create/", views.ProjectChangeCreateView.as_view(), name="change-create"),
    path("changes/<int:pk>/approve/", views.ProjectChangeApproveView.as_view(), name="change-approve"),

    # Milestones
    path("projects/<str:job_number>/milestones/", views.ProjectMilestoneListView.as_view(), name="milestone-list"),
    path("projects/<str:job_number>/milestones/create/", views.ProjectMilestoneCreateView.as_view(), name="milestone-create"),
    path("milestones/<int:pk>/complete/", views.ProjectMilestoneCompleteView.as_view(), name="milestone-complete"),

    # Teams
    path("projects/<str:job_number>/team/", views.ProjectTeamView.as_view(), name="project-team"),
    path("projects/<str:job_number>/team/assign/", views.ProjectTeamAssignView.as_view(), name="team-assign"),
    path("assignments/", views.MyProjectAssignmentsView.as_view(), name="my-assignments"),

    # Reports
    path("reports/", views.ProjectReportsView.as_view(), name="reports"),
    path("reports/financial/", views.FinancialReportView.as_view(), name="financial-report"),
    path("reports/progress/", views.ProgressReportView.as_view(), name="progress-report"),
    path("reports/team-performance/", views.TeamPerformanceReportView.as_view(), name="team-performance"),
    path("reports/utilization/", views.ResourceUtilizationReportView.as_view(), name="utilization-report"),

    # Export
    path("export/", views.ProjectExportView.as_view(), name="project-export"),
    path("export/<str:job_number>/pdf/", views.ProjectPDFExportView.as_view(), name="project-pdf"),

    # Utilities
    path("generate-job-number/", views.GenerateJobNumberView.as_view(), name="generate-job-number"),
    path("validate/", views.ProjectValidationView.as_view(), name="project-validation"),

    # Health
    path("health/", views.ProjectHealthCheckView.as_view(), name="health-check"),
    path("system-status/", views.SystemStatusView.as_view(), name="system-status"),

    # API include
    path("api/", include(api_patterns)),
]
