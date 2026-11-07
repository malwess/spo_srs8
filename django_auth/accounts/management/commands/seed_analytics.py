"""Заполнение базы данными для дашбордов: студенты, записи на курсы и оценки.

Существующие записи (факультеты, группы, курсы, пользователи admin, methodist,
student1) сохраняются, команда только дополняет базу.
"""
import random
from datetime import date, datetime, time, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import AcademicGroup, Course, Department, Grade, StudentProfile

NEW_COURSES = [
    ('Численные методы', 'Методы решения уравнений и систем, интерполяция.', 'Прикладная математика'),
    ('Теория вероятностей', 'Случайные величины, распределения, оценки.', 'Прикладная математика'),
]
NEW_GROUPS = [('М3О-212БВ-25', 'Прикладная математика')]

LAST = ['Иванова', 'Смирнов', 'Кузнецова', 'Попов', 'Васильева', 'Петров', 'Соколова', 'Михайлов',
        'Новикова', 'Фёдоров', 'Морозова', 'Волков', 'Алексеева', 'Лебедев', 'Семёнова', 'Егоров',
        'Павлова', 'Козлов', 'Степанова', 'Николаев', 'Орлова', 'Андреев', 'Макарова', 'Никитин',
        'Захарова', 'Зайцев', 'Соловьёва', 'Борисов', 'Яковлева', 'Григорьев', 'Романова', 'Воробьёв']
FIRST_F = ['Анна', 'Мария', 'Елена', 'Дарья', 'Полина', 'Алиса', 'Виктория', 'Софья']
FIRST_M = ['Иван', 'Артём', 'Максим', 'Дмитрий', 'Кирилл', 'Егор', 'Никита', 'Михаил']
KINDS = ['pz', 'pz', 'pz', 'srs', 'srs', 'lr', 'test']
# Насколько сильна группа: сдвиг вероятностей оценок
GROUP_LEVEL = {'М3О-236БВ-25': 0.35, 'М3О-234БВ-25': 0.0, 'М3О-210БВ-25': 0.2, 'М3О-212БВ-25': -0.25}


class Command(BaseCommand):
    help = 'Добавляет студентов, записи на курсы и оценки для дашбордов'

    def handle(self, *args, **options):
        rnd = random.Random(2026)
        Grade.objects.all().delete()
        User.objects.filter(username__startswith='st_').delete()

        departments = {d.name: d for d in Department.objects.all()}
        for title, descr, dep in NEW_COURSES:
            Course.objects.get_or_create(title=title, defaults={'description': descr, 'department': departments[dep]})
        for name, dep in NEW_GROUPS:
            AcademicGroup.objects.get_or_create(name=name, defaults={'department': departments[dep]})

        groups = list(AcademicGroup.objects.select_related('department'))
        sizes = {'М3О-236БВ-25': 10, 'М3О-234БВ-25': 8, 'М3О-210БВ-25': 7, 'М3О-212БВ-25': 6}
        start = date(2026, 8, 25)
        n = 0
        for group in groups:
            for _ in range(sizes.get(group.name, 6)):
                last = LAST[n % len(LAST)]
                first = rnd.choice(FIRST_F if last.endswith('а') else FIRST_M)
                joined = start + timedelta(days=rnd.randint(0, 56))
                user = User.objects.create_user(
                    username=f'st_{n + 1:02d}', password=None, first_name=first, last_name=last,
                    date_joined=timezone.make_aware(datetime.combine(joined, time(10, rnd.randint(0, 59)))))
                profile = StudentProfile.objects.create(user=user, department=group.department, academic_group=group)
                courses = list(group.department.courses.all())
                profile.courses.set(rnd.sample(courses, k=min(len(courses), rnd.randint(3, 5))))
                n += 1

        # студентка student1 тоже записана на курсы своего факультета
        for profile in StudentProfile.objects.filter(user__username='student1'):
            profile.courses.set(profile.department.courses.all()[:4])

        grades = []
        today = date(2026, 10, 28)
        for profile in StudentProfile.objects.select_related('academic_group', 'user'):
            ability = rnd.gauss(GROUP_LEVEL.get(profile.academic_group.name, 0), 0.45)
            joined = profile.user.date_joined.date()
            for course in profile.courses.all():
                for _ in range(rnd.randint(3, 6)):
                    day = max(joined, date(2026, 9, 1)) + timedelta(days=rnd.randint(0, 55))
                    if day > today:
                        day = today - timedelta(days=rnd.randint(0, 6))
                    score = 3.9 + ability + rnd.gauss(0, 0.7)
                    value = max(2, min(5, round(score)))
                    grades.append(Grade(student=profile, course=course, kind=rnd.choice(KINDS),
                                        value=value, date=day))
        Grade.objects.bulk_create(grades)

        self.stdout.write(self.style.SUCCESS(
            f'Факультетов: {Department.objects.count()}, групп: {AcademicGroup.objects.count()}, '
            f'курсов: {Course.objects.count()}, студентов: {StudentProfile.objects.count()}, '
            f'оценок: {Grade.objects.count()}'))
