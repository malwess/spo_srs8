"""Учебные данные для записи на пересдачу: время пересдач и несколько заявок с историей."""
from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Course
from retakes.models import RetakeEvent, RetakeRequest, RetakeSlot
from retakes.services import log, perform

# (курс, через сколько дней, время, аудитория, мест)
SLOTS = [
    ('Базы данных', 12, time(10, 0), '317', 6),
    ('Базы данных', 26, time(14, 0), '317', 4),
    ('Веб-программирование', 14, time(12, 0), '412', 5),
    ('Программирование на Python', 9, time(9, 0), '305', 2),
    ('Численные методы', 16, time(13, 30), '219', 4),
    ('Теория вероятностей', 21, time(11, 0), '219', 3),
    ('Операционные системы', -5, time(10, 0), '305', 4),     # уже прошла
]

REQUESTS = [
    # (пользователь, курс слота, причина, действия: (действие, кто, комментарий))
    ('student1', 'Программирование на Python', 'Не сдала лабораторную работу № 3 из-за болезни.',
     [('submit', 'student1', '')]),
    ('st_02', 'Программирование на Python', 'Получил неудовлетворительную оценку за контрольную.',
     [('submit', 'st_02', ''), ('approve', 'methodist', 'Допущен')]),
    ('st_05', 'Базы данных', 'Пропустил контрольную работу по уважительной причине.',
     [('submit', 'st_05', '')]),
    ('st_07', 'Базы данных', 'Хочу исправить оценку за контрольную работу.',
     [('submit', 'st_07', ''), ('reject', 'methodist', 'Оценка 4 — пересдача на повышение не предусмотрена')]),
    ('st_12', 'Численные методы', 'Не успела сдать СРС 2 в срок.', [('submit', 'st_12', ''), ('cancel', 'st_12', '')]),
]


class Command(BaseCommand):
    help = 'Создаёт время пересдач и учебные заявки'

    def handle(self, *args, **options):
        RetakeRequest.objects.all().delete()
        RetakeSlot.objects.all().delete()
        today = timezone.localdate()
        slots = {}
        for title, days, at, room, capacity in SLOTS:
            starts = timezone.make_aware(datetime.combine(today + timedelta(days=days), at))
            slot = RetakeSlot.objects.create(course=Course.objects.get(title=title), starts_at=starts,
                                             room=room, capacity=capacity)
            slots.setdefault(title, slot)
        for username, title, reason, steps in REQUESTS:
            owner = User.objects.get(username=username)
            obj = RetakeRequest.objects.create(owner=owner, slot=slots[title], reason=reason)
            log(obj, RetakeEvent.Action.CREATED, owner, '', obj.status, f'Пересдача: {obj.slot}')
            for action, who, comment in steps:
                perform(obj, action, User.objects.get(username=who), comment)
        self.stdout.write(self.style.SUCCESS(
            f'Пересдач: {RetakeSlot.objects.count()}, заявок: {RetakeRequest.objects.count()}, '
            f'событий: {RetakeEvent.objects.count()}'))
