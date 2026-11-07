from django.contrib.auth.models import Group, User
from django.test import TestCase

from .models import AcademicGroup, Course, Department


class AccessTests(TestCase):
    def setUp(self):
        self.dep = Department.objects.create(name="Информационные технологии")
        self.group = AcademicGroup.objects.create(name="М3О-236БВ-25", department=self.dep)
        self.course = Course.objects.create(title="Базы данных", department=self.dep)

        self.student = User.objects.create_user(username="student2", password="Kuznetsova2026!")
        self.methodist = User.objects.create_user(username="methodist2", password="Kafedra317Mai!")
        role = Group.objects.create(name="Методист")
        self.methodist.groups.add(role)

    def test_pages_require_login(self):
        for url in ["/departments/", "/groups/", "/courses/"]:
            response = self.client.get(url)
            self.assertRedirects(response, "/accounts/login/?next=" + url)

    def test_student_sees_lists_without_buttons(self):
        self.client.login(username="student2", password="Kuznetsova2026!")
        response = self.client.get("/groups/")
        self.assertContains(response, "М3О-236БВ-25")
        self.assertNotContains(response, "Изменить")
        self.assertNotContains(response, "Добавить группу")

    def test_student_cannot_open_edit_pages(self):
        self.client.login(username="student2", password="Kuznetsova2026!")
        for url in ["/departments/add/", f"/groups/{self.group.id}/edit/", f"/courses/{self.course.id}/delete/"]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/accounts/login/", response.url)

    def test_methodist_sees_buttons(self):
        self.client.login(username="methodist2", password="Kafedra317Mai!")
        response = self.client.get("/courses/")
        self.assertContains(response, "Добавить курс")
        self.assertContains(response, "Изменить")
        self.assertContains(response, "Удалить")

    def test_methodist_crud(self):
        self.client.login(username="methodist2", password="Kafedra317Mai!")
        self.client.post("/departments/add/", {"name": "Автоматизация"})
        dep = Department.objects.get(name="Автоматизация")
        self.client.post(f"/departments/{dep.id}/edit/", {"name": "Автоматизация и управление"})
        dep.refresh_from_db()
        self.assertEqual(dep.name, "Автоматизация и управление")
        self.client.post(f"/departments/{dep.id}/delete/")
        self.assertFalse(Department.objects.filter(id=dep.id).exists())

    def test_student_post_does_not_change_data(self):
        self.client.login(username="student2", password="Kuznetsova2026!")
        self.client.post(f"/courses/{self.course.id}/delete/")
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())
