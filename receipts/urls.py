from django.urls import path
from . import views

app_name = 'receipts'

urlpatterns = [
    path('', views.ReceiptListView.as_view(), name='list'),
    path('create/', views.ReceiptCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ReceiptDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ReceiptUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ReceiptDeleteView.as_view(), name='delete'),

    # Purchase type management
    path('purchase-types/', views.PurchaseTypeListView.as_view(), name='purchase-type-list'),
    path('purchase-types/create/', views.PurchaseTypeCreateView.as_view(), name='purchase-type-create'),
    path('purchase-types/<int:pk>/', views.PurchaseTypeDetailView.as_view(), name='purchase-type-detail'),
    path('purchase-types/<int:pk>/edit/', views.PurchaseTypeUpdateView.as_view(), name='purchase-type-update'),
    path('purchase-types/<int:pk>/delete/', views.PurchaseTypeDeleteView.as_view(), name='purchase-type-delete'),
]
