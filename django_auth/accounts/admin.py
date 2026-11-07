from django.contrib import admin

from .models import (
    AcademicGroup,
    Course,
    Department,
    Grade,
    StudentProfile,
)

admin.site.site_header = "Администрирование django_auth"
admin.site.site_title = "django_auth"
admin.site.index_title = "Управление данными проекта"


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(AcademicGroup)
class AcademicGroupAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'department',
    )

    list_filter = (
        'department',
    )

    search_fields = (
        'name',
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'department')
    list_filter = ('department',)
    search_fields = ('title',)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'department', 'academic_group')
    list_filter = ('department', 'academic_group')
    search_fields = ('user__username',)
    filter_horizontal = ('courses',)


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'course', 'kind', 'value', 'date')
    list_filter = ('course__department', 'course', 'kind', 'value')
    search_fields = ('student__user__username', 'student__user__last_name')
    date_hierarchy = 'date'
