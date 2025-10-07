# chat/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib import messages
import json
from .models import ChatRoom, Message, UserProfile, RoomInvitation, OnlineUser
from accounts.models import CustomUser
import uuid
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

@login_required
def chat_home(request):
    """الصفحة الرئيسية للدردشة مع قائمة الغرف"""
    try:
        # حساب الدعوات غير المقروءة
        unread_invitations_count = RoomInvitation.objects.filter(
            invited_user=request.user,
            is_accepted=False,
            is_declined=False,
            expires_at__gt=timezone.now()
        ).count()
        
        # إنشاء غرفة عامة افتراضية إذا لم تكن موجودة
        general_room, created = ChatRoom.objects.get_or_create(
            name='عام',
            room_type='public',
            defaults={
                'created_by': request.user, 
                'description': 'الغرفة العامة للدردشة'
            }
        )
        
        
        # جلب الغرف المتاحة للمستخدم
        available_rooms = ChatRoom.objects.filter(
            Q(room_type='public') | 
            Q(participants=request.user) |
            Q(created_by=request.user)
        ).distinct().filter(is_active=True)
        
        # غرف المستخدم الخاصة (التي أنشأها)
        user_rooms = request.user.created_rooms.all()
        
        # تحضير بيانات الغرف مع الإحصائيات - بشكل آمن
        rooms_data = []
        for room in available_rooms:
            try:
                room_data = {
                    'id': str(room.id),
                    'name': room.name,
                    'description': room.description or 'لا يوجد وصف',
                    'type': room.room_type,
                    'created_by': room.created_by.email,
                    'is_owner': room.created_by == request.user,
                    'online_count': room.get_online_count(),
                    'message_count': room.message_set.count(),
                    'can_join': room.can_join(request.user)
                }
                rooms_data.append(room_data)
            except Exception as e:
                print(f"Error processing room {room.id}: {e}")
                # استمرار مع الغرف الأخرى حتى في حالة الخطأ
        
        # بيانات غرف المستخدم
        user_rooms_data = []
        for room in user_rooms:
            try:
                room_data = {
                    'id': str(room.id),
                    'name': room.name,
                    'description': room.description or 'لا يوجد وصف',
                    'type': room.room_type,
                    'created_by': room.created_by.email,
                    'is_owner': True,
                    'online_count': room.get_online_count(),
                    'message_count': room.message_set.count(),
                    'can_join': True
                }
                user_rooms_data.append(room_data)
            except Exception as e:
                print(f"Error processing user room {room.id}: {e}")
        
        # الغرف العامة فقط
        public_rooms_data = [room for room in rooms_data if room['type'] == 'public']
        
        context = {
            'available_rooms': available_rooms,
            'user_rooms': user_rooms,
            'rooms_data_json': json.dumps(rooms_data, ensure_ascii=False),
            'user_rooms_data_json': json.dumps(user_rooms_data, ensure_ascii=False),
            'public_rooms_data_json': json.dumps(public_rooms_data, ensure_ascii=False),
            'current_room': general_room,
            'unread_invitations_count': unread_invitations_count,  # إضافة هذا
        }
        return render(request, 'chat/home.html', context)
        
    except Exception as e:
        print(f"Error in chat_home: {e}")
        messages.error(request, 'حدث خطأ في تحميل الغرف')
        return render(request, 'chat/home.html', {
            'rooms_data_json': '[]',
            'user_rooms_data_json': '[]',
            'public_rooms_data_json': '[]',
            'available_rooms': [],
            'user_rooms': [],
            'unread_invitations_count': 0
        })

