@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Локальный запуск в режиме разработки (подробно — README.md, раздел «Быстрый старт»).
if not exist .env (
    copy .env.example .env >nul
    echo Создан файл .env из .env.example
)
if not exist venv (
    python -m venv venv || py -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt
python manage.py check || goto :error
python manage.py migrate
python manage.py init_demo
python manage.py collectstatic --noinput
start http://127.0.0.1:8000/
python manage.py runserver
pause
exit /b
:error
echo Проверка не пройдена - см. docs\troubleshooting.md
pause
