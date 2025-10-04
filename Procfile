web: daphne -b 0.0.0.0 -p $PORT whatsapp_clone.asgi:application
web: DJANGO_SETTINGS_MODULE=whatsapp_clone.settings daphne -b 0.0.0.0 -p $PORT whatsapp_clone.asgi:application
worker: python manage.py runworker --settings=whatsapp_clone.settings
release: python manage.py migrate --settings=whatsapp_clone.settings
DJANGO_SETTINGS_MODULE=whatsapp_clone.settings

