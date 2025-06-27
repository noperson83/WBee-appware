from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.http import JsonResponse

from .models import BusinessConfiguration, BusinessType, ProjectCategory, BusinessTemplate
from company.models import Company


class BusinessConfigurationListView(LoginRequiredMixin, ListView):
    """List all business configurations"""
    model = BusinessConfiguration
    template_name = 'business/configuration_list.html'
    context_object_name = 'configurations'
    paginate_by = 20

    def get_queryset(self):
        queryset = BusinessConfiguration.objects.annotate(
            companies_count=Count('company')
        )

        # Filter by deployment type
        deployment_type = self.request.GET.get('deployment_type')
        if deployment_type:
            queryset = queryset.filter(deployment_type=deployment_type)

        # Filter by billing model
        billing_model = self.request.GET.get('billing_model')
        if billing_model:
            queryset = queryset.filter(billing_model=billing_model)

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset.filter(is_active=True).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['deployment_types'] = BusinessConfiguration.DEPLOYMENT_TYPES
        context['billing_models'] = BusinessConfiguration.BILLING_MODELS
        context['search_query'] = self.request.GET.get('search', '')
        return context


class BusinessConfigurationDetailView(LoginRequiredMixin, DetailView):
    """Detail view for business configuration"""
    model = BusinessConfiguration
    template_name = 'business/configuration_detail.html'
    context_object_name = 'config'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = self.object

        # Get companies using this configuration
        context['companies'] = Company.objects.filter(
            business_config=config,
            is_active=True
        ).order_by('company_name')

        # Get project categories for this configuration
        context['project_categories'] = config.get_default_categories()

        # Get available templates for this configuration
        context['templates'] = BusinessTemplate.objects.filter(
            business_config=config,
            is_active=True
        ).order_by('-is_featured', 'name')

        return context


class BusinessTypeListView(LoginRequiredMixin, ListView):
    """List all business types"""
    model = BusinessType
    template_name = 'business/type_list.html'
    context_object_name = 'business_types'

    def get_queryset(self):
        return BusinessType.objects.filter(is_active=True).annotate(
            categories_count=Count('project_categories')
        ).order_by('order', 'name')


class BusinessTypeDetailView(LoginRequiredMixin, DetailView):
    """Detail view for business type"""
    model = BusinessType
    template_name = 'business/type_detail.html'
    context_object_name = 'business_type'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business_type = self.object

        # Get project categories for this business type
        context['project_categories'] = business_type.project_categories.filter(
            is_active=True
        ).order_by('order', 'name')

        # Get companies of this business type
        context['companies'] = Company.objects.filter(
            business_category__in=business_type.project_categories.values('id'),
            is_active=True
        ).order_by('company_name')[:10]

        return context


