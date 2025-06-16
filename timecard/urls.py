from django.urls import path
from . import views

app_name = 'timecard'

urlpatterns = [
    path('', views.TimeCardListView.as_view(), name='list'),
    path('create/', views.TimeCardCreate.as_view(), name='create'),
    path('<int:pk>/edit/', views.TimeCardUpdate.as_view(), name='update'),
    path('<int:pk>/delete/', views.TimeCardDelete.as_view(), name='delete'),
]
