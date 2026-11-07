from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from .models import Category, Ticket


class TicketApiTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Тестовая категория')
        self.user = User.objects.create_user('u1', password='Pass2026Test!')
        self.other = User.objects.create_user('u2', password='Pass2026Test!')
        self.client.force_login(self.user)

    def create(self, title='Пересдача по базам данных', **extra):
        return self.client.post('/api/tickets/', {'title': title, 'category': self.category.pk, **extra}, format='json')

    def test_categories_from_db(self):
        names = [c['name'] for c in self.client.get('/api/categories/').json()]
        self.assertIn('Тестовая категория', names)

    def test_create_saves_owner_and_status(self):
        response = self.create()
        self.assertEqual(response.status_code, 201)
        ticket = Ticket.objects.get(pk=response.json()['id'])
        self.assertEqual((ticket.owner, ticket.status), (self.user, 'new'))

    def test_short_title_rejected(self):
        response = self.create(title='Тест')
        self.assertEqual(response.status_code, 400)
        self.assertIn('не менее 5 символов', response.json()['title'][0])

    def test_status_flow(self):
        url = f"/api/tickets/{self.create().json()['id']}/"
        self.assertEqual(self.client.patch(url, {'status': 'done'}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(url, {'status': 'progress'}, format='json').status_code, 200)
        self.assertEqual(self.client.patch(url, {'status': 'done'}, format='json').status_code, 200)
        self.assertEqual(self.client.patch(url, {'title': 'Новая тема обращения'}, format='json').status_code, 400)

    def test_new_ticket_must_be_new(self):
        self.assertEqual(self.create(status='done').status_code, 400)

    def test_delete(self):
        url = f"/api/tickets/{self.create().json()['id']}/"
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(Ticket.objects.exists())

    def test_foreign_ticket_not_available(self):
        url = f"/api/tickets/{self.create().json()['id']}/"
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertEqual(self.client.get('/api/tickets/').json(), [])

    def test_auth_required(self):
        self.client.logout()
        self.assertEqual(self.client.get('/api/tickets/').status_code, 403)
        self.assertEqual(self.client.get('/tickets/').status_code, 302)
