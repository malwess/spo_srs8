from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import RedirectView



def healthz(request):
    """Проверка доступности: Django запущен и отвечает. Секретов не раскрывает."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path('', RedirectView.as_view(url='/profile/', permanent=False)),
    path('healthz/', healthz),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('analytics/', include('analytics.urls')),
    path('', include('tickets.urls')),
    path('', include('retakes.urls')),
    path('', include('manager.urls')),
    path('', include('accounts.urls')),
]
