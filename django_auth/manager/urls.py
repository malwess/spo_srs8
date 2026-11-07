from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import api, views

router = DefaultRouter()
router.register('departments', api.DepartmentViewSet, basename='department')
router.register('courses', api.CourseViewSet, basename='course')

urlpatterns = [
    path('manager/', views.manager, name='manager'),
    path('api/', include(router.urls)),
]
