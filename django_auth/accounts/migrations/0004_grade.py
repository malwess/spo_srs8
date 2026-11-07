import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_academicgroup_studentprofile_academic_group"),
    ]

    operations = [
        migrations.CreateModel(
            name="Grade",
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
                    "kind",
                    models.CharField(
                        choices=[
                            ("pz", "Практическое занятие"),
                            ("srs", "Самостоятельная работа"),
                            ("lr", "Лабораторная работа"),
                            ("test", "Контрольная работа"),
                        ],
                        default="pz",
                        max_length=5,
                        verbose_name="Вид работы",
                    ),
                ),
                (
                    "value",
                    models.PositiveSmallIntegerField(
                        choices=[(2, "2"), (3, "3"), (4, "4"), (5, "5")],
                        verbose_name="Оценка",
                    ),
                ),
                ("date", models.DateField(verbose_name="Дата")),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="grades",
                        to="accounts.course",
                        verbose_name="Курс",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="grades",
                        to="accounts.studentprofile",
                        verbose_name="Студент",
                    ),
                ),
            ],
            options={
                "verbose_name": "Оценка",
                "verbose_name_plural": "Оценки",
                "ordering": ["-date"],
            },
        ),
    ]
