from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_home, name='room'),
    # path('start/', views.start_chat, name='start'),
    # path('join/<str:room_name>/', views.join_chat, name='join'),
    # أضف مسارات أخرى حسب الحاجة
]
    # أضف مسارات أخرى حسب الحاجة