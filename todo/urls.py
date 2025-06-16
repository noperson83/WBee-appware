"""URL configuration for the todo app."""

from django.urls import path

from . import views

app_name = "todo"

urlpatterns = [
    # List management
    path("", views.list_lists, name="lists"),
    path("mine/", views.list_detail, {"list_slug": "mine"}, name="mine"),
    path("add/", views.add_list, name="add_list"),
    path(
        "<int:list_id>/<slug:list_slug>/",
        views.list_detail,
        name="list_detail",
    ),
    path(
        "<int:list_id>/<slug:list_slug>/completed/",
        views.list_detail,
        {"view_completed": True},
        name="list_detail_completed",
    ),
    path(
        "<int:list_id>/<slug:list_slug>/delete/",
        views.del_list,
        name="del_list",
    ),

    # Task management
    path("task/<int:task_id>/", views.task_detail, name="task_detail"),
    path("task/<int:task_id>/delete/", views.delete_task, name="delete_task"),
    path(
        "task/<int:task_id>/toggle/",
        views.toggle_done,
        name="task_toggle_done",
    ),
    path("reorder/", views.reorder_tasks, name="reorder_tasks"),

    # External submission and search
    path("external/add/", views.external_add, name="external_add"),
    path("search/", views.search, name="search"),
]

