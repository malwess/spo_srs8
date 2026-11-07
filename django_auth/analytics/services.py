"""Расчёт показателей для дашбордов. Все значения берутся из базы через Django ORM."""
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncWeek

from accounts.models import AcademicGroup, Course, Department, Grade, StudentProfile

PERIODS = {'7': 7, '30': 30, 'all': None}


class Filters:
    """Фильтры из адреса запроса: ?department=1&group=2&period=30"""

    def __init__(self, params):
        self.department = params.get('department') or None
        self.group = params.get('group') or None
        self.period = params.get('period') if params.get('period') in PERIODS else 'all'

    def students(self):
        qs = StudentProfile.objects.all()
        if self.department:
            qs = qs.filter(department_id=self.department)
        if self.group:
            qs = qs.filter(academic_group_id=self.group)
        return qs

    def grades(self):
        qs = Grade.objects.filter(student__in=self.students())
        days = PERIODS[self.period]
        if days:
            qs = qs.filter(date__gte=date.today() - timedelta(days=days))
        return qs

    def courses(self):
        qs = Course.objects.all()
        if self.department:
            qs = qs.filter(department_id=self.department)
        return qs

    def groups(self):
        qs = AcademicGroup.objects.all()
        if self.department:
            qs = qs.filter(department_id=self.department)
        if self.group:
            qs = qs.filter(pk=self.group)
        return qs


# ---------- вспомогательные функции ----------

def chart(labels, series, **extra):
    """Единый формат данных для компонента графика."""
    return {'labels': list(labels), 'series': series, **extra}


def avg(value):
    return round(value or 0, 2)


def grade_summary(grades):
    """Количество оценок, средний балл и процент положительных оценок."""
    data = grades.aggregate(total=Count('id'), avg=Avg('value'), passed=Count('id', filter=Q(value__gte=3)))
    total = data['total']
    return {
        'grades': total,
        'avg': avg(data['avg']),
        'success': round(data['passed'] * 100 / total) if total else 0,
    }


def distribution(grades):
    """Сколько выставлено двоек, троек, четвёрок и пятёрок."""
    counts = dict(grades.values_list('value').annotate(n=Count('id')))
    return chart(['2', '3', '4', '5'], [{'name': 'Оценок', 'data': [counts.get(v, 0) for v in (2, 3, 4, 5)]}])


# ---------- дашборд 1: общий обзор ----------

def overview(f):
    students = f.students()
    grades = f.grades()
    deps = Department.objects.annotate(
        st=Count('students', filter=Q(students__in=students), distinct=True),
        cr=Count('courses', distinct=True),
    )
    weeks = (User.objects.filter(student_profile__in=students)
             .annotate(week=TruncWeek('date_joined')).values('week')
             .annotate(n=Count('id')).order_by('week'))
    total, cumulative = 0, []
    for w in weeks:
        total += w['n']
        cumulative.append(total)
    summary = grade_summary(grades)
    return {
        'kpi': {
            'students': students.count(),
            'groups': f.groups().count(),
            'courses': f.courses().count(),
            'grades': summary['grades'],
            'avg': summary['avg'],
            'success': summary['success'],
        },
        'charts': {
            'students_by_department': chart([d.name for d in deps], [d.st for d in deps],
                                            ids=[d.pk for d in deps]),
            'courses_by_department': chart([d.name for d in deps], [{'name': 'Курсов', 'data': [d.cr for d in deps]}],
                                           ids=[d.pk for d in deps]),
            'registrations': chart([w['week'].strftime('%d.%m') for w in weeks],
                                   [{'name': 'Новых за неделю', 'data': [w['n'] for w in weeks]},
                                    {'name': 'Всего студентов', 'data': cumulative}]),
            'grade_distribution': distribution(grades),
        },
    }


# ---------- дашборд 2: факультеты и группы ----------

def structure(f):
    grades = f.grades()
    groups = (f.groups().select_related('department')
              .annotate(st=Count('students', filter=Q(students__in=f.students()), distinct=True),
                        gr=Count('students__grades', filter=Q(students__grades__in=grades)),
                        av=Avg('students__grades__value', filter=Q(students__grades__in=grades)),
                        ok=Count('students__grades', filter=Q(students__grades__in=grades,
                                                               students__grades__value__gte=3)))
              .order_by('-av'))
    names = [g.name for g in groups]
    mix = {v: [] for v in (2, 3, 4, 5)}
    for g in groups:
        counts = dict(grades.filter(student__academic_group=g).values_list('value').annotate(n=Count('id')))
        for v in mix:
            mix[v].append(counts.get(v, 0))
    rows = [{'name': g.name, 'department': g.department.name, 'students': g.st, 'grades': g.gr,
             'avg': avg(g.av), 'success': round(g.ok * 100 / g.gr) if g.gr else 0} for g in groups]
    summary = grade_summary(grades)
    return {
        'kpi': {'groups': len(rows), 'students': f.students().count(), 'avg': summary['avg'],
                'success': summary['success']},
        'charts': {
            'students_by_group': chart(names, [{'name': 'Студентов', 'data': [g.st for g in groups]}]),
            'avg_by_group': chart(names, [{'name': 'Средний балл', 'data': [avg(g.av) for g in groups]}]),
            'grade_mix_by_group': chart(names, [{'name': f'Оценка {v}', 'data': mix[v]} for v in (5, 4, 3, 2)]),
        },
        'tables': {'groups_rating': rows},
    }


# ---------- дашборд 3: курсы и успеваемость ----------

def performance(f):
    grades = f.grades()
    courses = (f.courses()
               .annotate(av=Avg('grades__value', filter=Q(grades__in=grades)),
                         n=Count('grades', filter=Q(grades__in=grades), distinct=True),
                         st=Count('students', filter=Q(students__in=f.students()), distinct=True))
               .order_by('-av'))
    trend = (grades.annotate(week=TruncWeek('date')).values('week')
             .annotate(av=Avg('value'), n=Count('id')).order_by('week'))
    kinds = dict(Grade.KINDS)
    by_kind = grades.values('kind').annotate(n=Count('id')).order_by('-n')
    top = (f.students().select_related('user', 'academic_group')
           .annotate(av=Avg('grades__value', filter=Q(grades__in=grades)),
                     n=Count('grades', filter=Q(grades__in=grades)))
           .filter(n__gt=0).order_by('-av', '-n')[:7])
    summary = grade_summary(grades)
    return {
        'kpi': {'courses': f.courses().count(), 'grades': summary['grades'], 'avg': summary['avg'],
                'success': summary['success']},
        'charts': {
            'avg_by_course': chart([c.title for c in courses],
                                   [{'name': 'Средний балл', 'data': [avg(c.av) for c in courses]}]),
            'students_by_course': chart([c.title for c in courses],
                                        [{'name': 'Студентов', 'data': [c.st for c in courses]},
                                         {'name': 'Оценок', 'data': [c.n for c in courses]}]),
            'avg_trend': chart([t['week'].strftime('%d.%m') for t in trend],
                               [{'name': 'Средний балл', 'data': [avg(t['av']) for t in trend]},
                                {'name': 'Оценок за неделю', 'data': [t['n'] for t in trend]}]),
            'grades_by_kind': chart([kinds[k['kind']] for k in by_kind], [k['n'] for k in by_kind]),
        },
        'tables': {'top_students': [
            {'name': s.user.get_full_name() or s.user.username, 'group': s.academic_group.name if s.academic_group else '—',
             'grades': s.n, 'avg': avg(s.av)} for s in top]},
    }


DASHBOARDS = {'overview': overview, 'structure': structure, 'performance': performance}
