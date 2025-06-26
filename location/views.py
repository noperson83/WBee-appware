from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    View,
    FormView,
)
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
    PermissionRequiredMixin,
)
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import csv
import io

from client.models import Client
from .models import (
    Location,
    BusinessCategory,
    LocationType,
    LocationDocument,
    LocationNote,
    get_dynamic_choices as model_get_dynamic_choices,
)
from .forms import (
    LocationForm,
    LocationDocumentForm,
    LocationNoteForm,
    LocationImportForm,
)


def location_dashboard(request):
    """Dashboard view for locations with statistics"""
    template = 'location/location_dashboard.html'
    
    # Get business category filter if provided
    business_category = request.GET.get('business_category')
    
    # Base querysets
    locations = Location.objects.select_related('client', 'business_category', 'location_type')
    
    if business_category:
        locations = locations.filter(business_category_id=business_category)
    
    # Calculate statistics
    total_locations = locations.count()
    active_locations = locations.filter(status='active').count()
    
    # Get contract value total (if projects exist)
    try:
        from project.models import Project
        total_contract_value = Project.objects.filter(
            location__in=locations
        ).aggregate(total=Sum('contract_value'))['total'] or 0
    except ImportError:
        total_contract_value = 0
    
    # Recent locations
    recent_locations = locations.order_by('-created_at')[:5]
    
    # Business categories for filter
    business_categories = BusinessCategory.objects.filter(is_active=True)
    
    context = {
        'total_locations': total_locations,
        'active_locations': active_locations,
        'total_contract_value': total_contract_value,
        'recent_locations': recent_locations,
        'business_categories': business_categories,
        'selected_category': business_category,
    }
    
    return render(request, template, context)


