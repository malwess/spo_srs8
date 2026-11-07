#!/usr/bin/env bash
# Сценарий сборки на Render (Build Command: bash build.sh)
set -e

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Сбор статических файлов Tabler и проекта в staticfiles/ для WhiteNoise
python manage.py collectstatic --noinput

# Миграции в PostgreSQL. Сборка выполняется один раз на каждое развёртывание,
# поэтому миграции не запускаются параллельно несколькими процессами Gunicorn.
python manage.py migrate --noinput

# Учебные данные (пользователи, факультеты, курсы, обращения) — только в пустую БД
python manage.py init_demo
