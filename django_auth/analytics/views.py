from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.utils import timezone

from accounts.models import AcademicGroup, Department

from .services import DASHBOARDS, PERIODS, Filters

# Описание трёх дашбордов: адрес, заголовок, иконка и фильтры, которые на нём доступны
PAGES = {
    'overview': {'title': 'Общий обзор', 'icon': 'chart-pie', 'filters': ['department', 'period']},
    'structure': {'title': 'Факультеты и группы', 'icon': 'building', 'filters': ['department', 'period']},
    'performance': {'title': 'Курсы и успеваемость', 'icon': 'chart-line',
                    'filters': ['department', 'group', 'period']},
}


def filter_options():
    """Значения для выпадающих списков фильтров — тоже из базы."""
    return {
        'departments': Department.objects.order_by('name'),
        'groups': AcademicGroup.objects.select_related('department').order_by('name'),
        'periods': [('all', 'Весь семестр'), ('30', '30 дней'), ('7', '7 дней')],
    }


@login_required
def dashboard(request, name='overview'):
    """Страница дашборда. Данные графиков загружаются отдельно через API."""
    if name not in PAGES:
        raise Http404
    return render(request, f'analytics/{name}.html', {
        'name': name,
        'page': PAGES[name],
        'pages': PAGES,
        **filter_options(),
    })


@login_required
def dashboard_api(request, name):
    """GET /analytics/api/<name>/?department=&group=&period= — показатели дашборда в JSON."""
    if name not in DASHBOARDS:
        raise Http404
    data = DASHBOARDS[name](Filters(request.GET))
    data['generated_at'] = timezone.localtime().strftime('%H:%M:%S')
    return JsonResponse(data)
