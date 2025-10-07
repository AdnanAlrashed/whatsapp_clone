from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_home, name='home'),
    path('room/<str:room_id>/', views.room_detail, name='room_detail'),
    path('create-room/', views.create_room, name='create_room'),
    path('manage-room/<str:room_id>/', views.manage_room, name='manage_room'),
    path('messages/<str:room_id>/', views.get_messages, name='get_messages'),
    path('send/<str:room_id>/', views.send_message, name='send_message'),
    path('send-image/<str:room_id>/', views.send_image, name='send_image'),
    path('search-rooms/', views.search_rooms, name='search_rooms'),
    path('profile/', views.user_profile, name='user_profile'),
    path('create-test-rooms/', views.create_test_rooms, name='create_test_rooms'),  # إضافة هذا
    path('old/', views.chat_home, name='room_old'),
    path('invite/<str:room_id>/', views.invite_user, name='invite_user'),
    path('invitations/accept/<str:token>/', views.accept_invitation, name='accept_invitation'),
    path('invitations/decline/<str:token>/', views.decline_invitation, name='decline_invitation'),
    path('invitations/my/', views.my_invitations, name='my_invitations'),
    path('online-status/<str:room_id>/', views.update_online_status, name='update_online_status'),
]