from rest_framework import serializers

from .models import RetakeEvent, RetakeRequest, RetakeSlot
from .services import ACTION_LABELS, allowed_actions, check_slot


class RetakeSlotSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    free = serializers.IntegerField(read_only=True)

    class Meta:
        model = RetakeSlot
        fields = ('id', 'course', 'course_title', 'starts_at', 'room', 'capacity', 'booked', 'free')


class RetakeEventSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = RetakeEvent
        fields = ('id', 'action', 'action_display', 'actor_name', 'old_status', 'new_status', 'details', 'created_at')

    def get_actor_name(self, obj):
        return obj.actor.username if obj.actor else '—'


class RetakeRequestSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    slot_info = RetakeSlotSerializer(source='slot', read_only=True)
    actions = serializers.SerializerMethodField()

    class Meta:
        model = RetakeRequest
        fields = ('id', 'owner_name', 'slot', 'slot_info', 'reason', 'status', 'status_display', 'comment',
                  'actions', 'created_at', 'updated_at')
        read_only_fields = ('status', 'comment')
        extra_kwargs = {
            'reason': {'error_messages': {'blank': 'Укажите причину пересдачи.', 'required': 'Укажите причину пересдачи.'}},
            'slot': {'error_messages': {'required': 'Выберите время пересдачи.', 'null': 'Выберите время пересдачи.',
                                        'does_not_exist': 'Такой пересдачи нет в базе.'}},
        }

    def get_actions(self, obj):
        user = self.context['request'].user
        return [{'name': a, 'label': ACTION_LABELS[a]} for a in allowed_actions(obj, user)]

    def validate_reason(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError('Опишите причину подробнее — не менее 10 символов.')
        return value.strip()

    def validate(self, attrs):
        # Правило 5: менять содержимое можно только у черновика
        if self.instance and self.instance.status != RetakeRequest.Status.DRAFT:
            raise serializers.ValidationError(
                {'status': f'Заявку в статусе «{self.instance.get_status_display()}» изменять нельзя — '
                           'редактируется только черновик.'})
        slot = attrs.get('slot')
        if slot:
            owner = self.instance.owner if self.instance else self.context['request'].user
            check_slot(slot, owner, exclude_pk=getattr(self.instance, 'pk', None))
        return attrs
