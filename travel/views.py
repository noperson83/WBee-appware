from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Trip


class TripListView(LoginRequiredMixin, ListView):
    model = Trip
    template_name = "travel/trip_list.html"
    context_object_name = "trips"
    ordering = ["-start_date"]


class TripDetailView(LoginRequiredMixin, DetailView):
    model = Trip
    template_name = "travel/trip_detail.html"
    context_object_name = "trip"


class TripCreateView(LoginRequiredMixin, CreateView):
    model = Trip
    fields = ["project", "traveler", "start_date", "end_date", "destination", "purpose", "receipts"]
    template_name = "travel/trip_form.html"
    success_url = reverse_lazy("travel:trip-list")
