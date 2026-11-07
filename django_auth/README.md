# Учебный портал кафедры (django_auth)

Веб-приложение на Django для учебного офиса кафедры: справочники факультетов, групп и курсов,
дашборды успеваемости, обращения студентов и запись на пересдачу. Интерфейс построен на Tabler,
данные страниц загружаются через REST API без перезагрузки.

Проект выполнен в рамках дисциплины «Структура программного обеспечения и базы данных»
(ПЗ № 4–8, СРС № 4–8). Автор: Ерина С. В., группа М3О-236БВ-25.

## Возможности

- вход и выход пользователей, роли «Студент», «Методист» и администратор;
- справочники факультетов, учебных групп и курсов (CRUD для методиста);
- дашборды успеваемости с графиками ApexCharts и фильтрами;
- «Менеджер данных» — CRUD курсов и факультетов через REST API с серверным поиском и фильтрами;
- «Мои обращения» — обращения студента с переходами статусов «Новое → На рассмотрении → Выполнено»;
- «Пересдачи» — бизнес-процесс записи на пересдачу: ограниченные места, согласование методистом,
  транзакции и история событий;
- адрес проверки доступности `/healthz/`.

## Технологический стек

| Слой | Технологии |
|------|-----------|
| Сервер | Python 3.13, Django 6.1, Django REST Framework 3.18 |
| Интерфейс | шаблоны Django, Tabler 1.7 (лежит в `static/vendor`), ApexCharts, fetch() |
| База данных | SQLite (локально), PostgreSQL 16 (Render) |
| Запуск на сервере | Gunicorn, WhiteNoise, dj-database-url, psycopg 3 |

## Требования

- Python 3.13 (подойдёт 3.12+), pip;
- Git — чтобы получить код из репозитория (или распакуйте архив проекта);
- свободный порт 8000;
- для облака — аккаунты GitHub и Render.

## Быстрый старт (Windows)

Все команды выполняются в терминале из папки проекта.

```bat
git clone <адрес репозитория> django_auth
cd django_auth
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py check
python manage.py migrate
python manage.py init_demo
python manage.py runserver
```

Откройте http://127.0.0.1:8000/ — откроется страница входа. Учебные логины перечислены в файле
`ЛОГИНЫ.txt`, который выдаётся вместе с архивом проекта (пароли в README не публикуются).

Для Linux и macOS отличаются только две команды: `source venv/bin/activate` и `cp .env.example .env`.

То же самое одной командой делает `run_windows.bat`: создаёт `.env`, виртуальное окружение,
ставит зависимости, применяет миграции, загружает учебные данные и запускает сервер.

### Что делает каждый шаг

| Шаг | Зачем нужен |
|-----|-------------|
| `copy .env.example .env` | без `DJANGO_SECRET_KEY` Django не запускается (`ImproperlyConfigured`) |
| `migrate` | создаёт таблицы в новой базе `db.sqlite3` |
| `init_demo` | загружает пользователей, курсы, оценки, обращения и пересдачи; в заполненную базу ничего не добавляет |
| `collectstatic --noinput` | нужен только при `DJANGO_DEBUG=False` (запуск через Gunicorn, Render) |

### Проверка запуска

- http://127.0.0.1:8000/healthz/ → `{"status": "ok"}`;
- http://127.0.0.1:8000/api/courses/ без входа → 403 «Учетные данные не были предоставлены»;
- после входа: пункты меню «Мои обращения», «Пересдачи», «Менеджер данных», «Дашборды».

### Запуск в режиме, близком к серверу

```bash
python manage.py collectstatic --noinput
DJANGO_DEBUG=False DJANGO_HTTPS=False gunicorn config.wsgi:application --bind 127.0.0.1:8000
```

Gunicorn работает только в Linux и macOS; в Windows используйте `runserver`.

### Автоматические тесты

```bash
python manage.py test
```

## Переменные окружения

Все настройки, которые отличаются между компьютером и сервером, задаются переменными окружения.
Локально они читаются из файла `.env` (его создают копированием `.env.example`), на Render — из
раздела Environment. Файл `.env` в репозиторий не попадает.

| Переменная | Локально | Render |
|------------|----------|--------|
| `DJANGO_SECRET_KEY` | любая длинная строка | Generate (случайное значение) |
| `DJANGO_DEBUG` | `True` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | `<имя-сервиса>.onrender.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `http://127.0.0.1:8000` | `https://<имя-сервиса>.onrender.com` |
| `DJANGO_HTTPS` | `False` | не задавать (по умолчанию `True`) |
| `DATABASE_URL` | не задавать — SQLite | Internal Database URL базы PostgreSQL |

## Документация

- [docs/architecture.md](docs/architecture.md) — структура проекта и схема архитектуры;
- [docs/database.md](docs/database.md) — модели и связи базы данных;
- [docs/api.md](docs/api.md) — маршруты страниц и REST API с примерами;
- [docs/deployment.md](docs/deployment.md) — развёртывание на Render;
- [docs/troubleshooting.md](docs/troubleshooting.md) — типичные ошибки и диагностика.
