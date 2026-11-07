from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import AcademicGroup, Course, Department, Grade, StudentProfile


class DashboardTests(TestCase):
    """Проверяем, что дашборды считают показатели по данным из базы."""

    def setUp(self):
        dep = Department.objects.create(name='Информационные технологии')
        self.group = AcademicGroup.objects.create(name='М3О-236БВ-25', department=dep)
        self.course = Course.objects.create(title='Базы данных', department=dep)
        user = User.objects.create_user('st', password='Kuznetsova2026!')
        self.student = StudentProfile.objects.create(user=user, department=dep, academic_group=self.group)
        self.student.courses.add(self.course)
        Grade.objects.create(student=self.student, course=self.course, value=5, date=date.today())
        Grade.objects.create(student=self.student, course=self.course, value=3, date=date.today())
        self.client.login(username='st', password='Kuznetsova2026!')

    def api(self, name, **params):
        return self.client.get(f'/analytics/api/{name}/', params).json()

    def test_login_required(self):
        self.client.logout()
        self.assertEqual(self.client.get('/analytics/').status_code, 302)

    def test_pages_open(self):
        for url in ['/analytics/', '/analytics/structure/', '/analytics/performance/']:
            self.assertContains(self.client.get(url), 'data-chart=')

    def test_kpi_from_database(self):
        data = self.api('overview')
        self.assertEqual(data['kpi']['students'], 1)
        self.assertEqual(data['kpi']['grades'], 2)
        self.assertEqual(data['kpi']['avg'], 4.0)
        self.assertEqual(data['charts']['grade_distribution']['series'][0]['data'], [0, 1, 0, 1])

    def test_new_grade_changes_dashboard(self):
        Grade.objects.create(student=self.student, course=self.course, value=2, date=date.today())
        data = self.api('overview')
        self.assertEqual(data['kpi']['grades'], 3)
        self.assertEqual(data['kpi']['success'], 67)

    def test_filters(self):
        other = Department.objects.create(name='Прикладная математика')
        self.assertEqual(self.api('structure', department=other.pk)['kpi']['students'], 0)
        self.assertEqual(self.api('performance', group=self.group.pk)['tables']['top_students'][0]['avg'], 4.0)