# تحديث دالة room_detail أيضاً
@login_required
def room_detail(request, room_id):
    """تفاصيل غرفة دردشة محددة"""
    try:
        # محاولة تحويل room_id إلى UUID أولاً
        try:
            room_uuid = uuid.UUID(room_id)
            room = get_object_or_404(ChatRoom, id=room_uuid)
        except ValueError:
            room = get_object_or_404(ChatRoom, name=room_id)
        
        # التحقق من صلاحية الدخول
        if not room.can_join(request.user):
            messages.error(request, 'ليس لديك صلاحية للدخول إلى هذه الغرفة')
            return redirect('chat:home')
        
        # إضافة المستخدم إلى قائمة المتصلين
        room.add_online_user(request.user)
        
        # جلب آخر 100 رسالة
        messages_list = Message.objects.filter(
            room=room
        ).exclude(
            deleted_for=request.user
        ).select_related('sender', 'reply_to').order_by('-timestamp')[:100]
        
        # معلومات المستخدمين المتصلين
        online_users = room.online_users.filter(
            onlineuser__is_online=True
        ).distinct()
        
        # عدد المتصلين الحقيقي
        online_count = room.get_online_count()
        
        context = {
            'room': room,
            'room_id': str(room.id),
            'messages': reversed(messages_list),
            'online_users': online_users,
            'online_count': online_count,  # إضافة هذا
            'is_room_admin': room.admins.filter(id=request.user.id).exists() or room.created_by == request.user,
        }
        return render(request, 'chat/room.html', context)
        
    except Exception as e:
        print(f"Error in room_detail: {e}")
        messages.error(request, 'حدث خطأ في تحميل الغرفة')
        return redirect('chat:home')
    
# إضافة دالة لتحديث حالة الاتصال
@login_required
@csrf_exempt
def update_online_status(request, room_id):
    """تحديث حالة الاتصال للمستخدم"""
    if request.method == 'POST':
        try:
            room = get_object_or_404(ChatRoom, id=room_id)
            action = request.POST.get('action', 'ping')
            
            if action == 'join':
                room.add_online_user(request.user)
            elif action == 'leave':
                room.remove_online_user(request.user)
            elif action == 'ping':
                # تحديث last_seen فقط
                OnlineUser.objects.filter(
                    user=request.user,
                    room=room
                ).update(last_seen=timezone.now())
            
            return JsonResponse({
                'status': 'success',
                'online_count': room.get_online_count()
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'error': str(e)
            })
    
    return JsonResponse({'status': 'error', 'error': 'Method not allowed'})

@login_required
def create_room(request):
    """إنشاء غرفة دردشة جديدة"""
    if request.method == 'POST':
        room_name = request.POST.get('room_name')
        room_type = request.POST.get('room_type', 'public')
        description = request.POST.get('description', '')
        
        if room_name:
            room = ChatRoom.objects.create(
                name=room_name,
                room_type=room_type,
                description=description,
                created_by=request.user
            )
            
            # إضافة المنشئ كمشرف ومشارك
            room.admins.add(request.user)
            room.participants.add(request.user)
            
            messages.success(request, f'تم إنشاء الغرفة "{room_name}" بنجاح')
            return redirect('chat:room_detail', room_id=room.id)
    
    return render(request, 'chat/create_room.html')

