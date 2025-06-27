from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import generic
from django.http import JsonResponse
from django.contrib import messages

from .models import (
    BusinessConfiguration,
    BusinessType,
    BusinessTemplate,
    ProjectCategory,
)
from company.models import Company


def business_dashboard(request):
    """Simple dashboard placeholder"""
    return render(request, 'business/dashboard.html')


class BusinessConfigurationListView(generic.ListView):
    model = BusinessConfiguration
    template_name = 'business/configuration_list.html'
    context_object_name = 'configs'


class BusinessConfigurationDetailView(generic.DetailView):
    model = BusinessConfiguration
    slug_field = 'slug'
    template_name = 'business/configuration_detail.html'
    context_object_name = 'config'


class BusinessTypeListView(generic.ListView):
    model = BusinessType
    template_name = 'business/type_list.html'
    context_object_name = 'types'


class BusinessTypeDetailView(generic.DetailView):
    model = BusinessType
    slug_field = 'slug'
    template_name = 'business/type_detail.html'
    context_object_name = 'type'


class BusinessTemplateListView(generic.ListView):
    model = BusinessTemplate
    template_name = 'business/template_list.html'
    context_object_name = 'templates'


class BusinessTemplateDetailView(generic.DetailView):
    model = BusinessTemplate
    slug_field = 'slug'
    template_name = 'business/template_detail.html'
    context_object_name = 'template'


def apply_template_to_company(request, template_slug, company_id):
    template = get_object_or_404(BusinessTemplate, slug=template_slug)
    company = get_object_or_404(Company, id=company_id)
    template.apply_to_company(company)
    messages.success(request, 'Template applied successfully.')
    return redirect('company:detail', pk=company.id)


def business_setup_wizard(request):
    return render(request, 'business/setup_wizard.html')


def business_config_api(request):
    data = list(
        BusinessConfiguration.objects.values('id', 'name', 'slug')
    )
    return JsonResponse({'configs': data})


def business_template_api(request):
    data = list(
        BusinessTemplate.objects.filter(is_active=True).values('id', 'name', 'slug')
    )
    return JsonResponse({'templates': data})


def project_categories_api(request):
    data = list(
        ProjectCategory.objects.filter(is_active=True).values('id', 'name', 'slug')
    )
    return JsonResponse({'categories': data})
