# chat/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def chat_home(request):
    """شاشة الدردشة الرئيسية"""
    context = {
        'room_name': 'general',  # أو يمكنك جعلها ديناميكية
    }
    return render(request, 'chat/room.html', context)