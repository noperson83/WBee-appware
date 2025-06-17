from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import WIPItem


class WIPItemListView(LoginRequiredMixin, ListView):
    """Simple list view for work-in-progress items."""
    model = WIPItem
    template_name = "wip/wipitem_list.html"
    context_object_name = "items"
    paginate_by = 25
