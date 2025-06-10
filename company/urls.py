# company/urls.py - Modern URL Configuration for Company Management

from django.urls import path
from . import views

app_name = 'company'

urlpatterns = [
    # Company URLs
    path('', views.CompanyListView.as_view(), name='list'),
    path('overview/', views.company_overview, name='overview'),
    path('create/', views.CompanyCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.CompanyDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.CompanyUpdateView.as_view(), name='update'),
    path('<uuid:pk>/delete/', views.CompanyDeleteView.as_view(), name='delete'),
    path('<uuid:pk>/dashboard/', views.company_dashboard, name='dashboard'),
    path('<uuid:pk>/setup-defaults/', views.setup_company_defaults, name='setup-defaults'),
    
    # Office URLs
    path('<uuid:company_id>/offices/', views.OfficeListView.as_view(), name='office-list'),
    path('<uuid:company_id>/offices/create/', views.OfficeCreateView.as_view(), name='office-create'),
    path('offices/<uuid:pk>/', views.OfficeDetailView.as_view(), name='office-detail'),
    path('offices/<uuid:pk>/edit/', views.OfficeUpdateView.as_view(), name='office-update'),
    
    # Department URLs  
    path('<uuid:company_id>/departments/', views.DepartmentListView.as_view(), name='department-list'),
    path('<uuid:company_id>/departments/create/', views.DepartmentCreateView.as_view(), name='department-create'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department-detail'),
    
    # AJAX/API URLs
    path('api/search/', views.company_search_api, name='search-api'),
    path('api/offices/search/', views.office_search_api, name='office-search-api'),
    path('api/departments/search/', views.department_search_api, name='department-search-api'),
    
    # Legacy URLs (for backward compatibility)
    path('info/', views.company, name='info'),  # Redirects to list
    path('detail/<int:id>/', views.CompanyDeView, name='company-detail-legacy'),  # Redirects to detail
    
    # Legacy update/delete URLs (redirected to new format)
    path('update-company/<uuid:pk>/', views.CompanyUpdateView.as_view(), name='update-company-legacy'),
    path('company/<uuid:pk>/delete/', views.CompanyDeleteView.as_view(), name='delete-company-legacy'),
]
