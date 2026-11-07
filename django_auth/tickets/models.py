from django.conf import settings
from django.db import models

from accounts.models import Course


class Category(models.Model):
    """Тип обращения: пересдача, перенос срока, справка и т. д. (справочник)."""

    name = models.CharField('Название', max_length=100, unique=True)

    class Meta:
        verbose_name = 'Категория обращения'
        verbose_name_plural = 'Категории обращений'
        ordering = ['name']

    def __str__(self):
        return self.name


class Ticket(models.Model):
    """Обращение студента в учебный офис кафедры."""

    class Status(models.TextChoices):
        NEW = 'new', 'Новое'
        PROGRESS = 'progress', 'На рассмотрении'
        DONE = 'done', 'Выполнено'

    title = models.CharField('Тема', max_length=200)
    description = models.TextField('Описание', blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='tickets',
                                 verbose_name='Категория')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='tickets', verbose_name='Курс')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets',
                              verbose_name='Автор')
    status = models.CharField('Статус', max_length=10, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Изменено', auto_now=True)

    class Meta:
        verbose_name = 'Обращение'
        verbose_name_plural = 'Обращения'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
