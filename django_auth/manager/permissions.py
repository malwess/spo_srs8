from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.views import is_methodist


class IsMethodistOrReadOnly(BasePermission):
    """Читать данные могут все вошедшие пользователи, изменять — только методист."""

    message = 'Изменять данные может только методист. Войдите под учётной записью методиста.'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_superuser or is_methodist(request.user)
