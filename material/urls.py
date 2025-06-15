# material/urls.py - Modern URL configuration for inventory management
"""Inventory management URL patterns.
Provides CRUD routes for suppliers, manufacturers, product categories,
products and inventory transactions.
"""

from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = "material"

# Supplier URLs
supplier_patterns = [
    path("", views.SupplierListView.as_view(), name="supplier-list"),
    path("create/", views.SupplierCreateView.as_view(), name="supplier-create"),
    path("<uuid:pk>/", views.SupplierDetailView.as_view(), name="supplier-detail"),
    path("<uuid:pk>/edit/", views.SupplierUpdateView.as_view(), name="supplier-update"),
    path("<uuid:pk>/delete/", views.SupplierDeleteView.as_view(), name="supplier-delete"),
]

# Manufacturer URLs
manufacturer_patterns = [
    path("", views.ManufacturerListView.as_view(), name="manufacturer-list"),
    path("create/", views.ManufacturerCreateView.as_view(), name="manufacturer-create"),
    path("<uuid:pk>/", views.ManufacturerDetailView.as_view(), name="manufacturer-detail"),
    path("<uuid:pk>/edit/", views.ManufacturerUpdateView.as_view(), name="manufacturer-update"),
    path("<uuid:pk>/delete/", views.ManufacturerDeleteView.as_view(), name="manufacturer-delete"),
]

# Product category URLs
category_patterns = [
    path("", views.ProductCategoryListView.as_view(), name="category-list"),
    path("create/", views.ProductCategoryCreateView.as_view(), name="category-create"),
    path("<int:pk>/", views.ProductCategoryDetailView.as_view(), name="category-detail"),
    path("<int:pk>/edit/", views.ProductCategoryUpdateView.as_view(), name="category-update"),
    path("<int:pk>/delete/", views.ProductCategoryDeleteView.as_view(), name="category-delete"),
]

# Product URLs
product_patterns = [
    path("", views.ProductListView.as_view(), name="product-list"),
    path("create/", views.ProductCreateView.as_view(), name="product-create"),
    path("<uuid:pk>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("<uuid:pk>/edit/", views.ProductUpdateView.as_view(), name="product-update"),
    path("<uuid:pk>/delete/", views.ProductDeleteView.as_view(), name="product-delete"),
]

# Inventory transaction URLs
transaction_patterns = [
    path("", views.InventoryTransactionListView.as_view(), name="transaction-list"),
    path("create/", views.InventoryTransactionCreateView.as_view(), name="transaction-create"),
    path("<int:pk>/", views.InventoryTransactionDetailView.as_view(), name="transaction-detail"),
    path("<int:pk>/edit/", views.InventoryTransactionUpdateView.as_view(), name="transaction-update"),
    path("<int:pk>/delete/", views.InventoryTransactionDeleteView.as_view(), name="transaction-delete"),
]

urlpatterns = [
    path("suppliers/", include(supplier_patterns)),
    path("manufacturers/", include(manufacturer_patterns)),
    path("categories/", include(category_patterns)),
    path("products/", include(product_patterns)),
    path("transactions/", include(transaction_patterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
