# Развёртывание на Render

Приложение публикуется как **Web Service** (Python, Gunicorn) с отдельной базой **PostgreSQL**.
Секреты задаются только в разделе Environment сервиса и никогда не записываются в репозиторий,
README, скриншоты и отчёты.

## Подготовка репозитория

1. Убедитесь, что в репозитории есть `requirements.txt`, `build.sh`, `render.yaml`, `.python-version`
   и `.env.example`, а `.env`, `db.sqlite3`, `venv/` и `staticfiles/` исключены `.gitignore`.
2. Проверьте локально: `python manage.py check` и `python manage.py test` без ошибок.
3. Отправьте код на GitHub: `git push`.

## Вариант 1. Blueprint (render.yaml)

New → **Blueprint** → выбрать репозиторий → Apply. Render сам создаст базу `pz8-django-db`,
веб-сервис `pz8-django-app`, сгенерирует `DJANGO_SECRET_KEY` и подставит `DATABASE_URL` из базы.

## Вариант 2. Вручную

### 1. База данных

New → **PostgreSQL**: имя `pz8-django-db`, регион тот же, что будет у веб-сервиса, тариф Free.
Дождитесь статуса **Available**. На странице базы есть два адреса подключения:

- **Internal Database URL** — адрес внутри сети Render. Его используют сервисы Render в **том же
  регионе**: он быстрее и не выходит в интернет. Именно он записывается в `DATABASE_URL` веб-сервиса.
- **External Database URL** — для подключения с вашего компьютера (psql, PyCharm). Нужен только для
  ручной проверки данных.

Оба адреса содержат логин и пароль базы. Их значения **нельзя** публиковать в README, коде,
отчёте и на скриншотах — в документации указывается только имя переменной.

### 2. Web Service

New → **Web Service** → репозиторий GitHub. Настройки:

| Поле | Значение |
|------|----------|
| Runtime | Python 3 |
| Build Command | `bash build.sh` |
| Start Command | `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT` |
| Instance Type | Free |

### 3. Переменные окружения (Environment)

| Переменная | Значение |
|------------|----------|
| `DJANGO_SECRET_KEY` | кнопка **Generate** |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `<имя-сервиса>.onrender.com` (без `https://`) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://<имя-сервиса>.onrender.com` (с протоколом) |
| `DATABASE_URL` | Internal Database URL базы (вставить из страницы базы, значение скрыто) |
| `PYTHON_VERSION` | `3.13.5` (или файл `.python-version`) |

`DJANGO_HTTPS` на Render не задаётся: по умолчанию `True` включает перенаправление на HTTPS,
защищённые cookie и HSTS. Домен сервиса Django также берёт из `RENDER_EXTERNAL_HOSTNAME`, которую
Render задаёт сам.

## Этапы и где смотреть результат

| Этап | Команда | Где выполняется | Признак успеха в Logs |
|------|---------|-----------------|------------------------|
| Сборка | `pip install -r requirements.txt` | Build | `Successfully installed Django-6.1.2 ...` |
| Статика | `collectstatic --noinput` | Build (build.sh) | `176 static files copied ...` |
| Миграции | `migrate --noinput` | Build (build.sh), один раз на развёртывание | `Applying ... OK` или `No migrations to apply` |
| Данные | `init_demo` | Build (build.sh) | `Учебные данные загружены.` или `База уже заполнена` |
| Запуск | `gunicorn config.wsgi:application` | Start | `Listening at: http://0.0.0.0:10000`, статус **Live** |
| Проверка | открыть `https://<имя>.onrender.com/healthz/` | браузер | `{"status": "ok"}` |

После проверки `/healthz/` войдите на сайт, создайте обращение, выполните **Manual Deploy → Restart**
и убедитесь, что обращение сохранилось: данные лежат в PostgreSQL, а не на диске сервиса.

## Локальная и облачная база — разные базы

| | Локально | Render |
|---|----------|--------|
| СУБД | SQLite, файл `db.sqlite3` | PostgreSQL, сервис `pz8-django-db` |
| Откуда адрес | `DATABASE_URL` не задан | `DATABASE_URL` = Internal Database URL |
| Данные | свои; не попадают в Git | свои; заполняются `init_demo` при первой сборке |

Изменения моделей переносятся **миграциями** (они в репозитории), а не копированием базы. Записи,
созданные локально, на сервере не появятся.

## Обновление приложения

`git push` → Render автоматически пересобирает сервис (Auto-Deploy) → `build.sh` применяет новые
миграции → сервис перезапускается. При ошибке сборки продолжает работать предыдущая версия.

## Ограничения бесплатного тарифа

- веб-сервис засыпает после простоя, первый запрос после этого занимает до минуты;
- бесплатная база PostgreSQL ограничена по объёму и сроку действия — актуальные условия см. в
  документации Render.
