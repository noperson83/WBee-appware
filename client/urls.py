# client/urls.py - Clean URL Configuration

from django.urls import path
from . import views

app_name = 'client'

urlpatterns = [
    # Main client views
    path('', views.client_dashboard, name='dashboard'),
    path('list/', views.ClientListView.as_view(), name='list'),
    path('create/', views.ClientCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.ClientDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.ClientUpdateView.as_view(), name='update'),
    path('<uuid:pk>/delete/', views.ClientDeleteView.as_view(), name='delete'),
    
    # Financial views
    path('<uuid:pk>/financial/', views.client_financial_dashboard, name='financial-dashboard'),
    
    # Export/Import
    path('export/csv/', views.export_clients_csv, name='export-csv'),
    
    # AJAX API endpoints
    path('api/search/', views.client_search_api, name='api-search'),
    path('<uuid:pk>/add-address/', views.add_client_address, name='add-address'),
    path('<uuid:pk>/add-contact/', views.add_client_contact, name='add-contact'),
    path('bulk-update/', views.bulk_update_clients, name='bulk-update'),
    
    # Legacy URLs for backward compatibility
    path('legacy/', views.client_dashboard, name='client'),
    path('legacy/list/', views.ClientListView.as_view(), name='clients-list'),
    path('legacy/create/', views.ClientCreateView.as_view(), name='create-client'),
    path('legacy/update/<uuid:pk>/', views.ClientUpdateView.as_view(), name='update-client'),
    path('legacy/delete/<uuid:pk>/', views.ClientDeleteView.as_view(), name='delete-client'),
    path('legacy/detail/<uuid:pk>/', views.ClientDetailView.as_view(), name='client-detail'),
]
