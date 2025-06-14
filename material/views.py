# material/views.py - Inventory Management Views
"""CRUD views for inventory models."""

from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)

from .models import (
    Supplier, Manufacturer, ProductCategory, Product, InventoryTransaction
)


# Supplier Views
class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = "material/supplier_list.html"
    context_object_name = "suppliers"
    paginate_by = 20


class SupplierDetailView(LoginRequiredMixin, DetailView):
    model = Supplier
    template_name = "material/supplier_detail.html"
    context_object_name = "supplier"


class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    fields = "__all__"
    template_name = "material/supplier_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    fields = "__all__"
    template_name = "material/supplier_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    model = Supplier
    template_name = "material/supplier_confirm_delete.html"
    success_url = reverse_lazy("material:supplier-list")


# Manufacturer Views
class ManufacturerListView(LoginRequiredMixin, ListView):
    model = Manufacturer
    template_name = "material/manufacturer_list.html"
    context_object_name = "manufacturers"
    paginate_by = 20


class ManufacturerDetailView(LoginRequiredMixin, DetailView):
    model = Manufacturer
    template_name = "material/manufacturer_detail.html"
    context_object_name = "manufacturer"


class ManufacturerCreateView(LoginRequiredMixin, CreateView):
    model = Manufacturer
    fields = "__all__"
    template_name = "material/manufacturer_form.html"

    def get_success_url(self):
        return reverse("material:manufacturer-detail", kwargs={"pk": self.object.pk})


class ManufacturerUpdateView(LoginRequiredMixin, UpdateView):
    model = Manufacturer
    fields = "__all__"
    template_name = "material/manufacturer_form.html"

    def get_success_url(self):
        return reverse("material:manufacturer-detail", kwargs={"pk": self.object.pk})


class ManufacturerDeleteView(LoginRequiredMixin, DeleteView):
    model = Manufacturer
    template_name = "material/manufacturer_confirm_delete.html"
    success_url = reverse_lazy("material:manufacturer-list")


# Product Category Views
class ProductCategoryListView(LoginRequiredMixin, ListView):
    model = ProductCategory
    template_name = "material/category_list.html"
    context_object_name = "categories"
    paginate_by = 20


class ProductCategoryDetailView(LoginRequiredMixin, DetailView):
    model = ProductCategory
    template_name = "material/category_detail.html"
    context_object_name = "category"


class ProductCategoryCreateView(LoginRequiredMixin, CreateView):
    model = ProductCategory
    fields = "__all__"
    template_name = "material/category_form.html"

    def get_success_url(self):
        return reverse("material:category-detail", kwargs={"pk": self.object.pk})


class ProductCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductCategory
    fields = "__all__"
    template_name = "material/category_form.html"

    def get_success_url(self):
        return reverse("material:category-detail", kwargs={"pk": self.object.pk})


class ProductCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductCategory
    template_name = "material/category_confirm_delete.html"
    success_url = reverse_lazy("material:category-list")


# Product Views
class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "material/product_list.html"
    context_object_name = "products"
    paginate_by = 20


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = "material/product_detail.html"
    context_object_name = "product"


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    fields = "__all__"
    template_name = "material/product_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    fields = "__all__"
    template_name = "material/product_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = "material/product_confirm_delete.html"
    success_url = reverse_lazy("material:product-list")


# Inventory Transaction Views
class InventoryTransactionListView(LoginRequiredMixin, ListView):
    model = InventoryTransaction
    template_name = "material/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 20


class InventoryTransactionDetailView(LoginRequiredMixin, DetailView):
    model = InventoryTransaction
    template_name = "material/transaction_detail.html"
    context_object_name = "transaction"


class InventoryTransactionCreateView(LoginRequiredMixin, CreateView):
    model = InventoryTransaction
    fields = "__all__"
    template_name = "material/transaction_form.html"

    def get_success_url(self):
        return reverse("material:transaction-detail", kwargs={"pk": self.object.pk})


class InventoryTransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = InventoryTransaction
    fields = "__all__"
    template_name = "material/transaction_form.html"

    def get_success_url(self):
        return reverse("material:transaction-detail", kwargs={"pk": self.object.pk})


class InventoryTransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = InventoryTransaction
    template_name = "material/transaction_confirm_delete.html"
    success_url = reverse_lazy("material:transaction-list")
