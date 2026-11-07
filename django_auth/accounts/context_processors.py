from .views import is_methodist


def roles(request):
    """Делает переменную is_methodist доступной во всех шаблонах."""
    user = request.user
    return {
        'is_methodist': user.is_authenticated and is_methodist(user),
    }
