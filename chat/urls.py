from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_home, name='room'),
    path('messages/<str:room_name>/', views.get_messages, name='get_messages'),
    path('send/<str:room_name>/', views.send_message, name='send_message'),
    path('send-image/<str:room_name>/', views.send_image, name='send_image'),
]