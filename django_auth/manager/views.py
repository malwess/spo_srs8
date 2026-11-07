from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from accounts.views import is_methodist


@login_required
@ensure_csrf_cookie
def manager(request):
    """Страница «Менеджер данных». Все данные она получает и меняет через REST API."""
    return render(request, 'manager/index.html', {
        'can_edit': request.user.is_superuser or is_methodist(request.user),
    })
