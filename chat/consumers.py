import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, OnlineUser, CustomUser
import uuid

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope["user"]

        # التحقق من صحة المستخدم والغرفة
        if self.user.is_anonymous:
            await self.close()
            return

        room = await self.get_room()
        if not room or not await self.can_join_room():
            await self.close()
            return

        # الانضمام إلى مجموعة الغرفة
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # تسجيل المستخدم كمتصّل
        await self.add_online_user()

        await self.accept()

        # إرسال إشعار انضمام
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user': self.user.email,
                'display_name': await self.get_display_name()
            }
        )

    async def disconnect(self, close_code):
        # إزالة المستخدم من المتصلين
        await self.remove_online_user()

        # إرسال إشعار مغادرة
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user': self.user.email
            }
        )

        # مغادرة مجموعة الغرفة
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_message(text_data_json)
            elif message_type == 'typing':
                await self.handle_typing(text_data_json)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(text_data_json)
                
        except Exception as e:
            print(f"Error receiving message: {e}")

    async def handle_message(self, data):
        message = data.get('message', '').strip()
        reply_to = data.get('reply_to')
        
        if message:
            # حفظ الرسالة في قاعدة البيانات
            message_obj = await self.save_message(message, reply_to)
            
            # إرسال الرسالة إلى مجموعة الغرفة
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'message_id': str(message_obj.id),
                    'sender': self.user.email,
                    'display_name': await self.get_display_name(),
                    'timestamp': message_obj.timestamp.isoformat(),
                    'reply_to': reply_to
                }
            )

    async def handle_typing(self, data):
        # إرسال إشعار الكتابة
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_typing',
                'user': self.user.email,
                'display_name': await self.get_display_name(),
                'is_typing': data.get('is_typing', False)
            }
        )

    async def chat_message(self, event):
        # إرسال الرسالة إلى WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'message_id': event['message_id'],
            'sender': event['sender'],
            'display_name': event['display_name'],
            'timestamp': event['timestamp'],
            'reply_to': event.get('reply_to')
        }))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user': event['user'],
            'display_name': event['display_name'],
            'online_count': await self.get_online_count()
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user': event['user'],
            'online_count': await self.get_online_count()
        }))

    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_typing',
            'user': event['user'],
            'display_name': event['display_name'],
            'is_typing': event['is_typing']
        }))

    @database_sync_to_async
    def get_room(self):
        try:
            return ChatRoom.objects.get(id=self.room_id)
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def can_join_room(self):
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return room.can_join(self.user)
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def add_online_user(self):
        OnlineUser.objects.get_or_create(
            user=self.user,
            room_id=self.room_id,
            defaults={'channel_name': self.channel_name}
        )

    @database_sync_to_async
    def remove_online_user(self):
        OnlineUser.objects.filter(
            user=self.user,
            room_id=self.room_id
        ).delete()

    @database_sync_to_async
    def get_online_count(self):
        return OnlineUser.objects.filter(room_id=self.room_id).count()

    @database_sync_to_async
    def get_display_name(self):
        profile = getattr(self.user, 'chat_profile', None)
        return profile.display_name if profile and profile.display_name else self.user.email

    @database_sync_to_async
    def save_message(self, content, reply_to=None):
        from .models import Message
        from django.utils import timezone
        
        room = ChatRoom.objects.get(id=self.room_id)
        
        message = Message.objects.create(
            room=room,
            sender=self.user,
            content=content,
            timestamp=timezone.now()
        )
        
        if reply_to:
            try:
                reply_to_msg = Message.objects.get(id=reply_to)
                message.reply_to = reply_to_msg
                message.save()
            except Message.DoesNotExist:
                pass
        
        return message