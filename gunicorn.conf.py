# Gunicorn конфиг для CRM Hospital
import multiprocessing

# Сервер
bind = "0.0.0.0:8000"
backlog = 2048

# Workers
workers = 2
worker_class = "sync"
timeout = 30
keepalive = 2

# Логи
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Окружение
raw_env = [
    "DJANGO_SETTINGS_MODULE=medcrm.settings_production",
]
