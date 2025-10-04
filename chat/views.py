# chat/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .models import ChatRoom, Message

@login_required
def chat_home(request):
    """شاشة الدردشة الرئيسية"""
    # إنشاء أو جلب غرفة الدردشة العامة
    room, created = ChatRoom.objects.get_or_create(name='general')
    
    # جلب آخر 50 رسالة
    messages = Message.objects.filter(room=room).order_by('-timestamp')[:50]
    
    context = {
        'room_name': 'general',
        'messages': reversed(messages),  # لعرض الرسائل من الأقدم إلى الأحدث
    }
    return render(request, 'chat/room.html', context)

@login_required
def get_messages(request, room_name):
    """جلب الرسائل الجديدة باستخدام AJAX Polling"""
    room = get_object_or_404(ChatRoom, name=room_name)
    last_id = request.GET.get('last_id', 0)
    
    try:
        last_id = int(last_id)
    except ValueError:
        last_id = 0
    
    # جلب الرسائل الجديدة
    new_messages = Message.objects.filter(
        room=room, 
        id__gt=last_id
    ).order_by('timestamp')
    
    messages_data = []
    for msg in new_messages:
        messages_data.append({
            'id': msg.id,
            'sender': msg.sender.email,
            'message': msg.content,
            'image_url': msg.image.url if msg.image else None,
            'timestamp': msg.timestamp.strftime("%H:%M")
        })
    
    return JsonResponse(messages_data, safe=False)

@csrf_exempt
@login_required
def send_message(request, room_name):
    """إرسال رسالة جديدة"""
    if request.method == 'POST':
        try:
            room = get_object_or_404(ChatRoom, name=room_name)
            data = json.loads(request.body)
            message_content = data.get('message', '').strip()
            
            if message_content:
                # حفظ الرسالة
                message = Message.objects.create(
                    room=room,
                    sender=request.user,
                    content=message_content
                )
                
                return JsonResponse({
                    'status': 'success', 
                    'message_id': message.id,
                    'sender': request.user.email,
                    'timestamp': message.timestamp.strftime("%H:%M")
                })
            else:
                return JsonResponse({'status': 'error', 'error': 'الرسالة فارغة'})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)})
    
    return JsonResponse({'status': 'error', 'error': 'Method not allowed'})

@csrf_exempt
@login_required
def send_image(request, room_name):
    """إرسال صورة"""
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            room = get_object_or_404(ChatRoom, name=room_name)
            image_file = request.FILES['image']
            
            # حفظ الرسالة مع الصورة
            message = Message.objects.create(
                room=room,
                sender=request.user,
                content='📷 صورة مرفوعة',
                image=image_file
            )
            
            return JsonResponse({
                'status': 'success', 
                'message_id': message.id,
                'sender': request.user.email,
                'image_url': message.image.url,
                'timestamp': message.timestamp.strftime("%H:%M")
            })
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)})
    
    return JsonResponse({'status': 'error', 'error': 'لم يتم اختيار صورة'})