import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0004_grade"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RetakeRequest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("reason", models.TextField(verbose_name="Причина пересдачи")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Черновик"),
                            ("submitted", "Подана"),
                            ("approved", "Одобрена"),
                            ("rejected", "Отклонена"),
                            ("cancelled", "Отменена"),
                        ],
                        default="draft",
                        max_length=10,
                        verbose_name="Статус",
                    ),
                ),
                (
                    "comment",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Комментарий методиста"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Создана"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Изменена"),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="retake_requests",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Студент",
                    ),
                ),
            ],
            options={
                "verbose_name": "Заявка на пересдачу",
                "verbose_name_plural": "Заявки на пересдачу",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="RetakeEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("created", "Создана"),
                            ("updated", "Изменена"),
                            ("submitted", "Подана, место забронировано"),
                            ("approved", "Одобрена"),
                            ("rejected", "Отклонена, место освобождено"),
                            ("cancelled", "Отменена"),
                        ],
                        max_length=10,
                        verbose_name="Событие",
                    ),
                ),
                (
                    "old_status",
                    models.CharField(blank=True, max_length=10, verbose_name="Было"),
                ),
                (
                    "new_status",
                    models.CharField(blank=True, max_length=10, verbose_name="Стало"),
                ),
                (
                    "details",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Подробности"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Время"),
                ),
                (
                    "actor",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="retake_events",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Инициатор",
                    ),
                ),
                (
                    "request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="retakes.retakerequest",
                        verbose_name="Заявка",
                    ),
                ),
            ],
            options={
                "verbose_name": "Событие заявки",
                "verbose_name_plural": "История заявок",
                "ordering": ["created_at", "id"],
            },
        ),
        migrations.CreateModel(
            name="RetakeSlot",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("starts_at", models.DateTimeField(verbose_name="Дата и время")),
                ("room", models.CharField(max_length=50, verbose_name="Аудитория")),
                (
                    "capacity",
                    models.PositiveSmallIntegerField(verbose_name="Мест всего"),
                ),
                (
                    "booked",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="Мест занято"
                    ),
                ),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="retake_slots",
                        to="accounts.course",
                        verbose_name="Курс",
                    ),
                ),
            ],
            options={
                "verbose_name": "Время пересдачи",
                "verbose_name_plural": "Время пересдач",
                "ordering": ["starts_at"],
            },
        ),
        migrations.AddField(
            model_name="retakerequest",
            name="slot",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="requests",
                to="retakes.retakeslot",
                verbose_name="Пересдача",
            ),
        ),
        migrations.AddConstraint(
            model_name="retakeslot",
            constraint=models.CheckConstraint(
                condition=models.Q(("booked__lte", models.F("capacity"))),
                name="slot_booked_lte_capacity",
            ),
        ),
    ]
