"""wbee URL Configuration"""

from django.contrib import admin
from django.urls import include, path
from schedule.views import EventCreateView
from django.contrib.staticfiles.urls import static
from django.conf import settings

admin.site.site_header = "WBEE Universal Company Manager"
admin.site.index_title = "Database administration"

# Restrict Django admin to superusers only
def _superuser_only(request):
    return request.user.is_active and request.user.is_superuser

admin.site.has_permission = _superuser_only

urlpatterns = [
    path("", include("pwa.urls")),
    path("", include("home.urls")),
    path("admin/", admin.site.urls),
    path("asset/", include("asset.urls")),
    path("client/", include("client.urls")),
    path("filer/", include("filer.urls")),
    path("hr/", include("hr.urls")),
    path("company/", include("company.urls")),
    path("business/", include("business.urls")),
    path("location/", include("location.urls")),
    path('project/', include('project.urls')),
    path('material/', include('material.urls')),
    path('receipts/', include('receipts.urls')),
    path('travel/', include('travel.urls')),
    path('create-event/<str:proj>/', EventCreateView.as_view(), name='create-event'),
    path("schedule/", include("schedule.urls")),
    path('timecard/', include('timecard.urls')),
    path('helpdesk/', include('helpdesk.urls', namespace="helpdesk")),
    path('todo/', include('todo.urls', namespace="todo")),
    path('wip/', include('wip.urls')),
]

# Include Django debug toolbar URLs in development
if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns

# Add Django site authentication urls (for login, logout, password management)
urlpatterns += [
    path("accounts/", include("django.contrib.auth.urls")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = 'home.views.permission_denied_view'
