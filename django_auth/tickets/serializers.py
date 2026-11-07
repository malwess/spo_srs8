from rest_framework import serializers

from .models import Category, Ticket

# Бизнес-правило: обращение проходит этапы строго по порядку
NEXT_STATUS = {
    Ticket.Status.NEW: {Ticket.Status.PROGRESS},
    Ticket.Status.PROGRESS: {Ticket.Status.DONE},
    Ticket.Status.DONE: set(),
}


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class TicketSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    next_statuses = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ('id', 'title', 'description', 'category', 'category_name', 'course', 'course_title',
                  'status', 'status_display', 'next_statuses', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'title': {'error_messages': {'blank': 'Введите тему обращения.', 'required': 'Введите тему обращения.'}},
            'category': {'error_messages': {'required': 'Выберите категорию.', 'null': 'Выберите категорию.',
                                            'does_not_exist': 'Такой категории нет в базе.'}},
            'course': {'error_messages': {'does_not_exist': 'Такого курса нет в базе.'}},
        }

    def get_next_statuses(self, obj):
        """Статусы, в которые можно перевести обращение (интерфейс показывает только их)."""
        return [{'value': s, 'label': Ticket.Status(s).label} for s in NEXT_STATUS[obj.status]]

    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError('Тема должна содержать не менее 5 символов.')
        return value.strip()

    def validate(self, attrs):
        # Новое обращение создаётся только со статусом «Новое»
        if self.instance is None:
            if attrs.get('status', Ticket.Status.NEW) != Ticket.Status.NEW:
                raise serializers.ValidationError({'status': 'Новое обращение должно иметь статус «Новое».'})
            return attrs

        old = self.instance.status
        new = attrs.get('status', old)
        if old == Ticket.Status.DONE:
            raise serializers.ValidationError({'status': 'Выполненное обращение нельзя изменить.'})
        if new != old and new not in NEXT_STATUS[old]:
            raise serializers.ValidationError({'status': (
                f'Недопустимый переход статуса: «{Ticket.Status(old).label}» → «{Ticket.Status(new).label}». '
                'Обращение проходит этапы по порядку: Новое → На рассмотрении → Выполнено.')})
        return attrs
