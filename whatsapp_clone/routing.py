from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
import chat.routing
import calls.routing

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path('ws/chat/<str:room_name>/', chat.routing.websocket_urlpatterns),
            path('ws/call/', calls.routing.websocket_urlpatterns),
        ])
    ),
})