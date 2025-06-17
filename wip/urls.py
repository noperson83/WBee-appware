from django.urls import path

from . import views

app_name = "wip"

urlpatterns = [
    path("", views.WIPItemListView.as_view(), name="list"),
]
