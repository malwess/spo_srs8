"""Заполнение пустой базы учебными данными (используется при развёртывании).

Если в базе уже есть пользователи, команда ничего не делает — поэтому повторная
сборка на Render не затирает записи, созданные на сайте.
"""
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Загружает учебные данные в пустую базу данных'

    def handle(self, *args, **options):
        if User.objects.exists():
            self.stdout.write('База уже заполнена — учебные данные не загружаются.')
            return
        call_command('loaddata', 'demo_data', verbosity=1)
        self.stdout.write(self.style.SUCCESS('Учебные данные загружены.'))
