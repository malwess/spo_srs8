from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Category, Ticket
from .serializers import CategorySerializer, TicketSerializer


@login_required
@ensure_csrf_cookie
def dashboard(request):
    """Страница «Мои обращения». Данные загружаются через REST API."""
    return render(request, 'tickets/dashboard.html')


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/categories/ — справочник категорий (только чтение)."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class TicketViewSet(viewsets.ModelViewSet):
    """CRUD для обращений текущего пользователя: /api/tickets/ и /api/tickets/<id>/"""

    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title', 'status']

    def get_queryset(self):
        # Пользователь видит и может менять только собственные обращения:
        # чужое обращение для него «не существует» — API вернёт 404
        queryset = Ticket.objects.filter(owner=self.request.user).select_related('category', 'course')
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        # владельца назначает сервер по сессии, а не браузер
        serializer.save(owner=self.request.user)
