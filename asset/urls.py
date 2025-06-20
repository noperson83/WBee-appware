# asset/urls.py - Complete URL patterns for asset management
"""
Comprehensive Django 5 URL patterns for asset management.
Includes all major functionality while keeping it manageable.
"""

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'asset'

# Main asset management patterns
asset_patterns = [
    # Dashboard and overview
    path('', views.AssetDashboardView.as_view(), name='dashboard'),
    path('analytics/', views.AssetAnalyticsView.as_view(), name='analytics'),
    path('reports/', views.AssetReportsView.as_view(), name='reports'),
    
    # Asset CRUD operations
    path('list/', views.AssetListView.as_view(), name='list'),
    path('create/', views.AssetCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.AssetDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.AssetUpdateView.as_view(), name='update'),
    path('<uuid:pk>/delete/', views.AssetDeleteView.as_view(), name='delete'),
    path('<uuid:pk>/duplicate/', views.AssetDuplicateView.as_view(), name='duplicate'),
    
    # Asset actions
    path('<uuid:pk>/assign/', views.AssetAssignView.as_view(), name='assign'),
    path('<uuid:pk>/unassign/', views.AssetUnassignView.as_view(), name='unassign'),
    path('<uuid:pk>/transfer/', views.AssetTransferView.as_view(), name='transfer'),
    path('<uuid:pk>/checkout/', views.AssetCheckoutView.as_view(), name='checkout'),
    path('<uuid:pk>/checkin/', views.AssetCheckinView.as_view(), name='checkin'),
    
    # Asset maintenance
    path('<uuid:pk>/maintenance/', views.AssetMaintenanceView.as_view(), name='maintenance'),
    path('<uuid:pk>/maintenance/schedule/', views.AssetMaintenanceScheduleView.as_view(), name='maintenance-schedule'),
    path('<uuid:pk>/maintenance/history/', views.AssetMaintenanceHistoryView.as_view(), name='maintenance-history'),
    
    # Status management
    #path('<uuid:pk>/status/', views.AssetStatusUpdateView.as_view(), name='status-update'),
    
    # Bulk operations
    path('bulk/update/', views.AssetBulkUpdateView.as_view(), name='bulk-update'),
    path('bulk/assign/', views.AssetBulkAssignView.as_view(), name='bulk-assign'),
    path('bulk/status/', views.AssetBulkStatusView.as_view(), name='bulk-status'),
    
    # Import/Export
    path('import/', views.AssetImportView.as_view(), name='import'),
    path('export/', views.AssetExportView.as_view(), name='export'),
]

# Asset category management
category_patterns = [
    path('', views.AssetCategoryListView.as_view(), name='list'),
    path('create/', views.AssetCategoryCreateView.as_view(), name='create'),
    path('<int:pk>/', views.AssetCategoryDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.AssetCategoryUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.AssetCategoryDeleteView.as_view(), name='delete'),
    path('<int:pk>/assets/', views.AssetCategoryAssetsView.as_view(), name='assets'),
]

# Maintenance management
maintenance_patterns = [
    path('', views.MaintenanceListView.as_view(), name='list'),
    path('create/', views.MaintenanceCreateView.as_view(), name='create'),
    path('<int:pk>/', views.MaintenanceDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.MaintenanceUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.MaintenanceDeleteView.as_view(), name='delete'),
    path('schedule/', views.MaintenanceScheduleView.as_view(), name='schedule'),
    path('overdue/', views.MaintenanceOverdueView.as_view(), name='overdue'),
    path('upcoming/', views.MaintenanceUpcomingView.as_view(), name='upcoming'),
]

# Assignment management
assignment_patterns = [
    path('', views.AssetAssignmentListView.as_view(), name='list'),
    path('create/', views.AssetAssignmentCreateView.as_view(), name='create'),
    path('<int:pk>/', views.AssetAssignmentDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.AssetAssignmentUpdateView.as_view(), name='update'),
    path('<int:pk>/complete/', views.AssetAssignmentCompleteView.as_view(), name='complete'),
    path('active/', views.ActiveAssignmentsView.as_view(), name='active'),
    path('worker/<int:worker_id>/', views.WorkerAssignmentsView.as_view(), name='worker'),
    path('project/<int:project_id>/', views.ProjectAssignmentsView.as_view(), name='project'),
]

# API endpoints for AJAX/mobile
api_patterns = [
    # Search and filtering
    path('search/', views.AssetSearchAPIView.as_view(), name='search'),
    path('filter/', views.AssetFilterAPIView.as_view(), name='filter'),
    path('autocomplete/', views.AssetAutocompleteAPIView.as_view(), name='autocomplete'),
    
    # Quick actions
    path('<uuid:asset_id>/quick-status/', views.AssetQuickStatusAPIView.as_view(), name='quick-status'),
    path('<uuid:asset_id>/quick-assign/', views.AssetQuickAssignAPIView.as_view(), name='quick-assign'),
    
    # Dynamic data
    path('categories/<int:business_category_id>/', views.AssetCategoriesAPIView.as_view(), name='categories'),
    path('maintenance/due/', views.MaintenanceDueAPIView.as_view(), name='maintenance-due'),
    
    # Dashboard data
    path('dashboard-data/', views.asset_dashboard_data, name='dashboard-data'),
]

# QR Code and mobile
mobile_patterns = [
    path('qr/<uuid:asset_id>/', views.AssetQRCodeView.as_view(), name='qr-code'),
    path('scan/', views.AssetScanView.as_view(), name='scan'),
    path('mobile/<uuid:asset_id>/', views.AssetMobileView.as_view(), name='mobile-detail'),
]

# Legacy support (simplified)
legacy_patterns = [
    path('vehicles/', views.VehicleListView.as_view(), name='vehicle-list'),
    path('power-tools/', views.PowerToolListView.as_view(), name='power-tool-list'),
    path('ladders/', views.LadderListView.as_view(), name='ladder-list'),
    path('testers/', views.TesterListView.as_view(), name='tester-list'),
    path('tools/', views.ToolListView.as_view(), name='tool-list'),
]

# Main URL patterns
urlpatterns = [
    # Main asset management
    path('', include(asset_patterns)),
    
    # Category management
    path('categories/', include(category_patterns)),
    
    # Maintenance management
    path(
        'maintenance/',
        include((maintenance_patterns, 'maintenance'), namespace='maintenance'),
    ),
    
    # Assignment management  
    path(
        'assignments/',
        include((assignment_patterns, 'assignments'), namespace='assignments'),
    ),
    
    # API endpoints
    path('api/', include(api_patterns)),
    
    # Mobile and QR support
    path('mobile/', include(mobile_patterns)),
    
    # Legacy asset type support
    path('legacy/', include(legacy_patterns)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
