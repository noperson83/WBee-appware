# client/views.py - Complete Views Implementation

from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from .models import Client, Address, Contact, Revenue, FinancialPeriod
from .forms import ClientForm, AddressForm, ContactForm

class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff permissions"""
    def test_func(self):
        return self.request.user.is_staff

class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin permissions"""
    def test_func(self):
        return (self.request.user.is_staff and 
                hasattr(self.request.user, 'is_admin') and 
                self.request.user.is_admin)

@login_required
def client_dashboard(request):
    """
    Modern client dashboard with statistics and quick access
    """
    template = 'client/client_dashboard.html'
    
    # Get client statistics
    clients = Client.objects.all()
    stats = {
        'total_clients': clients.count(),
        'active_clients': clients.filter(status='active').count(),
        'prospect_clients': clients.filter(status='prospect').count(),
        'inactive_clients': clients.filter(status='inactive').count(),
    }
    
    # Recent clients
    recent_clients = clients.select_related().prefetch_related(
        'contacts', 'addresses'
    ).order_by('-created_at')[:5]
    
    # Top clients by revenue
    top_clients = clients.filter(
        total_revenue__isnull=False
    ).order_by('-total_revenue')[:5]
    
    # Client status distribution
    status_stats = clients.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Business type distribution
    business_stats = clients.exclude(business_type='').values(
        'business_type'
    ).annotate(count=Count('id')).order_by('business_type')
    
    context = {
        'stats': stats,
        'recent_clients': recent_clients,
        'top_clients': top_clients,
        'status_stats': status_stats,
        'business_stats': business_stats,
    }
    
    return render(request, template, context)

class ClientListView(LoginRequiredMixin, generic.ListView):
    """
    Modern client list with search, filtering, and grid/table views
    """
    template_name = 'client/client_list.html'
    model = Client
    context_object_name = 'client_list'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Client.objects.all().select_related().prefetch_related(
            'addresses', 'contacts'
        ).order_by('company_name')
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(company_name__icontains=search_query) |
                Q(contacts__first_name__icontains=search_query) |
                Q(contacts__last_name__icontains=search_query) |
                Q(contacts__email__icontains=search_query) |
                Q(addresses__city__icontains=search_query) |
                Q(addresses__state_province__icontains=search_query)
            ).distinct()
        
        # Status filter
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Business type filter
        business_type_filter = self.request.GET.get('business_type')
        if business_type_filter:
            queryset = queryset.filter(business_type=business_type_filter)
        
        # Sort options
        sort_by = self.request.GET.get('order_by', 'company_name')
        valid_sorts = ['company_name', '-company_name', '-created_at', 'created_at', 
                      '-total_revenue', 'total_revenue', '-date_of_contract']
        if sort_by in valid_sorts:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate counts for stats
        all_clients = Client.objects.all()
        context.update({
            'search_query': self.request.GET.get('search', ''),
            'status_filter': self.request.GET.get('status', ''),
            'business_type_filter': self.request.GET.get('business_type', ''),
            'order_by': self.request.GET.get('order_by', 'company_name'),
            'status_choices': Client.CLIENT_STATUS,
            'business_type_choices': Client.BUSINESS_TYPES,
            'current_filters': {
                'search': self.request.GET.get('search', ''),
                'status': self.request.GET.get('status', ''),
                'business_type': self.request.GET.get('business_type', ''),
            },
            # Additional stats for template
            'active_count': all_clients.filter(status='active').count(),
            'prospect_count': all_clients.filter(status='prospect').count(),
            'total_revenue': all_clients.aggregate(
                Sum('total_revenue')
            )['total_revenue__sum'] or 0,
        })
        return context

