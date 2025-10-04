import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing
import calls.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_clone.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns +
            calls.routing.websocket_urlpatterns
        )
    ),
})