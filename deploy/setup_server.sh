#!/bin/bash
# Скрипт первоначальной настройки сервера

set -e

PROJECT_DIR="/home/vitaly/CRM_Hospital"
SERVICE_NAME="crm-hospital"
RUN_DIR="/run/crm-hospital"
LOG_DIR="$PROJECT_DIR/logs"

echo "🔧 Настройка сервера..."

# Создание директорий
echo "📁 Создание директорий..."
sudo mkdir -p $RUN_DIR
sudo mkdir -p $LOG_DIR
sudo mkdir -p $PROJECT_DIR/staticfiles
sudo chown -R $USER:$USER $RUN_DIR
sudo chown -R $USER:$USER $LOG_DIR

# Копирование конфигов
echo "📋 Копирование конфигурационных файлов..."
sudo cp $PROJECT_DIR/deploy/crm-hospital.service /etc/systemd/system/
sudo cp $PROJECT_DIR/deploy/crm-hospital.nginx /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/crm-hospital.nginx /etc/nginx/sites-enabled/

# Перезапуск nginx
echo "🔄 Перезапуск Nginx..."
sudo nginx -t && sudo systemctl restart nginx

# Reload systemd
echo "🔄 Обновление systemd..."
sudo systemctl daemon-reload

# Включение сервиса
echo "▶️ Включение сервиса..."
sudo systemctl enable $SERVICE_NAME

echo "✅ Настройка завершена!"
echo ""
echo "Далее:"
echo "1. cp .env.example .env"
echo "2. bash deploy/deploy.sh"
