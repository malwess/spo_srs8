from django.contrib.auth.models import Group, User
from rest_framework.test import APITestCase

from accounts.models import Course, Department


class CourseApiTests(APITestCase):
    def setUp(self):
        self.it = Department.objects.create(name='Информационные технологии')
        self.math = Department.objects.create(name='Прикладная математика')
        self.db = Course.objects.create(title='Базы данных', department=self.it)
        Course.objects.create(title='Численные методы', department=self.math)
        self.methodist = User.objects.create_user('m', password='Kafedra317Mai!')
        self.methodist.groups.add(Group.objects.create(name='Методист'))
        self.student = User.objects.create_user('s', password='Kuznetsova2026!')
        self.client.force_login(self.methodist)

    def test_get_list_with_related_data(self):
        data = self.client.get('/api/courses/').json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['department_name'], 'Информационные технологии')

    def test_server_filters(self):
        data = self.client.get('/api/courses/', {'search': 'базы', 'department': self.it.pk,
                                                 'ordering': '-students_count'}).json()
        self.assertEqual([c['title'] for c in data], ['Базы данных'])

    def test_full_crud(self):
        created = self.client.post('/api/courses/', {'title': 'Компьютерные сети', 'department': self.it.pk},
                                   format='json')
        self.assertEqual(created.status_code, 201)
        url = f"/api/courses/{created.json()['id']}/"
        self.assertEqual(self.client.patch(url, {'description': 'TCP/IP'}, format='json').json()['description'], 'TCP/IP')
        self.assertEqual(self.client.put(url, {'title': 'Сети ЭВМ', 'department': self.math.pk, 'description': ''},
                                         format='json').status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_validation_errors(self):
        response = self.client.post('/api/courses/', {'title': ''}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('department', response.json())
        duplicate = self.client.post('/api/courses/', {'title': 'базы данных', 'department': self.it.pk}, format='json')
        self.assertEqual(duplicate.json()['title'], ['Курс с таким названием уже есть на этом факультете.'])

    def test_student_cannot_change(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get('/api/courses/').status_code, 200)
        self.assertEqual(self.client.delete(f'/api/courses/{self.db.pk}/').status_code, 403)

    def test_department_with_courses_is_protected(self):
        response = self.client.delete(f'/api/departments/{self.it.pk}/')
        self.assertEqual(response.status_code, 409)
        self.assertTrue(Department.objects.filter(pk=self.it.pk).exists())

    def test_anonymous_has_no_access(self):
        self.client.logout()
        self.assertEqual(self.client.get('/api/courses/').status_code, 403)
