from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import Group, User
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import Course, Department

from .models import RetakeEvent, RetakeRequest, RetakeSlot


class RetakeProcessTests(APITestCase):
    def setUp(self):
        dep = Department.objects.create(name='ИТ')
        self.course = Course.objects.create(title='Базы данных', department=dep)
        soon = timezone.now() + timedelta(days=7)
        self.slot = RetakeSlot.objects.create(course=self.course, starts_at=soon, room='317', capacity=1)
        self.student = User.objects.create_user('s1', password='x')
        self.other = User.objects.create_user('s2', password='x')
        self.methodist = User.objects.create_user('m', password='x')
        self.methodist.groups.add(Group.objects.create(name='Методист'))
        self.client.force_login(self.student)

    def create(self, slot=None, reason='Пропустила контрольную по болезни'):
        return self.client.post('/api/retakes/', {'slot': (slot or self.slot).pk, 'reason': reason}, format='json')

    def act(self, pk, action, **data):
        return self.client.post(f'/api/retakes/{pk}/{action}/', data, format='json')

    def test_1_create_writes_initial_event(self):
        r = self.create()
        self.assertEqual(r.status_code, 201)
        obj = RetakeRequest.objects.get()
        self.assertEqual((obj.status, obj.events.count()), ('draft', 1))

    def test_2_submit_books_seat_and_logs(self):
        pk = self.create().json()['id']
        self.assertEqual(self.act(pk, 'submit').status_code, 200)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.booked, 1)
        self.assertEqual(RetakeEvent.objects.filter(action='submitted').count(), 1)

    def test_3_forbidden_transition_changes_nothing(self):
        pk = self.create().json()['id']
        self.act(pk, 'submit')
        self.client.force_login(self.methodist)
        self.act(pk, 'approve')
        self.client.force_login(self.student)
        events = RetakeEvent.objects.count()
        r = self.act(pk, 'cancel')                       # одобренную отменить нельзя
        self.assertEqual(r.status_code, 400)
        self.assertEqual(RetakeRequest.objects.get().status, 'approved')
        self.assertEqual(RetakeEvent.objects.count(), events)
        r = self.client.patch(f'/api/retakes/{pk}/', {'status': 'draft'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_4_transaction_rollback(self):
        pk = self.create().json()['id']
        with mock.patch('retakes.services.log', side_effect=RuntimeError('сбой записи истории')):
            with self.assertRaises(RuntimeError):
                self.act(pk, 'submit')
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.booked, 0)                       # место не занято
        self.assertEqual(RetakeRequest.objects.get().status, 'draft')  # статус не изменился

    def test_5_foreign_objects_unavailable(self):
        pk = self.create().json()['id']
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f'/api/retakes/{pk}/').status_code, 404)
        self.assertEqual(self.client.delete(f'/api/retakes/{pk}/').status_code, 404)
        self.assertEqual(self.client.get('/api/retakes/').json(), [])

    def test_6_delete_rules(self):
        pk = self.create().json()['id']
        self.act(pk, 'submit')
        self.assertEqual(self.client.delete(f'/api/retakes/{pk}/').status_code, 400)
        self.act(pk, 'cancel')
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.booked, 0)
        self.assertEqual(self.client.delete(f'/api/retakes/{pk}/').status_code, 204)

    def test_7_no_free_seats_and_duplicate(self):
        self.act(self.create().json()['id'], 'submit')
        r = self.create()                                     # вторая активная по тому же курсу
        self.assertEqual(r.status_code, 400)
        self.client.force_login(self.other)
        self.assertIn('не осталось свободных мест', self.create().json()['slot'][0])

    def test_8_filters(self):
        pk = self.create().json()['id']
        self.act(pk, 'submit')
        self.assertEqual(len(self.client.get('/api/retakes/', {'status': 'submitted', 'course': self.course.pk}).json()), 1)
        self.assertEqual(len(self.client.get('/api/retakes/', {'status': 'draft'}).json()), 0)

    def test_9_roles(self):
        pk = self.create().json()['id']
        self.act(pk, 'submit')
        self.assertEqual(self.act(pk, 'approve').status_code, 403)          # студент не может одобрить
        self.client.force_login(self.methodist)
        self.assertEqual(self.act(pk, 'reject').status_code, 400)           # без причины
        self.assertEqual(self.act(pk, 'reject', comment='Нет допуска').status_code, 200)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.booked, 0)

    def test_10_past_slot(self):
        past = RetakeSlot.objects.create(course=self.course, starts_at=timezone.now() - timedelta(days=1),
                                         room='1', capacity=5)
        self.assertIn('уже прошла', self.create(slot=past).json()['slot'][0])
