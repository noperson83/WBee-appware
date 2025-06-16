from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)

from .models import Receipt, PurchaseType


class ReceiptListView(LoginRequiredMixin, ListView):
    model = Receipt
    template_name = 'receipts/receipt_list.html'
    context_object_name = 'receipts'
    paginate_by = 25
    ordering = ['-date_of_purchase']

    def get_queryset(self):
        return super().get_queryset().select_related('project', 'worker', 'purchase_type')


class ReceiptDetailView(LoginRequiredMixin, DetailView):
    model = Receipt
    template_name = 'receipts/receipt_detail.html'
    context_object_name = 'receipt'


class ReceiptCreateView(LoginRequiredMixin, CreateView):
    model = Receipt
    fields = [
        'date_of_purchase', 'company_name', 'project', 'worker',
        'purchase_type', 'description', 'total_amount', 'currency',
        'is_tax_deductible', 'receipt_image', 'notes',
        'is_reimbursed', 'reimbursement_date'
    ]
    template_name = 'receipts/receipt_form.html'
    success_url = reverse_lazy('receipts:list')


class ReceiptUpdateView(LoginRequiredMixin, UpdateView):
    model = Receipt
    fields = [
        'date_of_purchase', 'company_name', 'project', 'worker',
        'purchase_type', 'description', 'total_amount', 'currency',
        'is_tax_deductible', 'receipt_image', 'notes',
        'is_reimbursed', 'reimbursement_date'
    ]
    template_name = 'receipts/receipt_form.html'
    success_url = reverse_lazy('receipts:list')


class ReceiptDeleteView(LoginRequiredMixin, DeleteView):
    model = Receipt
    template_name = 'receipts/receipt_confirm_delete.html'
    success_url = reverse_lazy('receipts:list')


class PurchaseTypeListView(LoginRequiredMixin, ListView):
    model = PurchaseType
    template_name = 'receipts/purchase_type_list.html'
    context_object_name = 'purchase_types'
    ordering = ['name']


class PurchaseTypeCreateView(LoginRequiredMixin, CreateView):
    model = PurchaseType
    fields = ['name', 'code', 'description', 'is_active']
    template_name = 'receipts/purchase_type_form.html'
    success_url = reverse_lazy('receipts:purchase-type-list')


class PurchaseTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = PurchaseType
    fields = ['name', 'code', 'description', 'is_active']
    template_name = 'receipts/purchase_type_form.html'
    success_url = reverse_lazy('receipts:purchase-type-list')


class PurchaseTypeDetailView(LoginRequiredMixin, DetailView):
    model = PurchaseType
    template_name = 'receipts/purchase_type_detail.html'
    context_object_name = 'purchase_type'


class PurchaseTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = PurchaseType
    template_name = 'receipts/purchase_type_confirm_delete.html'
    success_url = reverse_lazy('receipts:purchase-type-list')
