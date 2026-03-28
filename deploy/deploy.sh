#!/bin/bash
# Скрипт деплоя CRM Hospital

set -e

PROJECT_DIR="/home/vitaly/CRM_Hospital"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="crm-hospital"

echo "🚀 Начало деплоя..."

# Переход в директорию проекта
cd "$PROJECT_DIR"

# Активация venv
echo "📦 Активация виртуального окружения..."
source "$VENV_DIR/bin/activate"

# Обновление зависимостей
echo "📦 Установка зависимостей..."
pip install -r requirements.txt
pip install gunicorn python-decouple

# Сбор статических файлов
echo "📁 Сбор статических файлов..."
python manage.py collectstatic --noinput

# Миграции БД
echo "🗄️ Применение миграций..."
python manage.py migrate

# Перезапуск сервиса
echo "🔄 Перезапуск сервиса..."
sudo systemctl restart $SERVICE_NAME

# Проверка статуса
echo "✅ Проверка статуса..."
sudo systemctl status $SERVICE_NAME --no-pager

echo "🎉 Деплой завершён!"