@login_required
def manage_room(request, room_id):
    """إدارة غرفة الدردشة"""
    try:
        room_uuid = uuid.UUID(room_id)
        room = get_object_or_404(ChatRoom, id=room_uuid)
    except ValueError:
        room = get_object_or_404(ChatRoom, name=room_id)
    
    # التحقق من الصلاحيات
    if not room.admins.filter(id=request.user.id).exists() and room.created_by != request.user:
        messages.error(request, 'ليس لديك صلاحية لإدارة هذه الغرفة')
        return redirect('chat:room_detail', room_id=room_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_room':
            room.name = request.POST.get('room_name', room.name)
            room.description = request.POST.get('description', room.description)
            room.max_participants = request.POST.get('max_participants', room.max_participants)
            room.save()
            messages.success(request, 'تم تحديث إعدادات الغرفة')
            
        elif action == 'add_participant':
            email = request.POST.get('email')
            try:
                user = CustomUser.objects.get(email=email)
                room.participants.add(user)
                messages.success(request, f'تم إضافة {email} إلى الغرفة')
                
                # إنشاء رسالة نظام
                Message.objects.create(
                    room=room,
                    sender=request.user,
                    content=f'انضم {user.email} إلى الغرفة',
                    message_type='system'
                )
                
            except CustomUser.DoesNotExist:
                messages.error(request, 'المستخدم غير موجود')
                
        elif action == 'remove_participant':
            user_id = request.POST.get('user_id')
            try:
                user = CustomUser.objects.get(id=user_id)
                room.participants.remove(user)
                room.admins.remove(user)
                messages.success(request, f'تم إزالة {user.email} من الغرفة')
            except CustomUser.DoesNotExist:
                messages.error(request, 'المستخدم غير موجود')
    
    participants = room.participants.all()
    return render(request, 'chat/manage_room.html', {
        'room': room,
        'participants': participants
    })

@login_required
def get_messages(request, room_id):
    """جلب الرسائل الجديدة - متوافق مع UUID والأسماء"""
    try:
        # محاولة البحث بـ UUID أولاً
        try:
            room_uuid = uuid.UUID(room_id)
            room = get_object_or_404(ChatRoom, id=room_uuid)
        except ValueError:
            # إذا لم يكن UUID، البحث بالاسم
            room = get_object_or_404(ChatRoom, name=room_id)
        
        if not room.can_join(request.user):
            return JsonResponse([], safe=False)
        
        last_id = request.GET.get('last_id')
        
        query = Message.objects.filter(room=room).exclude(deleted_for=request.user)
        
        if last_id:
            try:
                # محاولة استخدام last_id كـ UUID
                last_uuid = uuid.UUID(last_id)
                last_message = Message.objects.get(id=last_uuid)
                query = query.filter(timestamp__gt=last_message.timestamp)
            except (ValueError, Message.DoesNotExist):
                # إذا فشل، استخدام last_id كـ ID رقمي (للتتوافق)
                try:
                    last_id_int = int(last_id)
                    last_message = Message.objects.get(id=last_id_int)
                    query = query.filter(timestamp__gt=last_message.timestamp)
                except (ValueError, Message.DoesNotExist):
                    pass
        
        messages_list = query.order_by('timestamp')[:50]
        
        messages_data = []
        for msg in messages_list:
            # الحصول على الاسم المعروض بشكل آمن
            sender_display = msg.sender.email  # القيمة الافتراضية
            try:
                if hasattr(msg.sender, 'chat_profile') and msg.sender.chat_profile.display_name:
                    sender_display = msg.sender.chat_profile.display_name
            except Exception:
                pass  # استخدام القيمة الافتراضية في حالة الخطأ
            
            message_data = {
                'id': str(msg.id),
                'sender': msg.sender.email,
                'sender_display': sender_display,
                'message': msg.content,
                'message_type': msg.message_type,
                'timestamp': msg.timestamp.strftime("%H:%M"),
                'is_edited': msg.is_edited,
            }
            
            if msg.image:
                message_data['image_url'] = msg.image.url
            if msg.file:
                message_data['file_url'] = msg.file.url
                message_data['file_name'] = msg.file_name
            if msg.reply_to:
                message_data['reply_to'] = {
                    'id': str(msg.reply_to.id),
                    'sender': msg.reply_to.sender.email,
                    'message': msg.reply_to.content[:50]
                }
            
            messages_data.append(message_data)
        
        return JsonResponse(messages_data, safe=False)
        
    except Exception as e:
        print(f"Error in get_messages: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
def send_message(request, room_id):
    """إرسال رسالة جديدة - متوافق مع UUID والأسماء"""
    if request.method == 'POST':
        try:
            # محاولة البحث بـ UUID أولاً
            try:
                room_uuid = uuid.UUID(room_id)
                room = get_object_or_404(ChatRoom, id=room_uuid)
            except ValueError:
                # إذا لم يكن UUID، البحث بالاسم
                room = get_object_or_404(ChatRoom, name=room_id)
            
            if not room.can_join(request.user):
                return JsonResponse({'status': 'error', 'error': 'غير مصرح بالدخول'})
            
            data = json.loads(request.body)
            message_content = data.get('message', '').strip()
            reply_to_id = data.get('reply_to')
            
            if message_content:
                reply_to = None
                if reply_to_id:
                    try:
                        reply_to = Message.objects.get(id=reply_to_id, room=room)
                    except Message.DoesNotExist:
                        pass
                
                message = Message.objects.create(
                    room=room,
                    sender=request.user,
                    content=message_content,
                    reply_to=reply_to
                )
                
                # الحصول على الاسم المعروض بشكل آمن
                sender_display = request.user.email  # القيمة الافتراضية
                try:
                    if hasattr(request.user, 'chat_profile') and request.user.chat_profile.display_name:
                        sender_display = request.user.chat_profile.display_name
                except Exception:
                    pass  # استخدام القيمة الافتراضية في حالة الخطأ
                
                return JsonResponse({
                    'status': 'success', 
                    'message_id': str(message.id),
                    'sender': request.user.email,
                    'sender_display': sender_display,
                    'timestamp': message.timestamp.strftime("%H:%M"),
                    'reply_to': {
                        'id': str(reply_to.id),
                        'sender': reply_to.sender.email,
                        'message': reply_to.content[:50]
                    } if reply_to else None
                })
            else:
                return JsonResponse({'status': 'error', 'error': 'الرسالة فارغة'})
                
        except Exception as e:
            print(f"Error in send_message: {e}")
            return JsonResponse({'status': 'error', 'error': str(e)})
    
    return JsonResponse({'status': 'error', 'error': 'Method not allowed'})

@csrf_exempt
@login_required
def send_image(request, room_id):
    """إرسال صورة - متوافق مع UUID والأسماء"""
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            # محاولة البحث بـ UUID أولاً
            try:
                room_uuid = uuid.UUID(room_id)
                room = get_object_or_404(ChatRoom, id=room_uuid)
            except ValueError:
                # إذا لم يكن UUID، البحث بالاسم
                room = get_object_or_404(ChatRoom, name=room_id)
            
            image_file = request.FILES['image']
            
            # حفظ الرسالة مع الصورة
            message = Message.objects.create(
                room=room,
                sender=request.user,
                content='📷 صورة مرفوعة',
                image=image_file,
                message_type='image'
            )
            
            return JsonResponse({
                'status': 'success', 
                'message_id': str(message.id),
                'sender': request.user.email,
                'image_url': message.image.url,
                'timestamp': message.timestamp.strftime("%H:%M")
            })
                
        except Exception as e:
            print(f"Error in send_image: {e}")
            return JsonResponse({'status': 'error', 'error': str(e)})
    
    return JsonResponse({'status': 'error', 'error': 'لم يتم اختيار صورة'})

@login_required
def search_rooms(request):
    """بحث الغرف"""
    query = request.GET.get('q', '')
    
    if query:
        rooms = ChatRoom.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query),
            is_active=True
        ).filter(
            Q(room_type='public') | 
            Q(participants=request.user) |
            Q(created_by=request.user)
        ).distinct()
    else:
        rooms = ChatRoom.objects.none()
    
    rooms_data = []
    for room in rooms:
        rooms_data.append({
            'id': str(room.id),
            'name': room.name,
            'description': room.description,
            'room_type': room.get_room_type_display(),
            'online_count': room.get_online_count(),
            'created_by': room.created_by.email
        })
    
    return JsonResponse(rooms_data, safe=False)