class ClientDetailView(LoginRequiredMixin, generic.DetailView):
    """
    Modern client detail view with comprehensive information
    """
    model = Client
    template_name = 'client/client_detail.html'
    context_object_name = 'client_detail'  # Match template expectation
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.get_object()
        
        # Get related data
        addresses = client.addresses.filter(is_active=True).order_by('-is_primary', 'label')
        contacts = client.contacts.filter(is_active=True).order_by('-is_primary', 'contact_type')
        
        # Get jobsites/locations - try both possible model names
        client_job_list = []
        try:
            # Try to import from location app first
            from location.models import Location
            client_job_list = Location.objects.filter(
                client=client
            ).order_by('-created_at')[:10]
        except ImportError:
            try:
                # Fallback to jobsite app
                from jobsite.models import Jobsite
                client_job_list = Jobsite.objects.filter(
                    client=client
                ).order_by('-created_at')[:10]
            except ImportError:
                # Create empty list if neither exists
                client_job_list = []
        
        # Get recent revenue data
        recent_revenues = client.revenues.all().order_by('-period__start_date')[:12]
        
        # Calculate financial summary
        financial_summary = {
            'total_revenue': client.total_revenue or 0,
            'ytd_revenue': client.ytd_revenue or 0,
            'revenue_growth': self.calculate_revenue_growth(client),
            'average_project_value': self.calculate_avg_project_value(client),
        }
        
        context.update({
            'addresses': addresses,
            'contacts': contacts,
            'client_job_list': client_job_list,  # Match template expectation
            'recent_revenues': recent_revenues,
            'financial_summary': financial_summary,
            'primary_address': client.primary_address,
            'primary_contact': client.primary_contact,
            'billing_address': client.billing_address,
        })
        
        return context
    
    def calculate_revenue_growth(self, client):
        """Calculate year-over-year revenue growth"""
        try:
            current_year = timezone.now().year
            previous_year = current_year - 1
            
            current_year_revenue = client.revenues.filter(
                period__start_date__year=current_year
            ).aggregate(
                total=Sum('contract_revenue') + Sum('service_revenue') + 
                      Sum('material_revenue') + Sum('labor_revenue')
            )['total'] or 0
            
            previous_year_revenue = client.revenues.filter(
                period__start_date__year=previous_year
            ).aggregate(
                total=Sum('contract_revenue') + Sum('service_revenue') + 
                      Sum('material_revenue') + Sum('labor_revenue')
            )['total'] or 0
            
            if previous_year_revenue > 0:
                return ((current_year_revenue - previous_year_revenue) / previous_year_revenue) * 100
        except Exception:
            pass
        return 0
    
    def calculate_avg_project_value(self, client):
        """Calculate average project value"""
        try:
            # Try location model first
            from location.models import Location
            projects = Location.objects.filter(
                client=client, 
                contract_value__isnull=False
            )
            if projects.exists():
                total_value = projects.aggregate(Sum('contract_value'))['contract_value__sum']
                return total_value / projects.count() if total_value else 0
        except ImportError:
            try:
                # Fallback to jobsite model
                from jobsite.models import Jobsite
                projects = Jobsite.objects.filter(
                    client=client, 
                    contract_value__isnull=False
                )
                if projects.exists():
                    total_value = projects.aggregate(Sum('contract_value'))['contract_value__sum']
                    return total_value / projects.count() if total_value else 0
            except ImportError:
                pass
        return 0

class ClientCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """
    Modern client creation with enhanced form handling
    """
    model = Client
    form_class = ClientForm
    template_name = 'client/client_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'form_title': 'Create New Client',
            'submit_text': 'Create Client',
            'is_edit': False,
        })
        return context
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Client "{form.instance.company_name}" created successfully!'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('client:detail', kwargs={'pk': self.object.pk})

class ClientUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """
    Modern client update with comprehensive editing
    """
    model = Client
    form_class = ClientForm
    template_name = 'client/client_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get existing contact and address data to populate form
        primary_contact = self.object.primary_contact
        billing_address = self.object.billing_address
        
        context.update({
            'form_title': f'Update {self.object.company_name}',
            'submit_text': 'Update Client',
            'is_edit': True,
            'addresses': self.object.addresses.filter(is_active=True),
            'contacts': self.object.contacts.filter(is_active=True),
            'primary_contact': primary_contact,
            'billing_address': billing_address,
            'client': self.object,  # For template compatibility
        })
        return context
    
    def get_form(self, form_class=None):
        """Pre-populate form with existing contact and address data"""
        form = super().get_form(form_class)
        
        # Pre-populate contact fields
        primary_contact = self.object.primary_contact
        if primary_contact:
            form.fields['contact_first_name'].initial = primary_contact.first_name
            form.fields['contact_last_name'].initial = primary_contact.last_name
            form.fields['contact_title'].initial = primary_contact.title
            form.fields['contact_email'].initial = primary_contact.email
            form.fields['contact_phone'].initial = primary_contact.phone
            form.fields['contact_type'].initial = primary_contact.contact_type
        
        # Pre-populate address fields
        billing_address = self.object.billing_address
        if billing_address:
            form.fields['billing_attention'].initial = billing_address.attention_line
            form.fields['billing_address'].initial = billing_address.line1
            form.fields['billing_address2'].initial = billing_address.line2
            form.fields['billing_city'].initial = billing_address.city
            form.fields['billing_state'].initial = billing_address.state_province
            form.fields['billing_zipcode'].initial = billing_address.postal_code
            form.fields['billing_country'].initial = billing_address.country
        
        return form
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Client "{self.object.company_name}" updated successfully!'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('client:detail', kwargs={'pk': self.object.pk})

class ClientDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """
    Client deletion with enhanced confirmation
    """
    model = Client
    template_name = 'client/client_confirm_delete.html'
    success_url = reverse_lazy('client:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.get_object()
        
        # Get related objects count for warning
        context.update({
            'related_counts': {
                'addresses': client.addresses.count(),
                'contacts': client.contacts.count(),
                'revenues': client.revenues.count(),
            }
        })
        return context
    
    def delete(self, request, *args, **kwargs):
        client_name = self.get_object().company_name
        result = super().delete(request, *args, **kwargs)
        messages.success(request, f'Client "{client_name}" deleted successfully!')
        return result

# AJAX API Views
@login_required
@require_http_methods(["POST"])
def add_client_address(request, pk):
    """AJAX endpoint to add new address"""
    try:
        client = get_object_or_404(Client, id=pk)
        
        # Check if user has permission
        if not request.user.is_staff:
            return JsonResponse({
                'success': False, 
                'message': 'Permission denied'
            }, status=403)
        
        # Validate required fields
        if not request.POST.get('line1'):
            return JsonResponse({
                'success': False,
                'message': 'Street address is required'
            }, status=400)
        
        # Check if this should be the primary address
        is_primary = request.POST.get('is_primary') == 'true'
        if is_primary:
            # Unset other primary addresses
            client.addresses.filter(is_primary=True).update(is_primary=False)
        
        address = Address.objects.create(
            content_object=client,
            label=request.POST.get('label', 'billing'),
            attention_line=request.POST.get('attention_line', ''),
            line1=request.POST.get('line1', ''),
            line2=request.POST.get('line2', ''),
            city=request.POST.get('city', ''),
            state_province=request.POST.get('state_province', ''),
            postal_code=request.POST.get('postal_code', ''),
            country=request.POST.get('country', 'US'),
            is_primary=is_primary
        )
        
        return JsonResponse({
            'success': True,
            'address': {
                'id': str(address.id),
                'label': address.get_label_display(),
                'formatted_address': str(address),
                'is_primary': address.is_primary,
            },
            'message': 'Address added successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error adding address: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def add_client_contact(request, pk):
    """AJAX endpoint to add new contact"""
    try:
        client = get_object_or_404(Client, id=pk)
        
        # Check if user has permission
        if not request.user.is_staff:
            return JsonResponse({
                'success': False, 
                'message': 'Permission denied'
            }, status=403)
        
        # Validate required fields
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        
        if not (first_name or last_name or email):
            return JsonResponse({
                'success': False,
                'message': 'At least name or email is required'
            }, status=400)
        
        # Check if this should be the primary contact
        is_primary = request.POST.get('is_primary') == 'true'
        if is_primary:
            # Unset other primary contacts
            client.contacts.filter(is_primary=True).update(is_primary=False)
        
        contact = Contact.objects.create(
            content_object=client,
            contact_type=request.POST.get('contact_type', 'primary'),
            first_name=first_name,
            last_name=last_name,
            title=request.POST.get('title', ''),
            email=email,
            phone=request.POST.get('phone', ''),
            is_primary=is_primary
        )
        
        return JsonResponse({
            'success': True,
            'contact': {
                'id': str(contact.id),
                'full_name': contact.full_name,
                'contact_type': contact.get_contact_type_display(),
                'email': contact.email,
                'phone': contact.phone,
                'is_primary': contact.is_primary,
            },
            'message': 'Contact added successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error adding contact: {str(e)}'
        }, status=500)

@login_required
def client_search_api(request):
    """API endpoint for client search autocomplete"""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    clients = Client.objects.filter(
        Q(company_name__icontains=query) |
        Q(contacts__first_name__icontains=query) |
        Q(contacts__last_name__icontains=query) |
        Q(contacts__email__icontains=query)
    ).distinct().select_related().prefetch_related('contacts')[:10]
    
    results = []
    for client in clients:
        primary_contact = client.primary_contact
        results.append({
            'id': str(client.id),
            'text': client.company_name,
            'status': client.get_status_display(),
            'url': client.get_absolute_url(),
            'primary_contact': primary_contact.full_name if primary_contact else '',
            'email': primary_contact.email if primary_contact else '',
        })
    
    return JsonResponse({'results': results})

@login_required
def client_financial_dashboard(request, pk):
    """Financial dashboard for specific client"""
    client = get_object_or_404(Client, id=pk)
    
    # Get revenue data for charts
    revenues = client.revenues.all().order_by('period__start_date')
    
    # Calculate financial metrics
    financial_data = {
        'total_revenue': client.total_revenue or 0,
        'ytd_revenue': client.ytd_revenue or 0,
        'revenue_by_type': {
            'contract': sum(r.contract_revenue for r in revenues),
            'service': sum(r.service_revenue for r in revenues),
            'material': sum(r.material_revenue for r in revenues),
            'labor': sum(r.labor_revenue for r in revenues),
        },
        'monthly_revenue': [
            {
                'period': r.period.name,
                'revenue': float(r.total_revenue),
                'date': r.period.start_date.isoformat(),
            }
            for r in revenues.filter(period__period_type='monthly')
        ]
    }
    
    context = {
        'client': client,
        'financial_data': financial_data,
        'revenues': revenues,
    }
    
    return render(request, 'client/client_financial_dashboard.html', context)

@login_required
@require_http_methods(["POST"])
def bulk_update_clients(request):
    """Bulk update multiple clients"""
    try:
        client_ids = request.POST.getlist('client_ids')
        action = request.POST.get('action')
        
        # Check permissions
        if not request.user.is_staff:
            return JsonResponse({
                'success': False, 
                'message': 'Permission denied'
            }, status=403)
        
        if not client_ids:
            return JsonResponse({
                'success': False,
                'message': 'No clients selected'
            }, status=400)
        
        clients = Client.objects.filter(id__in=client_ids)
        
        if action == 'update_status':
            new_status = request.POST.get('new_status')
            if new_status in dict(Client.CLIENT_STATUS):
                updated = clients.update(status=new_status)
                messages.success(
                    request, 
                    f'Updated status for {updated} clients to {dict(Client.CLIENT_STATUS)[new_status]}'
                )
                return JsonResponse({
                    'success': True,
                    'message': f'Updated {updated} clients',
                    'redirect': reverse('client:list')
                })
        
        elif action == 'update_payment_terms':
            new_terms = request.POST.get('new_payment_terms')
            if new_terms in dict(Client.PAYMENT_TERMS):
                updated = clients.update(payment_terms=new_terms)
                messages.success(
                    request, 
                    f'Updated payment terms for {updated} clients'
                )
                return JsonResponse({
                    'success': True,
                    'message': f'Updated {updated} clients',
                    'redirect': reverse('client:list')
                })
        
        elif action == 'export_csv':
            # You could implement CSV export here
            return JsonResponse({
                'success': True,
                'message': 'CSV export would be implemented here'
            })
        
        return JsonResponse({
            'success': False,
            'message': 'Invalid action'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)

# Legacy support for existing URLs
def client(request):
    """Legacy view - redirect to dashboard"""
    return redirect('client:dashboard')

def clientresults(request, firststr):
    """Legacy alphabetical client results - redirect to list with filter"""
    return redirect(f"{reverse('client:list')}?search={firststr}")

def ClientDeView(request, id):
    """Legacy detail view - redirect to new detail view"""
    return redirect('client:detail', pk=id)

# Utility views
@login_required
def export_clients_csv(request):
    """Export clients to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="clients.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Company Name', 'Status', 'Business Type', 'Primary Contact',
        'Email', 'Phone', 'City', 'State', 'Total Revenue', 'YTD Revenue',
        'Date Created'
    ])
    
    clients = Client.objects.all().select_related().prefetch_related(
        'contacts', 'addresses'
    )
    
    for client in clients:
        primary_contact = client.primary_contact
        primary_address = client.primary_address
        
        writer.writerow([
            client.company_name,
            client.get_status_display(),
            client.get_business_type_display() if client.business_type else '',
            primary_contact.full_name if primary_contact else '',
            primary_contact.email if primary_contact else '',
            primary_contact.phone if primary_contact else '',
            primary_address.city if primary_address else '',
            primary_address.state_province if primary_address else '',
            client.total_revenue or 0,
            client.ytd_revenue or 0,
            client.created_at.strftime('%Y-%m-%d')
        ])
    
    return response