class BusinessTemplateListView(LoginRequiredMixin, ListView):
    """List all business templates"""
    model = BusinessTemplate
    template_name = 'business/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20

    def get_queryset(self):
        queryset = BusinessTemplate.objects.select_related(
            'business_type', 'business_config'
        )

        # Filter by business type
        business_type = self.request.GET.get('business_type')
        if business_type:
            queryset = queryset.filter(business_type__slug=business_type)

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset.filter(is_active=True).order_by('-is_featured', '-usage_count', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['business_types'] = BusinessType.objects.filter(is_active=True)
        context['featured_templates'] = BusinessTemplate.objects.filter(
            is_featured=True, is_active=True
        ).order_by('name')[:6]
        return context


class BusinessTemplateDetailView(LoginRequiredMixin, DetailView):
    """Detail view for business template"""
    model = BusinessTemplate
    template_name = 'business/template_detail.html'
    context_object_name = 'template'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        template = self.object

        # Parse template data for display
        template_data = template.template_data
        context['categories'] = template_data.get('categories', [])
        context['workflow_requirements'] = template_data.get('workflow_requirements', {})
        context['default_settings'] = template_data.get('default_settings', {})

        return context


# Utility Views
@login_required
def business_dashboard(request):
    """Business management dashboard"""
    context = {
        'total_configurations': BusinessConfiguration.objects.filter(is_active=True).count(),
        'total_business_types': BusinessType.objects.filter(is_active=True).count(),
        'total_templates': BusinessTemplate.objects.filter(is_active=True).count(),
        'recent_configurations': BusinessConfiguration.objects.filter(
            is_active=True
        ).order_by('-created_at')[:5],
        'popular_templates': BusinessTemplate.objects.filter(
            is_active=True
        ).order_by('-usage_count')[:5],
        'featured_templates': BusinessTemplate.objects.filter(
            is_featured=True, is_active=True
        ).order_by('name')[:6],
    }

    return render(request, 'business/dashboard.html', context)


@login_required
def apply_template_to_company(request, template_slug, company_id):
    """Apply a business template to a company"""
    template = get_object_or_404(BusinessTemplate, slug=template_slug, is_active=True)
    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        try:
            success = template.apply_to_company(company)
            if success:
                messages.success(
                    request,
                    f'Business template "{template.name}" applied to {company.company_name} successfully.'
                )
            else:
                messages.error(
                    request,
                    f'Failed to apply template "{template.name}" to {company.company_name}.'
                )
        except Exception as e:
            messages.error(
                request,
                f'Error applying template: {str(e)}'
            )

        return redirect('company:detail', pk=company.id)

    context = {
        'template': template,
        'company': company,
    }
    return render(request, 'business/apply_template_confirm.html', context)


@login_required
def business_setup_wizard(request):
    """Step-by-step business setup wizard"""
    step = request.GET.get('step', '1')

    if step == '1':
        # Step 1: Choose business type
        business_types = BusinessType.objects.filter(is_active=True).order_by('order', 'name')
        context = {'business_types': business_types, 'step': 1}
        return render(request, 'business/setup_wizard_step1.html', context)

    elif step == '2':
        # Step 2: Choose configuration
        business_type_slug = request.GET.get('business_type')
        if business_type_slug:
            business_type = get_object_or_404(BusinessType, slug=business_type_slug)
            configurations = BusinessConfiguration.objects.filter(is_active=True)
            templates = BusinessTemplate.objects.filter(
                business_type=business_type, is_active=True
            ).order_by('-is_featured', 'name')

            context = {
                'business_type': business_type,
                'configurations': configurations,
                'templates': templates,
                'step': 2
            }
            return render(request, 'business/setup_wizard_step2.html', context)

    elif step == '3':
        # Step 3: Configure details
        template_slug = request.GET.get('template')
        config_slug = request.GET.get('config')

        context = {'step': 3}

        if template_slug:
            template = get_object_or_404(BusinessTemplate, slug=template_slug)
            context['template'] = template
            context['template_data'] = template.template_data

        if config_slug:
            config = get_object_or_404(BusinessConfiguration, slug=config_slug)
            context['config'] = config

        return render(request, 'business/setup_wizard_step3.html', context)

    # Default to step 1
    return redirect('business:setup-wizard')


# API Views
@login_required
def business_config_api(request):
    """API endpoint for business configuration data"""
    configs = BusinessConfiguration.objects.filter(is_active=True).values(
        'id', 'name', 'slug', 'deployment_type', 'billing_model'
    )
    return JsonResponse({'configurations': list(configs)})


@login_required
def business_template_api(request):
    """API endpoint for business template data"""
    business_type_slug = request.GET.get('business_type')

    templates = BusinessTemplate.objects.filter(is_active=True)
    if business_type_slug:
        templates = templates.filter(business_type__slug=business_type_slug)

    template_data = templates.values(
        'id', 'name', 'slug', 'description', 'is_featured', 'usage_count'
    )

    return JsonResponse({'templates': list(template_data)})


@login_required
def project_categories_api(request):
    """API endpoint for project categories"""
    business_config_id = request.GET.get('business_config')
    business_type_id = request.GET.get('business_type')

    categories = ProjectCategory.objects.filter(is_active=True)

    if business_config_id:
        categories = categories.filter(business_config_id=business_config_id)
    elif business_type_id:
        categories = categories.filter(business_type_id=business_type_id)

    category_data = categories.values(
        'id', 'name', 'slug', 'icon', 'color', 'is_billable', 'default_unit'
    ).order_by('order', 'name')

    return JsonResponse({'categories': list(category_data)})
