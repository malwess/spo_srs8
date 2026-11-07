from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import RetakeEvent, RetakeRequest, RetakeSlot
from .serializers import RetakeEventSerializer, RetakeRequestSerializer, RetakeSlotSerializer
from .services import can_manage, log, perform


@login_required
@ensure_csrf_cookie
def page(request):
    """Страница «Пересдачи». Все данные она получает и меняет через REST API."""
    return render(request, 'retakes/index.html', {'can_manage': can_manage(request.user)})


class RetakeSlotViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/retake-slots/?course=<id>&upcoming=1 — время пересдач и свободные места."""

    serializer_class = RetakeSlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = RetakeSlot.objects.select_related('course')
        course = self.request.query_params.get('course')
        if course:
            qs = qs.filter(course_id=course)
        if self.request.query_params.get('upcoming'):
            qs = qs.filter(starts_at__gt=timezone.now())
        return qs


class RetakeRequestViewSet(viewsets.ModelViewSet):
    """CRUD заявок и действия бизнес-процесса.

    Фильтры: ?status=submitted&course=<id>&mine=1
    Действия: POST /api/retakes/<id>/submit|approve|reject|cancel/
    История:  GET  /api/retakes/<id>/history/
    """

    serializer_class = RetakeRequestSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'put', 'delete']

    def get_queryset(self):
        user = self.request.user
        qs = RetakeRequest.objects.select_related('owner', 'slot__course')
        # студент видит только свои заявки; методист (роль) — заявки всех студентов
        if not can_manage(user) or self.request.query_params.get('mine'):
            qs = qs.filter(owner=user)
        params = self.request.query_params
        if params.get('status'):
            qs = qs.filter(status=params['status'])
        if params.get('course'):
            qs = qs.filter(slot__course_id=params['course'])
        return qs

    def check_owner(self, obj):
        if obj.owner_id != self.request.user.id:
            raise PermissionDenied('Изменять и удалять заявку может только её автор.')

    def update(self, request, *args, **kwargs):
        if 'status' in request.data:
            raise ValidationError({'status': 'Статус нельзя изменить через PATCH/PUT — используйте действия '
                                             'submit, approve, reject или cancel.'})
        self.check_owner(self.get_object())
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        obj = serializer.save(owner=self.request.user)
        log(obj, RetakeEvent.Action.CREATED, self.request.user, '', obj.status, f'Пересдача: {obj.slot}')

    def perform_update(self, serializer):
        obj = serializer.save()
        log(obj, RetakeEvent.Action.UPDATED, self.request.user, obj.status, obj.status,
            f'Пересдача: {obj.slot}')

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        self.check_owner(obj)
        # Правило 5: удалить можно только черновик или отменённую заявку
        if obj.status not in (RetakeRequest.Status.DRAFT, RetakeRequest.Status.CANCELLED):
            raise ValidationError({'status': f'Заявку в статусе «{obj.get_status_display()}» удалить нельзя. '
                                             'Сначала отмените её.'})
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def run(self, request, name):
        obj = perform(self.get_object(), name, request.user, request.data.get('comment', ''))
        return Response(self.get_serializer(obj).data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        return self.run(request, 'submit')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        return self.run(request, 'approve')

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        return self.run(request, 'reject')

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        return self.run(request, 'cancel')

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        events = self.get_object().events.select_related('actor')
        return Response(RetakeEventSerializer(events, many=True).data)
