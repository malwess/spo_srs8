from rest_framework import serializers

from accounts.models import Course, Department


class DepartmentSerializer(serializers.ModelSerializer):
    courses_count = serializers.IntegerField(read_only=True)
    groups_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Department
        fields = ['id', 'name', 'courses_count', 'groups_count']
        extra_kwargs = {'name': {'error_messages': {
            'blank': 'Введите название факультета.',
            'required': 'Введите название факультета.',
        }}}

    def validate_name(self, value):
        value = value.strip()
        others = Department.objects.exclude(pk=getattr(self.instance, 'pk', None))
        # сравнение в Python: SQLite не умеет iexact для русских букв
        if any(d.name.casefold() == value.casefold() for d in others):
            raise serializers.ValidationError('Факультет с таким названием уже есть.')
        return value


class CourseSerializer(serializers.ModelSerializer):
    # связанные данные: название факультета и показатели, посчитанные в запросе
    department_name = serializers.CharField(source='department.name', read_only=True)
    students_count = serializers.IntegerField(read_only=True)
    grades_count = serializers.IntegerField(read_only=True)
    avg_grade = serializers.FloatField(read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'department', 'department_name',
                  'students_count', 'grades_count', 'avg_grade']
        extra_kwargs = {
            'title': {'error_messages': {'blank': 'Введите название курса.',
                                         'required': 'Введите название курса.',
                                         'max_length': 'Название не длиннее 200 символов.'}},
            'department': {'error_messages': {'required': 'Выберите факультет.',
                                              'null': 'Выберите факультет.',
                                              'does_not_exist': 'Такого факультета нет в базе.',
                                              'incorrect_type': 'Выберите факультет из списка.'}},
        }

    def validate_title(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError('Название курса должно быть не короче 3 символов.')
        return value

    def validate(self, attrs):
        title = attrs.get('title', getattr(self.instance, 'title', None))
        department = attrs.get('department', getattr(self.instance, 'department', None))
        others = Course.objects.filter(department=department).exclude(pk=getattr(self.instance, 'pk', None))
        if title and any(c.title.casefold() == title.casefold() for c in others):
            raise serializers.ValidationError({'title': 'Курс с таким названием уже есть на этом факультете.'})
        return attrs
