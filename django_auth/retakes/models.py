from django.conf import settings
from django.db import models
from django.db.models import F
from django.utils import timezone

from accounts.models import Course


class RetakeSlot(models.Model):
    """Время пересдачи по курсу с ограниченным числом мест (ограниченный ресурс)."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='retake_slots', verbose_name='Курс')
    starts_at = models.DateTimeField('Дата и время')
    room = models.CharField('Аудитория', max_length=50)
    capacity = models.PositiveSmallIntegerField('Мест всего')
    booked = models.PositiveSmallIntegerField('Мест занято', default=0)

    class Meta:
        verbose_name = 'Время пересдачи'
        verbose_name_plural = 'Время пересдач'
        ordering = ['starts_at']
        constraints = [
            # занятых мест не может быть больше, чем всего мест — проверяет сама БД
            models.CheckConstraint(condition=models.Q(booked__lte=F('capacity')), name='slot_booked_lte_capacity'),
        ]

    def __str__(self):
        return f'{self.course} · {timezone.localtime(self.starts_at):%d.%m.%Y %H:%M} · ауд. {self.room}'

    @property
    def free(self):
        return self.capacity - self.booked


class RetakeRequest(models.Model):
    """Заявка студента на пересдачу — основная сущность бизнес-процесса."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        SUBMITTED = 'submitted', 'Подана'
        APPROVED = 'approved', 'Одобрена'
        REJECTED = 'rejected', 'Отклонена'
        CANCELLED = 'cancelled', 'Отменена'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='retake_requests',
                              verbose_name='Студент')
    slot = models.ForeignKey(RetakeSlot, on_delete=models.PROTECT, related_name='requests', verbose_name='Пересдача')
    reason = models.TextField('Причина пересдачи')
    status = models.CharField('Статус', max_length=10, choices=Status.choices, default=Status.DRAFT)
    comment = models.CharField('Комментарий методиста', max_length=255, blank=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Изменена', auto_now=True)

    class Meta:
        verbose_name = 'Заявка на пересдачу'
        verbose_name_plural = 'Заявки на пересдачу'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заявка № {self.pk} ({self.get_status_display()})'


class RetakeEvent(models.Model):
    """История заявки: что произошло, кто и когда это сделал."""

    class Action(models.TextChoices):
        CREATED = 'created', 'Создана'
        UPDATED = 'updated', 'Изменена'
        SUBMITTED = 'submitted', 'Подана, место забронировано'
        APPROVED = 'approved', 'Одобрена'
        REJECTED = 'rejected', 'Отклонена, место освобождено'
        CANCELLED = 'cancelled', 'Отменена'

    request = models.ForeignKey(RetakeRequest, on_delete=models.CASCADE, related_name='events', verbose_name='Заявка')
    action = models.CharField('Событие', max_length=10, choices=Action.choices)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                              related_name='retake_events', verbose_name='Инициатор')
    old_status = models.CharField('Было', max_length=10, blank=True)
    new_status = models.CharField('Стало', max_length=10, blank=True)
    details = models.CharField('Подробности', max_length=255, blank=True)
    created_at = models.DateTimeField('Время', auto_now_add=True)

    class Meta:
        verbose_name = 'Событие заявки'
        verbose_name_plural = 'История заявок'
        ordering = ['created_at', 'id']

    def __str__(self):
        return f'{self.request_id}: {self.get_action_display()}'
