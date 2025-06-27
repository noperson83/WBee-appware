from django.urls import path
from . import views

app_name = 'business'

urlpatterns = [
    # Dashboard
    path('', views.business_dashboard, name='dashboard'),

    # Business Configurations
    path('configurations/', views.BusinessConfigurationListView.as_view(), name='config-list'),
    path('configurations/<slug:slug>/', views.BusinessConfigurationDetailView.as_view(), name='config-detail'),

    # Business Types
    path('types/', views.BusinessTypeListView.as_view(), name='type-list'),
    path('types/<slug:slug>/', views.BusinessTypeDetailView.as_view(), name='type-detail'),

    # Business Templates
    path('templates/', views.BusinessTemplateListView.as_view(), name='template-list'),
    path('templates/<slug:slug>/', views.BusinessTemplateDetailView.as_view(), name='template-detail'),
    path('templates/<slug:template_slug>/apply/<uuid:company_id>/',
         views.apply_template_to_company, name='apply-template'),

    # Setup Wizard
    path('setup/', views.business_setup_wizard, name='setup-wizard'),

    # API Endpoints
    path('api/configurations/', views.business_config_api, name='config-api'),
    path('api/templates/', views.business_template_api, name='template-api'),
    path('api/categories/', views.project_categories_api, name='categories-api'),
]
