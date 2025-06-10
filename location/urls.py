from django.urls import path, include
from . import views

app_name = 'location'

urlpatterns = [
    # Main location views
    path('', views.location_dashboard, name='dashboard'),
    path('list/', views.LocationListView.as_view(), name='location-list'),
    path('<uuid:pk>/', views.LocationDetailView.as_view(), name='location-detail'),
    path('create/', views.LocationCreateView.as_view(), name='location-create'),
    path('<uuid:pk>/update/', views.LocationUpdateView.as_view(), name='location-update'),
    path('<uuid:pk>/delete/', views.LocationDeleteView.as_view(), name='location-delete'),
    
    # Document management
    path('<uuid:location_pk>/documents/add/', 
         views.LocationDocumentCreateView.as_view(), 
         name='document-create'),
    path('documents/<int:pk>/delete/', 
         views.LocationDocumentDeleteView.as_view(), 
         name='document-delete'),
    
    # Note management
    path('<uuid:location_pk>/notes/add/', 
         views.LocationNoteCreateView.as_view(), 
         name='note-create'),
    path('notes/<int:pk>/update/', 
         views.LocationNoteUpdateView.as_view(), 
         name='note-update'),
    
    # Utility views
    path('<uuid:pk>/calculate-totals/', 
         views.calculate_contract_totals, 
         name='calculate-totals'),
    
    # Map views
    path('map/', views.locations_map_view, name='locations-map'),
    path('api/map-data/', views.location_map_data, name='map-data'),
    
    # AJAX endpoints
    path('ajax/location-types/', views.get_location_types, name='ajax-location-types'),
    path('ajax/dynamic-choices/', views.get_dynamic_choices, name='ajax-dynamic-choices'),
    
    # Legacy redirects (for backward compatibility)
    path('jobsite/<int:pk>/', views.legacy_jobsite_redirect, name='legacy-jobsite-redirect'),
]

# Alternative URL patterns for different naming conventions
# Include these if you want to support multiple URL styles

# RESTful style URLs
rest_patterns = [
    path('locations/', views.LocationListView.as_view(), name='locations-index'),
    path('locations/new/', views.LocationCreateView.as_view(), name='locations-new'),
    path('locations/<uuid:pk>/', views.LocationDetailView.as_view(), name='locations-show'),
    path('locations/<uuid:pk>/edit/', views.LocationUpdateView.as_view(), name='locations-edit'),
    path('locations/<uuid:pk>/destroy/', views.LocationDeleteView.as_view(), name='locations-destroy'),
]

# You can include the REST patterns if desired:
# urlpatterns += rest_patterns

# API-style patterns for frontend frameworks
api_patterns = [
    path('api/locations/', views.LocationListView.as_view(), name='api-locations'),
    path('api/locations/<uuid:pk>/', views.LocationDetailView.as_view(), name='api-location-detail'),
]

# Include API patterns if building a SPA or mobile app:
# urlpatterns += api_patterns