from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AcademicGroupForm, CourseForm, DepartmentForm
from .models import AcademicGroup, Course, Department


def is_methodist(user):
    return user.groups.filter(
        name='Методист'
    ).exists()


@login_required
def profile(request):
    return render(request, 'profile.html', {
        'is_methodist': is_methodist(request.user),
        'department_count': Department.objects.count(),
        'group_count': AcademicGroup.objects.count(),
        'course_count': Course.objects.count(),
        'user_count': User.objects.count(),
        'last_courses': Course.objects.select_related('department').order_by('-id')[:4],
    })


def save_form(request, form_class, instance, list_url, title, success_text):
    form = form_class(request.POST or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        messages.success(request, success_text.format(obj))
        return redirect(list_url)

    return render(request, 'object_form.html', {
        'form': form,
        'title': title,
        'list_url': list_url,
    })


def delete_object(request, obj, list_url, title):
    if request.method == 'POST':
        name = str(obj)
        obj.delete()
        messages.success(request, f'Запись «{name}» удалена.')
        return redirect(list_url)

    return render(request, 'object_confirm_delete.html', {
        'object': obj,
        'title': title,
        'list_url': list_url,
    })


# ---------- Факультеты ----------

@login_required
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'department_list.html', {
        'departments': departments,
        'is_methodist': is_methodist(request.user),
    })


@login_required
@user_passes_test(is_methodist)
def department_create(request):
    return save_form(request, DepartmentForm, None, 'department_list',
                     'Добавление факультета', 'Факультет «{}» добавлен.')


@login_required
@user_passes_test(is_methodist)
def department_update(request, pk):
    department = get_object_or_404(Department, pk=pk)
    return save_form(request, DepartmentForm, department, 'department_list',
                     'Изменение факультета', 'Факультет «{}» сохранён.')


@login_required
@user_passes_test(is_methodist)
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    return delete_object(request, department, 'department_list',
                         'Удаление факультета')


# ---------- Учебные группы ----------

@login_required
def academic_group_list(request):
    groups = AcademicGroup.objects.select_related('department').all()
    return render(request, 'academic_group_list.html', {
        'groups': groups,
        'is_methodist': is_methodist(request.user),
    })


@login_required
@user_passes_test(is_methodist)
def academic_group_create(request):
    return save_form(request, AcademicGroupForm, None, 'academic_group_list',
                     'Добавление учебной группы', 'Группа «{}» добавлена.')


@login_required
@user_passes_test(is_methodist)
def academic_group_update(request, pk):
    group = get_object_or_404(AcademicGroup, pk=pk)
    return save_form(request, AcademicGroupForm, group, 'academic_group_list',
                     'Изменение учебной группы', 'Группа «{}» сохранена.')


@login_required
@user_passes_test(is_methodist)
def academic_group_delete(request, pk):
    group = get_object_or_404(AcademicGroup, pk=pk)
    return delete_object(request, group, 'academic_group_list',
                         'Удаление учебной группы')


# ---------- Курсы ----------

@login_required
def course_list(request):
    courses = Course.objects.select_related('department').all()
    return render(request, 'course_list.html', {
        'courses': courses,
        'is_methodist': is_methodist(request.user),
    })


@login_required
@user_passes_test(is_methodist)
def course_create(request):
    return save_form(request, CourseForm, None, 'course_list',
                     'Добавление курса', 'Курс «{}» добавлен.')


@login_required
@user_passes_test(is_methodist)
def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk)
    return save_form(request, CourseForm, course, 'course_list',
                     'Изменение курса', 'Курс «{}» сохранён.')


@login_required
@user_passes_test(is_methodist)
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    return delete_object(request, course, 'course_list',
                         'Удаление курса')
