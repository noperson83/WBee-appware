"""wbee URL Configuration"""

from django.contrib import admin
from django.urls import include, path
from schedule.views import EventCreateView
from django.contrib.staticfiles.urls import static
from django.conf import settings

admin.site.site_header = "Distribution Solutions"
admin.site.index_title = "Database administration configuration."

# Restrict Django admin to superusers only
def _superuser_only(request):
    return request.user.is_active and request.user.is_superuser

admin.site.has_permission = _superuser_only

urlpatterns = [
    path("", include("home.urls")),
    path("grappelli/", include("grappelli.urls")),
    path("admin/", admin.site.urls),
    path("asset/", include("asset.urls")),
    path("client/", include("client.urls")),
    path("filer/", include("filer.urls")),
    path("hr/", include("hr.urls")),
    path("company/", include("company.urls")),
    path("location/", include("location.urls")),
    path('project/', include('project.urls')),
    path('material/', include('material.urls')),
    path('receipts/', include('receipts.urls')),
    path('create-event/<str:proj>/', EventCreateView.as_view(), name='create-event'),
    path("schedule/", include("schedule.urls")),
    path('timecard/', include('timecard.urls')),
    path('helpdesk/', include('helpdesk.urls', namespace="helpdesk")),
    path('todo/', include('todo.urls', namespace="todo")),
    path('wip/', include('wip.urls')),
]

# Add Django site authentication urls (for login, logout, password management)
urlpatterns += [
    path("accounts/", include("django.contrib.auth.urls")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