@login_required
def user_profile(request):
    """صفحة الملف الشخصي للمستخدم"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        profile.display_name = request.POST.get('display_name', '')
        profile.status = request.POST.get('status', 'online')
        profile.theme = request.POST.get('theme', 'light')
        
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        
        profile.save()
        messages.success(request, 'تم تحديث الملف الشخصي')
        return redirect('chat:user_profile')
    
    return render(request, 'chat/user_profile.html', {'profile': profile})

def chat_home_old(request):
    """للتتوافق مع الروابط القديمة - إعادة توجيه للصفحة الرئيسية"""
    return redirect('chat:home')

@login_required
def create_test_rooms(request):
    """إنشاء غرف اختبارية (للتطوير فقط)"""
    try:
        # غرفة عامة
        public_room, created = ChatRoom.objects.get_or_create(
            name='الغرفة العامة',
            room_type='public',
            defaults={
                'created_by': request.user,
                'description': 'هذه هي الغرفة العامة للجميع'
            }
        )
        
        # غرفة خاصة للمستخدم
        private_room, created = ChatRoom.objects.get_or_create(
            name='غرفتي الخاصة',
            room_type='private',
            created_by=request.user,
            defaults={
                'description': 'هذه غرفتي الخاصة'
            }
        )
        private_room.participants.add(request.user)
        private_room.admins.add(request.user)
        
        messages.success(request, 'تم إنشاء غرف الاختبار بنجاح')
        return redirect('chat:home')
        
    except Exception as e:
        messages.error(request, f'خطأ في إنشاء غرف الاختبار: {e}')
        return redirect('chat:home')
    

@login_required
def invite_user(request, room_id):
    """دعوة مستخدم إلى غرفة خاصة"""
    try:
        room = get_object_or_404(ChatRoom, id=room_id)
        
        # التحقق من الصلاحيات
        if not (room.created_by == request.user or room.admins.filter(id=request.user.id).exists()):
            messages.error(request, 'ليس لديك صلاحية لدعوة مستخدمين إلى هذه الغرفة')
            return redirect('chat:manage_room', room_id=room_id)
        
        if request.method == 'POST':
            email = request.POST.get('email', '').strip().lower()
            
            if not email:
                messages.error(request, 'يرجى إدخال بريد إلكتروني')
                return redirect('chat:manage_room', room_id=room_id)
            
            try:
                invited_user = CustomUser.objects.get(email=email)
                
                # التحقق من عدم دعوة المستخدم لنفسه
                if invited_user == request.user:
                    messages.warning(request, 'لا يمكنك دعوة نفسك')
                    return redirect('chat:manage_room', room_id=room_id)
                
                # التحقق من عدم وجود دعوة سابقة
                existing_invitation = RoomInvitation.objects.filter(
                    room=room,
                    invited_user=invited_user,
                    is_accepted=False,
                    is_declined=False,
                    expires_at__gt=timezone.now()
                ).exists()
                
                if existing_invitation:
                    messages.warning(request, 'تم إرسال دعوة سابقة لهذا المستخدم ولا تزال فعالة')
                    return redirect('chat:manage_room', room_id=room_id)
                
                # التحقق من أن المستخدم ليس عضو بالفعل
                if room.participants.filter(id=invited_user.id).exists():
                    messages.warning(request, 'المستخدم عضو بالفعل في الغرفة')
                    return redirect('chat:manage_room', room_id=room_id)
                
                # إنشاء الدعوة
                invitation = RoomInvitation.objects.create(
                    room=room,
                    invited_by=request.user,
                    invited_user=invited_user,
                    expires_at=timezone.now() + timezone.timedelta(days=7)
                )
                
                # إرسال بريد إلكتروني
                try:
                    send_invitation_email(invitation, request)
                    messages.success(request, f'تم إرسال دعوة إلى {email} بنجاح')
                except Exception as e:
                    # الدعوة تم إنشاؤها ولكن فشل إرسال البريد
                    messages.warning(request, f'تم إنشاء الدعوة ولكن فشل إرسال البريد: {str(e)}')
                
            except CustomUser.DoesNotExist:
                messages.error(request, f'المستخدم بالبريد {email} غير موجود في النظام')
            except Exception as e:
                messages.error(request, f'حدث خطأ غير متوقع: {str(e)}')
        
        return redirect('chat:manage_room', room_id=room_id)
        
    except Exception as e:
        print(f"Error in invite_user: {e}")
        messages.error(request, f'حدث خطأ في إنشاء الدعوة: {str(e)}')
        return redirect('chat:manage_room', room_id=room_id)


def send_invitation_email(invitation, request):
    """إرسال بريد دعوة"""
    try:
        current_site = get_current_site(request)
        subject = f'دعوة للانضمام إلى غرفة الدردشة: {invitation.room.name}'
        
        # تحميل القالب وإرسال البريد
        message = render_to_string('chat/invitation_email.html', {
            'invitation': invitation,
            'domain': current_site.domain,
            'protocol': 'https' if request.is_secure() else 'http'
        })
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email='ADALChat <adnanalrashed7@gmail.com>',  # تحديث هذا
            to=[invitation.invited_user.email]
        )
        email.content_subtype = "html"
        
        # إرسال البريد
        email.send()
        print(f"✅ تم إرسال بريد الدعوة إلى: {invitation.invited_user.email}")
        return True
        
    except Exception as e:
        print(f"❌ فشل إرسال بريد الدعوة: {str(e)}")
        # طباعة تفاصيل الخطأ للمساعدة في التصحيح
        import traceback
        print(f"❌ تفاصيل الخطأ: {traceback.format_exc()}")
        return False


@login_required
def accept_invitation(request, token):
    """قبول دعوة الانضمام إلى غرفة"""
    try:
        invitation = get_object_or_404(RoomInvitation, token=token, invited_user=request.user)
        
        if invitation.is_expired():
            messages.error(request, 'انتهت صلاحية الدعوة')
            return redirect('chat:home')
        
        if invitation.is_accepted:
            messages.info(request, 'لقد قبلت هذه الدعوة مسبقاً')
            return redirect('chat:room_detail', room_id=invitation.room.id)
        
        if invitation.is_declined:
            messages.error(request, 'لقد رفضت هذه الدعوة مسبقاً')
            return redirect('chat:home')
        
        # إضافة المستخدم إلى الغرفة
        invitation.room.participants.add(request.user)
        invitation.is_accepted = True
        invitation.save()
        
        # إنشاء رسالة نظام
        Message.objects.create(
            room=invitation.room,
            sender=request.user,
            content=f'انضم {request.user.email} إلى الغرفة',
            message_type='system'
        )
        
        messages.success(request, f'تم الانضمام إلى غرفة {invitation.room.name}')
        return redirect('chat:room_detail', room_id=invitation.room.id)
        
    except Exception as e:
        messages.error(request, 'رابط الدعوة غير صالح')
        return redirect('chat:home')

@login_required
def decline_invitation(request, token):
    """رفض دعوة الانضمام إلى غرفة"""
    try:
        invitation = get_object_or_404(RoomInvitation, token=token, invited_user=request.user)
        
        if not invitation.is_accepted and not invitation.is_declined:
            invitation.is_declined = True
            invitation.save()
            messages.info(request, 'تم رفض الدعوة')
        
        return redirect('chat:home')
        
    except Exception as e:
        messages.error(request, 'رابط الدعوة غير صالح')
        return redirect('chat:home')

@login_required
def my_invitations(request):
    """عرض الدعوات الواردة للمستخدم"""
    invitations = RoomInvitation.objects.filter(
        invited_user=request.user,
        is_accepted=False,
        is_declined=False
    ).filter(expires_at__gt=timezone.now()).select_related('room', 'invited_by')
    
    return render(request, 'chat/my_invitations.html', {
        'invitations': invitations
    })

@login_required
def check_invitation(request, token):
    """صفحة للتحقق من صحة الدعوة"""
    try:
        invitation = get_object_or_404(RoomInvitation, token=token)
        
        context = {
            'invitation': invitation,
            'is_valid': not invitation.is_expired() and not invitation.is_accepted and not invitation.is_declined,
            'is_expired': invitation.is_expired(),
            'is_accepted': invitation.is_accepted,
            'is_declined': invitation.is_declined,
        }
        
        return render(request, 'chat/check_invitation.html', context)
        
    except Exception as e:
        messages.error(request, 'رابط الدعوة غير صالح')
        return redirect('chat:home')

def debug_invitation_system():
    """دالة لتصحيح نظام الدعوات"""
    from chat.models import RoomInvitation, ChatRoom
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    print("\n=== DEBUG INVITATION SYSTEM ===")
    
    # عرض جميع الدعوات
    invitations = RoomInvitation.objects.all()
    print(f"Total invitations: {invitations.count()}")
    
    for inv in invitations:
        status = "Pending"
        if inv.is_accepted:
            status = "Accepted"
        elif inv.is_declined:
            status = "Declined"
        elif inv.is_expired():
            status = "Expired"
        
        print(f"- {inv.invited_user.email} -> {inv.room.name} [{status}]")
    
    print("=== END DEBUG ===\n")

    # يمكن إضافة هذا الكود في ملف utilities.py أو في نهاية views.py
from django.contrib.auth import get_user_model
from chat.models import ChatRoom, RoomInvitation
from django.utils import timezone

def create_room_invitation(room, invited_email, invited_by):
    """
    دالة مساعدة لإنشاء دعوة يدوياً
    """
    User = get_user_model()
    
    try:
        # البحث عن المستخدم المدعو
        invited_user = User.objects.get(email=invited_email)
        
        # التحقق من عدم وجود دعوة سابقة
        existing_invitation = RoomInvitation.objects.filter(
            room=room,
            invited_user=invited_user,
            is_accepted=False,
            is_declined=False
        ).first()
        
        if existing_invitation:
            return {
                'success': False,
                'message': 'تم إرسال دعوة سابقة لهذا المستخدم',
                'invitation': existing_invitation
            }
        
        # التحقق من أن المستخدم ليس عضو بالفعل
        if room.participants.filter(id=invited_user.id).exists():
            return {
                'success': False,
                'message': 'المستخدم عضو بالفعل في الغرفة'
            }
        
        # إنشاء الدعوة
        invitation = RoomInvitation.objects.create(
            room=room,
            invited_by=invited_by,
            invited_user=invited_user,
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        
        return {
            'success': True,
            'message': 'تم إنشاء الدعوة بنجاح',
            'invitation': invitation
        }
        
    except User.DoesNotExist:
        return {
            'success': False,
            'message': 'المستخدم غير موجود'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }

# مثال للاستخدام:
# result = create_room_invitation(room, 'user@example.com', request.user)
# if result['success']:
#     send_invitation_email(result['invitation'], request)