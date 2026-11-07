from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, {'name': 'overview'}, name='analytics_overview'),
    path('structure/', views.dashboard, {'name': 'structure'}, name='analytics_structure'),
    path('performance/', views.dashboard, {'name': 'performance'}, name='analytics_performance'),
    path('api/<str:name>/', views.dashboard_api, name='analytics_api'),
]
