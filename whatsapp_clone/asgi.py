import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_clone.settings')
django.setup()
import chat.routing  # 👈 بعد تهيئة Django
# import calls.routing  # 👈 بعد تهيئة Django

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
            # calls.routing.websocket_urlpatterns
        )
    ),
})