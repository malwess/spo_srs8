from django.db.models import Avg, Count
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import Course, Department

from .permissions import IsMethodistOrReadOnly
from .serializers import CourseSerializer, DepartmentSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    """GET, POST /api/departments/ · GET, PUT, PATCH, DELETE /api/departments/<id>/"""

    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsMethodistOrReadOnly]
    search_fields = ['name']
    ordering_fields = ['name', 'courses_count', 'groups_count']
    ordering = ['name']

    def get_queryset(self):
        return Department.objects.annotate(
            courses_count=Count('courses', distinct=True),
            groups_count=Count('groups', distinct=True),
        )

    def destroy(self, request, *args, **kwargs):
        department = self.get_object()
        count = department.courses.count()
        if count:
            # Удаление факультета удалило бы и все его курсы, поэтому запрещаем
            return Response(
                {'detail': f'Нельзя удалить факультет «{department.name}»: к нему привязано курсов — {count}. '
                           'Сначала перенесите курсы на другой факультет или удалите их.'},
                status=status.HTTP_409_CONFLICT)
        return super().destroy(request, *args, **kwargs)


class CourseViewSet(viewsets.ModelViewSet):
    """GET, POST /api/courses/ · GET, PUT, PATCH, DELETE /api/courses/<id>/

    Серверная фильтрация: ?search=…&department=<id>&ordering=-students_count
    """

    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsMethodistOrReadOnly]
    search_fields = ['title', 'description', 'department__name']
    ordering_fields = ['title', 'students_count', 'grades_count', 'avg_grade', 'id']
    ordering = ['title']

    def get_queryset(self):
        queryset = (Course.objects.select_related('department')
                    .annotate(students_count=Count('students', distinct=True),
                              grades_count=Count('grades', distinct=True),
                              avg_grade=Avg('grades__value')))
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        return queryset
