from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import RetakeRequestViewSet, RetakeSlotViewSet, page

router = SimpleRouter()
router.register('retake-slots', RetakeSlotViewSet, basename='retake-slots')
router.register('retakes', RetakeRequestViewSet, basename='retakes')

urlpatterns = [
    path('retakes/', page, name='retakes_page'),
    path('api/', include(router.urls)),
]