class LocationListView(ListView):
    """Modern list view for locations"""
    model = Location
    template_name = 'location/location_list.html'
    context_object_name = 'locations'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Location.objects.select_related(
            'client', 'business_category', 'location_type'
        ).prefetch_related('addresses', 'contacts')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(client__company_name__icontains=search) |
                Q(addresses__city__icontains=search)
            ).distinct()
        
        # Filter by business category
        business_category = self.request.GET.get('business_category')
        if business_category:
            queryset = queryset.filter(business_category_id=business_category)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Ordering
        order_by = self.request.GET.get('order_by', '-created_at')
        queryset = queryset.order_by(order_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business_categories = BusinessCategory.objects.filter(is_active=True)
        context['business_categories'] = business_categories

        # Currently applied filters
        current_filters = {
            'search': self.request.GET.get('search', ''),
            'business_category': self.request.GET.get('business_category', ''),
            'status': self.request.GET.get('status', ''),
            'client': self.request.GET.get('client', ''),
            'has_coordinates': self.request.GET.get('has_coordinates', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'sort': self.request.GET.get('sort', '-created_at'),
        }
        context['current_filters'] = current_filters

        # Convenience variables used by templates
        context['search_query'] = current_filters['search']
        context['selected_category'] = current_filters['business_category']
        context['selected_status'] = current_filters['status']

        if current_filters['business_category']:
            selected_cat = business_categories.filter(
                id=current_filters['business_category']
            ).first()
            context['selected_category_name'] = selected_cat.name if selected_cat else ''
        else:
            context['selected_category_name'] = ''

        return context


class LocationDetailView(DetailView):
    """Modern detail view for locations"""
    model = Location
    template_name = 'location/location_detail.html'
    context_object_name = 'location'
    
    def get_queryset(self):
        return Location.objects.select_related(
            'client', 'business_category', 'location_type'
        ).prefetch_related(
            'addresses', 'contacts', 'documents', 'notes'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        location = self.get_object()
        
        # Get related projects if they exist
        try:
            from project.models import Project
            context['projects'] = Project.objects.filter(
                location=location
            ).order_by('-created_at')
            context['active_projects_count'] = context['projects'].exclude(
                status__in=['c', 'm', 'l']
            ).count()
        except ImportError:
            context['projects'] = []
            context['active_projects_count'] = 0
        
        # Recent documents and notes
        context['recent_documents'] = location.documents.filter(
            is_current=True
        ).order_by('-created_at')[:5]
        
        context['recent_notes'] = location.notes.order_by('-created_at')[:5]
        
        # Follow-up notes
        context['followup_notes'] = location.notes.filter(
            requires_followup=True,
            followup_date__gte=timezone.now().date()
        ).order_by('followup_date')
        
        return context


class LocationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create new location"""
    model = Location
    form_class = LocationForm
    template_name = 'location/location_form.html'

    def form_valid(self, form):
        messages.success(self.request, f'Location "{form.instance.name}" created successfully!')
        return super().form_valid(form)
    
    def get_initial(self):
        initial = super().get_initial()
        # Pre-populate client if coming from client detail page
        client_id = self.request.GET.get('client')
        if client_id:
            initial['client'] = client_id
        return initial

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        if form:
            context['location_type_count'] = form.fields['location_type'].queryset.count()
        return context


class LocationUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing location"""
    model = Location
    form_class = LocationForm
    template_name = 'location/location_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, f'Location "{form.instance.name}" updated successfully!')
        return super().form_valid(form)


class LocationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete location (admin only)"""
    model = Location
    template_name = 'location/location_confirm_delete.html'
    success_url = reverse_lazy('location:location-list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        location = self.get_object()
        messages.success(request, f'Location "{location.name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)


# AJAX Views for dynamic forms
@login_required
def get_location_types(request):
    """AJAX view to get location types for a business category"""
    business_category_id = request.GET.get('business_category')
    location_types = []
    
    if business_category_id:
        location_types = list(
            LocationType.objects.filter(
                business_category_id=business_category_id
            ).values('id', 'name')
        )
    
    return JsonResponse({'location_types': location_types})


@login_required
def ajax_dynamic_choices(request):
    """AJAX view to fetch dynamic choices for a business category."""
    business_category_id = request.GET.get('business_category')
    choice_type = request.GET.get('choice_type')

    choices = []
    if business_category_id and choice_type:
        choices = model_get_dynamic_choices(choice_type, business_category_id)

    return JsonResponse({'choices': choices})


# Document management views
class LocationDocumentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Add document to location"""
    model = LocationDocument
    form_class = LocationDocumentForm
    template_name = 'location/document_form.html'
    
    def form_valid(self, form):
        form.instance.location_id = self.kwargs['location_pk']
        form.instance.uploaded_by = self.request.user.get_full_name() or self.request.user.username
        messages.success(self.request, 'Document uploaded successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('location:location-detail', kwargs={'pk': self.kwargs['location_pk']})

    def test_func(self):
        return self.request.user.is_staff


class LocationDocumentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete location document"""
    model = LocationDocument
    template_name = 'location/document_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('location:location-detail', kwargs={'pk': self.object.location.pk})


# Note management views
class LocationNoteCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Add note to location"""
    model = LocationNote
    form_class = LocationNoteForm
    template_name = 'location/note_form.html'
    
    def form_valid(self, form):
        form.instance.location_id = self.kwargs['location_pk']
        form.instance.created_by = self.request.user.get_full_name() or self.request.user.username
        messages.success(self.request, 'Note added successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('location:location-detail', kwargs={'pk': self.kwargs['location_pk']})

    def test_func(self):
        return self.request.user.is_staff


class LocationNoteUpdateView(LoginRequiredMixin, UpdateView):
    """Update location note"""
    model = LocationNote
    form_class = LocationNoteForm
    template_name = 'location/note_form.html'

    def get_success_url(self):
        return reverse('location:location-detail', kwargs={'pk': self.object.location.pk})


class LocationNoteListView(LoginRequiredMixin, ListView):
    """List notes for a specific location with filtering"""
    model = LocationNote
    template_name = 'location/note_list.html'
    context_object_name = 'notes'
    paginate_by = 20

    def get_queryset(self):
        queryset = LocationNote.objects.filter(
            location_id=self.kwargs['location_pk']
        ).order_by('-created_at')

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )

        note_type = self.request.GET.get('note_type')
        if note_type:
            queryset = queryset.filter(note_type=note_type)

        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        req_follow = self.request.GET.get('requires_followup')
        if req_follow in ['true', 'false']:
            queryset = queryset.filter(requires_followup=(req_follow == 'true'))

        client_visible = self.request.GET.get('client_visible')
        if client_visible in ['true', 'false']:
            queryset = queryset.filter(is_client_visible=(client_visible == 'true'))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        location = get_object_or_404(Location, pk=self.kwargs['location_pk'])
        context['location'] = location
        context['today'] = timezone.now().date()
        context['week_from_now'] = context['today'] + timezone.timedelta(days=7)

        notes_all = location.notes.all()
        context['total_notes'] = notes_all.count()
        context['followup_notes_count'] = notes_all.filter(requires_followup=True).count()
        context['client_visible_count'] = notes_all.filter(is_client_visible=True).count()
        context['overdue_followups_count'] = notes_all.filter(
            requires_followup=True,
            followup_date__lt=context['today']
        ).count()

        context['note_type_choices'] = model_get_dynamic_choices('note_type', location.business_category)

        return context


class LocationNoteDetailView(LoginRequiredMixin, DetailView):
    """Display a single location note"""
    model = LocationNote
    template_name = 'location/note_detail.html'
    context_object_name = 'note'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        note = self.object
        context['recent_notes'] = note.location.notes.order_by('-created_at')[:5]
        context['today'] = timezone.now().date()
        return context


class LocationNoteDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a location note"""
    model = LocationNote
    template_name = 'location/note_confirm_delete.html'

    def get_success_url(self):
        return reverse('location:location-detail', kwargs={'pk': self.object.location.pk})


# ============================================================================
# BULK OPERATIONS
# ============================================================================
@login_required
@require_http_methods(["POST"])
def bulk_update_locations(request):
    """Handle bulk actions on multiple locations."""
    try:
        ids_raw = request.POST.get('location_ids', '')
        location_ids = [pk for pk in ids_raw.split(',') if pk]
        action = request.POST.get('action')

        if not location_ids:
            messages.error(request, 'No locations selected')
            return redirect('location:location-list')

        locations = Location.objects.filter(id__in=location_ids)

        if action == 'update_status':
            new_status = request.POST.get('new_status')
            if new_status:
                updated = locations.update(status=new_status)
                messages.success(request, f'Updated status for {updated} locations')
        elif action == 'update_category':
            category_id = request.POST.get('new_business_category')
            if category_id:
                category = BusinessCategory.objects.filter(id=category_id).first()
                updated = locations.update(business_category=category)
                messages.success(request, f'Updated business category for {updated} locations')
        elif action == 'add_note':
            title = request.POST.get('bulk_note_title') or 'Note'
            content = request.POST.get('bulk_note_content', '')
            for loc in locations:
                LocationNote.objects.create(
                    location=loc,
                    title=title,
                    content=content,
                    created_by=request.user.get_full_name() or request.user.username,
                )
            messages.success(request, f'Added note to {locations.count()} locations')
        elif action == 'recalculate_totals':
            for loc in locations:
                loc.calculate_total_contract_value()
            messages.success(request, f'Recalculated totals for {locations.count()} locations')
        elif action == 'export':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="locations.csv"'
            writer = csv.writer(response)
            writer.writerow([
                'Name', 'Client', 'Business Category', 'Location Type', 'Status',
                'Address', 'City', 'State', 'Latitude', 'Longitude',
            ])
            for loc in locations.select_related('client', 'business_category', 'location_type').prefetch_related('addresses'):
                address = loc.primary_address
                writer.writerow([
                    loc.name,
                    loc.client.company_name if loc.client else '',
                    loc.business_category.name if loc.business_category else '',
                    loc.location_type.name if loc.location_type else '',
                    loc.status,
                    address.line1 if address else '',
                    address.city if address else '',
                    address.state_province if address else '',
                    loc.latitude or '',
                    loc.longitude or '',
                ])
            return response
        else:
            messages.error(request, 'Invalid action')

    except Exception as exc:
        messages.error(request, f'Error processing bulk action: {exc}')

    return redirect('location:location-list')
# Utility views
@login_required
def calculate_contract_totals(request, pk):
    """Recalculate contract totals for a location"""
    location = get_object_or_404(Location, pk=pk)
    total = location.calculate_total_contract_value()
    messages.success(request, f'Contract total updated: ${total:,.2f}')
    return redirect('location:location-detail', pk=pk)


# Map views
def location_map_data(request):
    """Return location data for map display"""
    locations = Location.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('client', 'business_category')
    
    map_data = []
    for location in locations:
        map_data.append({
            'id': location.id,
            'name': location.name,
            'client': location.client.company_name,
            'lat': float(location.latitude),
            'lng': float(location.longitude),
            'status': location.status,
            'business_category': location.business_category.name if location.business_category else '',
            'url': location.get_absolute_url()
        })
    
    return JsonResponse({'locations': map_data})


def locations_map_view(request):
    """Display all locations on a map"""
    return render(request, 'location/locations_map.html')


# Export view
class LocationExportView(LoginRequiredMixin, View):
    """Export locations to CSV."""

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="locations.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Name', 'Client', 'Business Category', 'Location Type', 'Status',
            'Address', 'City', 'State', 'Latitude', 'Longitude'
        ])

        locations = Location.objects.select_related(
            'client', 'business_category', 'location_type'
        ).prefetch_related('addresses')

        for location in locations:
            address = location.primary_address
            writer.writerow([
                location.name,
                location.client.company_name if location.client else '',
                location.business_category.name if location.business_category else '',
                location.location_type.name if location.location_type else '',
                location.status,
                address.line1 if address else '',
                address.city if address else '',
                address.state_province if address else '',
                location.latitude or '',
                location.longitude or '',
            ])

        return response


# Legacy support (redirects old jobsite URLs to new location URLs)
def legacy_jobsite_redirect(request, pk):
    """Redirect old jobsite URLs to new location URLs"""
    return redirect('location:location-detail', pk=pk, permanent=True)


class LocationImportView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Import locations from a CSV file."""

    template_name = 'location/location_import.html'
    form_class = LocationImportForm
    permission_required = 'location.add_location'

    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']

        try:
            file_data = csv_file.read().decode('utf-8')
            csv_data = csv.DictReader(io.StringIO(file_data))

            created_count = 0
            for row in csv_data:
                client = Client.objects.filter(
                    company_name=row.get('client', '').strip()
                ).first()
                business_category = BusinessCategory.objects.filter(
                    name=row.get('business_category', '').strip()
                ).first()
                location_type = LocationType.objects.filter(
                    name=row.get('location_type', '').strip()
                ).first()

                Location.objects.create(
                    name=row.get('name', ''),
                    client=client,
                    business_category=business_category,
                    location_type=location_type,
                    description=row.get('description', ''),
                    status=row.get('status', 'active'),
                    latitude=row.get('latitude') or None,
                    longitude=row.get('longitude') or None,
                )
                created_count += 1

            messages.success(
                self.request,
                f'Successfully imported {created_count} locations.'
            )
        except Exception as exc:
            messages.error(self.request, f'Error processing file: {exc}')

        return redirect('location:location-list')


class LocationImportTemplateView(LoginRequiredMixin, View):
    """Provide a CSV template for location import."""

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="location_import_template.csv"'
        )

        writer = csv.writer(response)
        writer.writerow([
            'name', 'client', 'business_category', 'location_type',
            'status', 'description', 'latitude', 'longitude'
        ])
        writer.writerow([
            'Example Site', 'ACME Corp', 'Retail', 'Warehouse',
            'active', 'Example description', '40.7128', '-74.0060'
        ])

        return response
