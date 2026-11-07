"""Бизнес-процесс «Запись на пересдачу».

Все изменения статуса проходят только через функцию perform(): она проверяет права,
допустимость перехода и бизнес-правила, а изменения заявки, места в пересдаче и
записи истории сохраняет в одной транзакции.
"""
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.views import is_methodist

from .models import RetakeEvent, RetakeRequest, RetakeSlot

S = RetakeRequest.Status
ACTIVE = (S.SUBMITTED, S.APPROVED)

# Таблица переходов: действие → (из каких статусов, в какой статус, кто выполняет)
TRANSITIONS = {
    'submit': ({S.DRAFT}, S.SUBMITTED, 'owner'),
    'approve': ({S.SUBMITTED}, S.APPROVED, 'methodist'),
    'reject': ({S.SUBMITTED}, S.REJECTED, 'methodist'),
    'cancel': ({S.DRAFT, S.SUBMITTED}, S.CANCELLED, 'owner'),
}
EVENT_FOR_ACTION = {'submit': RetakeEvent.Action.SUBMITTED, 'approve': RetakeEvent.Action.APPROVED,
                    'reject': RetakeEvent.Action.REJECTED, 'cancel': RetakeEvent.Action.CANCELLED}
ACTION_LABELS = {'submit': 'Подать', 'approve': 'Одобрить', 'reject': 'Отклонить', 'cancel': 'Отменить'}


def can_manage(user):
    return user.is_superuser or is_methodist(user)


def allowed_actions(request_obj, user):
    """Какие действия доступны пользователю — интерфейс показывает только эти кнопки."""
    result = []
    for action, (sources, _, who) in TRANSITIONS.items():
        if request_obj.status not in sources:
            continue
        if who == 'owner' and request_obj.owner_id == user.id:
            result.append(action)
        if who == 'methodist' and can_manage(user) and request_obj.owner_id != user.id:
            result.append(action)
    return result


def log(request_obj, action, user, old='', new='', details=''):
    return RetakeEvent.objects.create(request=request_obj, action=action, actor=user,
                                      old_status=old, new_status=new, details=details)


def check_slot(slot, owner, exclude_pk=None):
    """Правила 1–3: время пересдачи в будущем, есть места, нет другой активной заявки по курсу."""
    if slot.starts_at <= timezone.now():
        raise ValidationError({'slot': 'Эта пересдача уже прошла — выберите другое время.'})
    if slot.free <= 0:
        raise ValidationError({'slot': 'На эту пересдачу не осталось свободных мест.'})
    duplicate = (RetakeRequest.objects.filter(owner=owner, slot__course=slot.course_id, status__in=ACTIVE)
                 .exclude(pk=exclude_pk))
    if duplicate.exists():
        raise ValidationError({'slot': f'У вас уже есть поданная заявка на пересдачу по курсу «{slot.course}».'})


@transaction.atomic
def perform(request_obj, action, user, comment=''):
    """Выполнить действие бизнес-процесса. Всё внутри — одна транзакция."""
    if action not in TRANSITIONS:
        raise ValidationError({'action': 'Неизвестное действие.'})
    sources, target, who = TRANSITIONS[action]

    # блокируем строку заявки, чтобы два одновременных запроса не изменили её дважды
    obj = RetakeRequest.objects.select_for_update().get(pk=request_obj.pk)

    if who == 'owner' and obj.owner_id != user.id:
        raise PermissionDenied('Это действие может выполнить только автор заявки.')
    if who == 'methodist':
        if not can_manage(user):
            raise PermissionDenied('Одобрять и отклонять заявки может только методист.')
        if obj.owner_id == user.id:
            raise PermissionDenied('Нельзя рассматривать собственную заявку.')
    if obj.status not in sources:
        raise ValidationError({'status': (
            f'Недопустимый переход: заявку в статусе «{obj.get_status_display()}» нельзя '
            f'«{ACTION_LABELS[action].lower()}». Разрешено только для статусов: '
            + ', '.join(f'«{s.label}»' for s in sources) + '.')})
    if action == 'reject' and not comment.strip():
        raise ValidationError({'comment': 'Укажите причину отклонения.'})

    slot = RetakeSlot.objects.select_for_update().get(pk=obj.slot_id)
    old = obj.status

    # Составная операция: меняются заявка и количество занятых мест
    if action == 'submit':
        check_slot(slot, obj.owner, exclude_pk=obj.pk)
        slot.booked += 1
        slot.save(update_fields=['booked'])
        details = f'Занято мест: {slot.booked} из {slot.capacity}'
    elif target in (S.REJECTED, S.CANCELLED) and old == S.SUBMITTED:
        slot.booked -= 1
        slot.save(update_fields=['booked'])
        details = f'Место освобождено. Занято мест: {slot.booked} из {slot.capacity}'
    else:
        details = ''
    if comment:
        details = (details + '. ' if details else '') + f'Комментарий: {comment}'

    obj.status = target
    if comment:
        obj.comment = comment
    obj.save(update_fields=['status', 'comment', 'updated_at'])
    log(obj, EVENT_FOR_ACTION[action], user, old, target, details)
    return obj
