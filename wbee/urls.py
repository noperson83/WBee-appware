"""wbee URL Configuration"""

from django.contrib import admin
from django.urls import include, path
from django.contrib.staticfiles.urls import static
from django.conf import settings
from django.urls import path, re_path

admin.site.site_header = "Distrobution Solutions"
admin.site.index_title = "Database administration configuration."

urlpatterns = [
    path("", include("home.urls")),
    path("grappelli/", include("grappelli.urls")),
    path("admin/", admin.site.urls),
    path("asset/", include("asset.urls")),
    path("client/", include("client.urls")),
    path("filer/", include("filer.urls")),
    path("hr/", include("hr.urls")),
    # path('helpdesk/', include('helpdesk.urls')),
    path("company/", include("company.urls")),
    path("location/", include("location.urls")),
    # path('project/', include('project.urls')),
    # path('material/', include('material.urls')),
    # path('receipts/', include('receipts.urls')),
    path("schedule/", include("schedule.urls")),
    # path('timecard/', include('timecard.urls')),
    # path('todo/', include('todo.urls', namespace="todo")),
    # path('wip/', include('wip.urls')),
]

# Add Django site authentication urls (for login, logout, password management)
urlpatterns += [
    path("accounts/", include("django.contrib.auth.urls")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
