from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import CategoryViewSet, TicketViewSet, dashboard

router = SimpleRouter()  # корень /api/ уже описан в manager/urls.py
router.register('categories', CategoryViewSet, basename='categories')
router.register('tickets', TicketViewSet, basename='tickets')

urlpatterns = [
    path('tickets/', dashboard, name='tickets_dashboard'),
    path('api/', include(router.urls)),
]
