import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Call
from django.utils import timezone

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("✅ Call WebSocket connected")

    async def disconnect(self, close_code):
        print("❌ Call WebSocket disconnected")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            caller_email = text_data_json.get('caller')
            receiver_email = text_data_json.get('receiver')
            call_type = text_data_json.get('call_type', 'audio')
            
            print(f"📞 Received call message: {message_type}")
            
            if message_type == 'start_call':
                # إنشاء سجل المكالمة في قاعدة البيانات
                call = await self.create_call_record(caller_email, receiver_email, call_type)
                
                await self.send(text_data=json.dumps({
                    'type': 'call_started',
                    'message': 'تم بدء المكالمة',
                    'call_id': call.id
                }))
                
            elif message_type == 'end_call':
                await self.end_call_record(caller_email, receiver_email)
                
                await self.send(text_data=json.dumps({
                    'type': 'call_ended',
                    'message': 'تم إنهاء المكالمة'
                }))
                
            elif message_type == 'test':
                await self.send(text_data=json.dumps({
                    'type': 'test_response',
                    'message': 'Call WebSocket is working!'
                }))
                
        except Exception as e:
            print(f"Error in call WebSocket: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'خطأ: {str(e)}'
            }))

    @database_sync_to_async
    def create_call_record(self, caller_email, receiver_email, call_type):
        from accounts.models import CustomUser
        
        caller = CustomUser.objects.get(email=caller_email)
        receiver = CustomUser.objects.get(email=receiver_email)
        
        call = Call.objects.create(
            caller=caller,
            receiver=receiver,
            call_type=call_type,
            status='ongoing'
        )
        return call

    @database_sync_to_async
    def end_call_record(self, caller_email, receiver_email):
        from accounts.models import CustomUser
        
        caller = CustomUser.objects.get(email=caller_email)
        receiver = CustomUser.objects.get(email=receiver_email)
        
        try:
            call = Call.objects.filter(
                caller=caller,
                receiver=receiver,
                status='ongoing'
            ).latest('timestamp')
            
            call.status = 'completed'
            call.ended_at = timezone.now()
            call.is_active = False
            call.save()
            
        except Call.DoesNotExist:
            print("No ongoing call found to end")