import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        image_url = text_data_json.get('image_url', None)

        # حفظ الرسالة في قاعدة البيانات
        await self.save_message(message, image_url)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'image_url': image_url,
                'sender': self.scope['user'].email
            }
        )

    async def chat_message(self, event):
        message = event['message']
        image_url = event.get('image_url', None)
        sender = event['sender']

        await self.send(text_data=json.dumps({
            'message': message,
            'image_url': image_url,
            'sender': sender
        }))

    @database_sync_to_async
    def save_message(self, message, image_url):
        from .models import Message, ChatRoom
        room = ChatRoom.objects.get(name=self.room_name)
        Message.objects.create(
            room=room,
            sender=self.scope['user'],
            content=message,
            image=image_url
        )