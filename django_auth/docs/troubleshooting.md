# Типичные ошибки и диагностика

Сообщения ниже воспроизведены на этом проекте. Порядок диагностики: прочитать **последнюю строку**
ошибки в терминале (или в Logs на Render) → найти её здесь → исправить → повторить команду.
Полезные команды: `python manage.py check`, `python manage.py check --deploy`,
`python manage.py showmigrations`, `pip list`.

## 1. ImproperlyConfigured: Set DJANGO_SECRET_KEY

**Когда:** первая команда `manage.py` после клонирования репозитория.
**Причина:** нет файла `.env` (он не хранится в Git) или на Render не задана переменная.
**Исправление:** `copy .env.example .env` (Linux/macOS: `cp .env.example .env`);
на Render — Environment → `DJANGO_SECRET_KEY` → Generate.

## 2. Не удаётся войти: «Пожалуйста, введите правильные имя пользователя и пароль»

**Когда:** новая база после `migrate`.
**Причина:** миграции создают пустые таблицы, пользователей в базе нет.
**Проверка:** `python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.count())"` → `0`.
**Исправление:** `python manage.py init_demo` (или `createsuperuser` для своего администратора).

## 3. OperationalError: no such table: ...

**Причина:** не выполнены миграции, или `DATABASE_URL` указывает на другую (пустую) базу.
**Исправление:** `python manage.py migrate`; проверить `showmigrations` — у всех строк должно быть `[X]`.

## 4. 500 Server Error при DJANGO_DEBUG=False, в журнале «Missing staticfiles manifest entry»

**Причина:** при `DEBUG=False` статику отдаёт WhiteNoise по манифесту, который создаётся только
командой `collectstatic`.
**Исправление:** `python manage.py collectstatic --noinput` (на Render это делает `build.sh`).

## 5. 400 Bad Request, в журнале «Invalid HTTP_HOST header ... add '...' to ALLOWED_HOSTS»

**Причина:** сайт открыт по адресу, которого нет в `DJANGO_ALLOWED_HOSTS` (IP в локальной сети,
другой домен Render).
**Исправление:** добавить домен **без протокола и порта** в `DJANGO_ALLOWED_HOSTS` через запятую
и перезапустить сервер.

## 6. OperationalError: failed to resolve host 'dpg-...'

**Причина:** в `DATABASE_URL` на своём компьютере подставлен **Internal Database URL** — он работает
только внутри сети Render.
**Исправление:** локально удалить `DATABASE_URL` из `.env` (будет SQLite); для ручного подключения
к облачной базе использовать External Database URL и не сохранять его в файлах проекта.

## 7. Error: That port is already in use.

**Причина:** на порту 8000 уже запущен другой сервер (например, второе окно `runserver`).
**Исправление:** закрыть старый сервер (Ctrl+C) или запустить на другом порту:
`python manage.py runserver 8001`.

## 8. ModuleNotFoundError: No module named 'django' (или 'rest_framework', 'dj_database_url')

**Причина:** не активировано виртуальное окружение или не установлены зависимости.
**Исправление:** `venv\Scripts\activate`, затем `pip install -r requirements.txt`.
В начале строки терминала должно быть `(venv)`.

## 9. 403 в API: «Учетные данные не были предоставлены» или «CSRF Failed»

**Причина:** запрос без входа на сайт; для POST/PUT/PATCH/DELETE — нет заголовка `X-CSRFToken`.
**Исправление:** войти на `/accounts/login/`; в своих запросах `fetch()` передавать
`X-CSRFToken` из cookie `csrftoken` (пример — в `docs/api.md`).

## 10. Render: Build failed / сервис не становится Live

**Порядок диагностики:** открыть Logs и найти первую строку с `ERROR` или `Traceback`.

- `No matching distribution found` — опечатка или несовместимая версия в `requirements.txt`;
- ошибки 1, 4 или 6 из этого списка — проверить Environment;
- `Exited with status 127` / `bash: build.sh: No such file` — файл `build.sh` не отправлен в репозиторий;
- сервис Live, но страница 400 — пункт 5.
