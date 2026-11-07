from django.db import migrations

CATEGORIES = ['Пересдача', 'Перенос срока сдачи работы', 'Справка из учебного офиса', 'Вопрос по курсу']


def add_categories(apps, schema_editor):
    Category = apps.get_model('tickets', 'Category')
    for name in CATEGORIES:
        Category.objects.get_or_create(name=name)


def remove_categories(apps, schema_editor):
    apps.get_model('tickets', 'Category').objects.filter(name__in=CATEGORIES).delete()


class Migration(migrations.Migration):
    """Заполняет справочник категорий обращений."""

    dependencies = [('tickets', '0001_initial')]

    operations = [migrations.RunPython(add_categories, remove_categories)]
