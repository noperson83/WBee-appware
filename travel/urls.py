from django.urls import path

from .views import TripListView, TripDetailView, TripCreateView

app_name = "travel"

urlpatterns = [
    path("", TripListView.as_view(), name="trip-list"),
    path("create/", TripCreateView.as_view(), name="trip-create"),
    path("<int:pk>/", TripDetailView.as_view(), name="trip-detail"),
]
